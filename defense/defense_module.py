import os
import sys
import numpy as np
import torch
import librosa
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from modelscope.hub.snapshot_download import snapshot_download
import onnxruntime as ort
from scipy.spatial.distance import pdist, squareform
import scipy.signal
import logging
import soundfile as sf
import re
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress noisy loggers from third-party libraries
logging.getLogger('modelscope').setLevel(logging.ERROR)
logging.getLogger('funasr').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)


@dataclass
class DefenseConfig:
    """Configuration for Audio Defense Module."""
    # Models
    MODEL_CAMPLUS: str = 'iic/speech_campplus_sv_zh_en_16k-common_advanced'
    MODEL_FSMN_VAD: str = 'iic/speech_fsmn_vad_zh-cn-16k-common-pytorch'
    MODEL_MOSSFORMER: str = 'dengcunqin/speech_mossformer2_separation_temporal_16k'
    MODEL_SENSEVOICE: str = 'iic/SenseVoiceSmall'

    # Audio Processing
    SAMPLE_RATE: int = 16000
    WINDOW_SIZE: float = 1.0
    STEP_SIZE: float = 0.5
    
    # Feature Weights
    WEIGHT_EMBED: float = 0.7
    WEIGHT_ACOUSTIC: float = 0.3

    # Thresholds
    BASE_SIMILARITY_THRESHOLD: float = 0.2
    VARIANCE_THRESHOLD: float = 0.08
    
    # Type 3 Defense Thresholds
    MIN_SECONDARY_ENERGY_RATIO: float = 0.08
    LOUD_RATIO_THRESHOLD: float = 0.2
    STRICT_SIM_THRESHOLD: float = 0.5
    LOOSE_SIM_THRESHOLD: float = 0.25
    CORRELATION_THRESHOLD: float = 0.3
    
    # SNR
    SNR_LOW_THRESHOLD: float = 15.0
    SNR_PENALTY: float = 0.05


class AudioAgentSecurityDefense:
    def __init__(self, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        """
        Initialize the Audio Agent Security Defense module.
        """
        self.device = device
        self.config = DefenseConfig()
        logger.info(f"Initializing Defense Module V3 on {self.device}...")
        
        self.sv_pipeline = None
        self.vad_pipeline = None
        self.sep_sess = None
        self.asr_pipeline = None
        
        self._load_models()

    def _load_models(self):
        """Load all necessary models with error handling."""
        # 1. Load CAM++ (Speaker Verification)
        try:
            self.sv_pipeline = pipeline(
                task=Tasks.speaker_verification,
                model=self.config.MODEL_CAMPLUS,
                device=self.device
            )
            logger.info("CAM++ Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load CAM++ model: {e}")
            raise e

        # 2. Load FSMN-VAD
        try:
            self.vad_pipeline = pipeline(
                task=Tasks.voice_activity_detection,
                model=self.config.MODEL_FSMN_VAD,
                device=self.device
            )
            logger.info("FSMN-VAD Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load VAD model: {e}")
            raise e

        # 3. Load Mossformer2 Separation Model (ONNX)
        try:
            logger.info("Loading Mossformer2 Separation Model...")
            sep_model_dir = snapshot_download(self.config.MODEL_MOSSFORMER)
            onnx_files = [f for f in os.listdir(sep_model_dir) if f.endswith('.onnx')]
            
            if not onnx_files:
                logger.warning("No .onnx file found for separation model. Feature disabled.")
            else:
                onnx_path = os.path.join(sep_model_dir, onnx_files[0])
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if self.device == 'cuda' else ['CPUExecutionProvider']
                self.sep_sess = ort.InferenceSession(onnx_path, providers=providers)
                logger.info(f"Mossformer2 loaded successfully from {onnx_path}")
        except Exception as e:
            logger.error(f"Failed to load Separation model: {e}")

        # 4. Load SenseVoiceSmall (ASR)
        try:
            self.asr_pipeline = pipeline(
                task=Tasks.auto_speech_recognition,
                model=self.config.MODEL_SENSEVOICE,
                device=self.device
            )
            logger.info("SenseVoiceSmall Model loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to load ASR model (Semantic Check disabled): {e}")

    def load_audio(self, audio_path: str) -> Optional[np.ndarray]:
        """Load audio and resample to target sample rate."""
        try:
            # Try soundfile first
            data, samplerate = sf.read(audio_path)
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
                
            if samplerate != self.config.SAMPLE_RATE:
                num_samples = int(len(data) * self.config.SAMPLE_RATE / samplerate)
                data = scipy.signal.resample(data, num_samples)
                
            return data.astype(np.float32)
        except Exception as e:
            logger.debug(f"Soundfile load failed for {audio_path}, trying librosa. Error: {e}")
            try:
                waveform, sr = librosa.load(audio_path, sr=self.config.SAMPLE_RATE)
                return waveform.astype(np.float32)
            except Exception as e2:
                logger.error(f"Error loading audio {audio_path}: {e2}")
                return None

    def estimate_snr(self, audio_data: np.ndarray) -> float:
        """Estimate Signal-to-Noise Ratio (SNR) in dB."""
        frame_len = 512
        if len(audio_data) < frame_len: 
            return 20.0
        
        # Calculate Short-Term Energy
        # Use strided sliding window for speed
        # Simple approximation: sum of squares in chunks
        num_frames = len(audio_data) // frame_len
        if num_frames == 0:
             return 20.0
             
        reshaped = audio_data[:num_frames*frame_len].reshape(num_frames, frame_len)
        energies = np.sum(reshaped**2, axis=1)
        
        energies = np.maximum(energies, 1e-10)
        
        signal_energy = np.percentile(energies, 95)
        noise_energy = np.percentile(energies, 10)
        
        if noise_energy <= 0: 
            return 30.0
        
        snr = 10 * np.log10(signal_energy / noise_energy)
        return snr

    def apply_vad(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply FSMN-VAD to extract speech segments."""
        if len(audio_data) == 0: 
            return audio_data
        
        try:
            res = self.vad_pipeline(audio_data, disable_pbar=True, verbose=False)
            
            segments_ms = []
            if isinstance(res, list) and len(res) > 0 and isinstance(res[0], dict) and 'value' in res[0]:
                segments_ms = res[0]['value']
            elif 'value' in res: 
                segments_ms = res['value']
            elif isinstance(res, list): 
                segments_ms = res
            
            if not segments_ms: 
                return np.array([], dtype=np.float32)
                
            speech_clips = []
            for start_ms, end_ms in segments_ms:
                start_idx = int(start_ms * self.config.SAMPLE_RATE / 1000)
                end_idx = int(end_ms * self.config.SAMPLE_RATE / 1000)
                start_idx = max(0, start_idx)
                end_idx = min(len(audio_data), end_idx)
                if end_idx > start_idx:
                    speech_clips.append(audio_data[start_idx:end_idx])
            
            if not speech_clips: 
                return np.array([], dtype=np.float32)
            return np.concatenate(speech_clips)
            
        except Exception as e:
            logger.warning(f"VAD failed: {e}")
            return audio_data

    def check_semantic_content(self, audio_data: np.ndarray) -> Tuple[bool, str]:
        """Use ASR to check if audio contains meaningful text."""
        if self.asr_pipeline is None: 
            return True, ""
            
        try:
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            res = self.asr_pipeline(audio_data, disable_pbar=True, verbose=False)
            
            text = ""
            if isinstance(res, dict):
                text = res.get('text', '') or res.get('text_postprocessed', '')
            elif isinstance(res, list) and len(res) > 0:
                if isinstance(res[0], dict):
                    text = res[0].get('text', '') or res[0].get('text_postprocessed', '')
            
            clean_text = re.sub(r'<\|.*?\|>', '', text).strip()
            
            # 1. Length Check
            if len(clean_text) < 2: 
                return False, clean_text
                
            # 2. Noise Marker Check
            noise_markers = {
                "?", "。", "nan", "uh", "um", "ah", "hmm", "laugh", "noise", "unk",
                ".", ",", "!", "what", "oh", "hey", "嗯", "啊", "哦", "唉", "呃"
            }
            if clean_text.lower() in noise_markers:
                return False, clean_text
                
            return True, clean_text
            
        except Exception as e:
            logger.warning(f"ASR semantic check failed: {e}")
            return True, "" 

    def segment_audio(self, audio_data: np.ndarray) -> Tuple[List[np.ndarray], List[Tuple[float, float]]]:
        """Sliding window segmentation."""
        window_samples = int(self.config.WINDOW_SIZE * self.config.SAMPLE_RATE)
        step_samples = int(self.config.STEP_SIZE * self.config.SAMPLE_RATE)
        segments = []
        timestamps = []
        length = len(audio_data)
        
        if length < window_samples:
            if length > int(0.2 * self.config.SAMPLE_RATE): 
                segments.append(audio_data)
                timestamps.append((0, length/self.config.SAMPLE_RATE))
            return segments, timestamps
            
        for start in range(0, length - window_samples + 1, step_samples):
            end = start + window_samples
            segments.append(audio_data[start:end])
            timestamps.append((start/self.config.SAMPLE_RATE, end/self.config.SAMPLE_RATE))
        return segments, timestamps

    def extract_features_batch(self, segments: List[np.ndarray]) -> List[Dict[str, Any]]:
        """Extract features using batch inference where possible."""
        if not segments:
            return []

        features_list = [{} for _ in range(len(segments))]
        
        # 1. Identity Embedding (CAM++)
        try:
            batch_input = [seg.astype(np.float32) for seg in segments]
            res = self.sv_pipeline(batch_input, output_emb=True)
            
            embeddings = []
            if isinstance(res, dict):
                if 'embs' in res:
                    embeddings = res['embs']
                elif 'spk_embedding' in res:
                    embeddings = res['spk_embedding']
            elif isinstance(res, list):
                for item in res:
                    if isinstance(item, dict):
                        if 'embs' in item: embeddings.append(item['embs'])
                        elif 'spk_embedding' in item: embeddings.append(item['spk_embedding'])
            
            for i, emb in enumerate(embeddings):
                if i < len(features_list):
                    features_list[i]['embedding'] = emb

        except Exception as e:
            logger.error(f"Batch embedding extraction failed: {e}")
            return []
            
        # 2. Acoustic Features (Librosa)
        for i, audio_segment in enumerate(segments):
            try:
                # Basic features
                mfcc_mean = np.mean(librosa.feature.mfcc(y=audio_segment, sr=self.config.SAMPLE_RATE, n_mfcc=13), axis=1)
                zcr_mean = np.mean(librosa.feature.zero_crossing_rate(y=audio_segment))
                cent_mean = np.mean(librosa.feature.spectral_centroid(y=audio_segment, sr=self.config.SAMPLE_RATE))
                rolloff_mean = np.mean(librosa.feature.spectral_rolloff(y=audio_segment, sr=self.config.SAMPLE_RATE))
                
                feat_vec = np.concatenate([
                    mfcc_mean, 
                    [zcr_mean * 100], 
                    [np.log1p(cent_mean)], 
                    [np.log1p(rolloff_mean)]
                ])
                features_list[i]['acoustic'] = feat_vec
            except Exception as e:
                # Only log distinct errors to avoid flooding
                pass
            
        valid_features = [f for f in features_list if 'embedding' in f and 'acoustic' in f]
        return valid_features

    def compute_similarity_matrix(self, feature_list: List[Dict]) -> np.ndarray:
        """Compute Combined N×N Similarity Matrix."""
        if len(feature_list) < 2:
            return np.array([[1.0]])

        # 1. Embeddings Similarity
        embeddings = np.array([f['embedding'] for f in feature_list])
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-10)
        sim_embed = np.dot(embeddings, embeddings.T) 

        # 2. Acoustic Similarity
        acoustics = np.array([f['acoustic'] for f in feature_list])
        mean = np.mean(acoustics, axis=0)
        std = np.std(acoustics, axis=0) + 1e-6
        acoustics_norm = (acoustics - mean) / std
        
        dists = pdist(acoustics_norm, metric='euclidean')
        dist_matrix = squareform(dists)
        sim_acoustic = 1.0 / (1.0 + dist_matrix)
        
        # Normalize embed sim to [0,1] range roughly
        sim_embed_norm = 0.5 * (sim_embed + 1.0) 
        
        combined_matrix = self.config.WEIGHT_EMBED * sim_embed_norm + self.config.WEIGHT_ACOUSTIC * sim_acoustic
        return combined_matrix

    def _get_single_embedding(self, audio_data: np.ndarray) -> Optional[np.ndarray]:
        """Helper to extract a single embedding."""
        try:
            if len(audio_data) < 200: 
                return None
            
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # CAM++ expects list for batch, here batch of 2 to avoid edge cases
            res = self.sv_pipeline([audio_data, audio_data], output_emb=True)
            
            if 'embs' in res and len(res['embs']) > 0:
                return res['embs'][0]
            elif 'spk_embedding' in res:
                return res['spk_embedding']
        except Exception:
            return None
        return None

    def separate_audio_tracks(self, audio_data: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Separate audio using Mossformer2."""
        if self.sep_sess is None: 
            return None, None
        
        try:
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            input_tensor = audio_data[np.newaxis, :]
            input_name = self.sep_sess.get_inputs()[0].name
            
            outputs = self.sep_sess.run(None, {input_name: input_tensor})
            est_source = outputs[0] # Shape: (1, T, 2)
            
            track1 = est_source[0, :, 0]
            track2 = est_source[0, :, 1]
            
            return track1, track2
        except Exception as e:
            logger.error(f"Separation inference failed: {e}")
            return None, None

    def _analyze_type3_risk(self, raw_audio: np.ndarray) -> Tuple[bool, Dict[str, Any]]:
        """Specific logic for detecting Type 3 (Superimposed) attacks."""
        if not self.sep_sess:
            return False, {}

        # Limit input length for separation speed
        max_len = 30 * self.config.SAMPLE_RATE
        sep_input = raw_audio[:max_len] if len(raw_audio) > max_len else raw_audio

        t1, t2 = self.separate_audio_tracks(sep_input)
        if t1 is None or t2 is None:
            return False, {}

        # Energy Analysis
        rms1 = np.sqrt(np.mean(t1**2))
        rms2 = np.sqrt(np.mean(t2**2))
        
        # Identify Dominant vs Secondary
        if rms1 > rms2:
            p1, p2, e1, e2 = t1, t2, rms1, rms2
        else:
            p1, p2, e1, e2 = t2, t1, rms2, rms1
        
        # Filter weak secondary tracks
        if e2 < 0.001 or e2 <= self.config.MIN_SECONDARY_ENERGY_RATIO * e1:
            return False, {}

        # VAD
        vad1 = self.apply_vad(p1)
        vad2 = self.apply_vad(p2)
        
        valid1 = len(vad1) > 0.5 * self.config.SAMPLE_RATE
        valid2 = len(vad2) > 0.5 * self.config.SAMPLE_RATE

        if not (valid1 and valid2):
            return False, {"vad1": vad1 if valid1 else None} # Return valid vad1 to reuse

        # Similarity Check
        emb1 = self._get_single_embedding(vad1)
        emb2 = self._get_single_embedding(vad2)
        
        if emb1 is None or emb2 is None:
            return False, {"vad1": vad1}

        n1 = np.linalg.norm(emb1)
        n2 = np.linalg.norm(emb2)
        sim = np.dot(emb1, emb2) / ((n1 * n2) + 1e-10)
        
        ratio = e2 / e1
        dynamic_thresh = self.config.STRICT_SIM_THRESHOLD if ratio > self.config.LOUD_RATIO_THRESHOLD else self.config.LOOSE_SIM_THRESHOLD
        
        if sim < dynamic_thresh:
            # Cross-Correlation Check (Anti-Reverb/Echo)
            # Normalize
            norm_p1 = (p1 - np.mean(p1)) / (np.std(p1) + 1e-10)
            norm_p2 = (p2 - np.mean(p2)) / (np.std(p2) + 1e-10)
            
            # Truncate for speed
            limit = 16000 * 3
            if len(norm_p1) > limit:
                center = np.argmax(np.abs(p1))
                start = max(0, center - limit // 2)
                end = min(len(norm_p1), center + limit // 2)
                segment_p1 = norm_p1[start:end]
                segment_p2 = norm_p2[start:end]
            else:
                segment_p1 = norm_p1
                segment_p2 = norm_p2

            correlation = scipy.signal.correlate(segment_p1, segment_p2, mode='same', method='fft')
            max_corr = np.max(np.abs(correlation)) / len(segment_p1)
            
            if max_corr <= self.config.CORRELATION_THRESHOLD:
                # Semantic Check
                has_semantics, clean_text = self.check_semantic_content(vad2)
                
                if has_semantics:
                    return True, {
                        "ratio": ratio,
                        "sim": sim,
                        "corr": max_corr,
                        "text": clean_text,
                        "threshold": dynamic_thresh,
                        "vad1": vad1
                    }

        return False, {"vad1": vad1}

    def detect_risk(self, audio_path: str) -> Dict[str, Any]:
        """Main Pipeline Entry Point."""
        raw_audio = self.load_audio(audio_path)
        if raw_audio is None: 
            return {"risk": False, "reason": "Load Error"}
        
        # 1. Type 3 Specific Check
        # Returns is_risk (bool) and info (dict)
        # Info might contain 'vad1' to save re-computation
        type3_risk, info = self._analyze_type3_risk(raw_audio)
        
        if type3_risk:
            return {
                "risk": True,
                "snr_db": float(self.estimate_snr(raw_audio)),
                "threshold_used": info.get("threshold", 0.0),
                "min_sim": float(info.get("sim", 0.0)),
                "variance": 0.0,
                "anchor_min_sim": 0.0,
                "reasons": f"Type 3 Attack: Dual Speakers (Ratio {info['ratio']:.2f}, Sim {info['sim']:.2f}, Text='{info['text']}')"
            }

        # 2. General Consistency Check
        # Reuse VAD audio if computed during Type 3 check
        speech_audio = info.get("vad1")
        if speech_audio is None:
             speech_audio = self.apply_vad(raw_audio)
             
        snr = self.estimate_snr(raw_audio)
        current_threshold = self.config.BASE_SIMILARITY_THRESHOLD
        
        if snr < self.config.SNR_LOW_THRESHOLD:
            current_threshold -= self.config.SNR_PENALTY

        if len(speech_audio) < self.config.SAMPLE_RATE * 0.5:
             return {"risk": False, "reason": "Too Short"}

        segments, _ = self.segment_audio(speech_audio)
        if len(segments) < 2:
            return {"risk": False, "reason": "Single Segment"}

        feature_list = self.extract_features_batch(segments)
        
        if len(feature_list) < 2:
            return {"risk": False, "reason": "Insufficient Features"}

        # Anchor Logic
        anchor_embedding = feature_list[0]['embedding']
        anchor_embedding = anchor_embedding / (np.linalg.norm(anchor_embedding) + 1e-10)
        
        anchor_sims = []
        for i, feat in enumerate(feature_list):
            emb = feat['embedding']
            emb_norm = emb / (np.linalg.norm(emb)+1e-10)
            sim = np.dot(anchor_embedding, emb_norm)
            anchor_sims.append(sim)
            
        min_anchor_sim = np.min(anchor_sims)
        
        # Matrix Logic
        sim_matrix = self.compute_similarity_matrix(feature_list)
        min_matrix_sim = np.min(sim_matrix)
        variance_matrix = np.var(sim_matrix)
        
        is_risk = False
        reasons = []
        
        if min_matrix_sim < current_threshold:
            is_risk = True
            reasons.append(f"Matrix MinSim {min_matrix_sim:.3f} < {current_threshold:.2f}")
            
        if variance_matrix > self.config.VARIANCE_THRESHOLD:
            is_risk = True
            reasons.append(f"Matrix Var {variance_matrix:.3f} > {self.config.VARIANCE_THRESHOLD}")
            
        if min_anchor_sim < current_threshold:
             is_risk = True
             reasons.append(f"Anchor MinSim {min_anchor_sim:.3f} < {current_threshold:.2f}")

        return {
            "risk": is_risk,
            "snr_db": float(snr),
            "threshold_used": float(current_threshold),
            "min_sim": float(min_matrix_sim),
            "variance": float(variance_matrix),
            "anchor_min_sim": float(min_anchor_sim),
            "reasons": "; ".join(reasons)
        }
