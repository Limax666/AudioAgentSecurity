import os
import sys
import json
import json_repair
import glob
import logging
from tqdm import tqdm
from dotenv import load_dotenv

# Setup Paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from src.model import Model
from config import ATTACK_SYSTEM_PROMPT, DOLPHIN_ATTACK_DIR
from src.inference import load_audio, _run_audio_inference

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def generate_benign_baselines(model_name="qwen2.5-omni-7b"):
    load_dotenv()
    
    benign_dir = os.path.join(DOLPHIN_ATTACK_DIR, "benign")
    output_file = os.path.join(DOLPHIN_ATTACK_DIR, f"benign_baselines_{model_name}.json")
    
    if not os.path.exists(benign_dir):
        logger.error(f"Benign directory not found: {benign_dir}")
        return

    logger.info(f"Loading model: {model_name}")
    try:
        model = Model(model_name)
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        return

    wav_files = glob.glob(os.path.join(benign_dir, "*.wav"))
    logger.info(f"Found {len(wav_files)} benign audio files.")

    results = {}
    
    # Check for existing results to resume
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            logger.info(f"Resuming from {len(results)} existing baselines.")
        except:
            pass

    for wav_path in tqdm(wav_files, desc="Generating Baselines"):
        filename = os.path.basename(wav_path)
        if filename in results:
            continue
            
        audio_data, audio_sr = load_audio(wav_path)
        if audio_data is None:
            logger.error(f"Failed to load {wav_path}")
            continue

        # Retry logic
        max_retries = 5
        final_result = None
        
        for attempt in range(max_retries):
            response = _run_audio_inference(
                model,
                audio_data,
                audio_sr,
                ATTACK_SYSTEM_PROMPT,
                context=f"Benign {filename} (Attempt {attempt + 1})"
            )
            
            parsed_json = None
            is_valid = False
            
            # Try parsing
            try:
                # 1. Standard JSON load
                parsed_json = json.loads(response)
            except (json.JSONDecodeError, TypeError):
                try:
                    # 2. JSON Repair
                    decoded = json_repair.repair_json(response, return_objects=True)
                    if isinstance(decoded, list):
                        # Filter for likely valid objects
                        candidates = [
                            d for d in decoded 
                            if isinstance(d, dict) and ('tool_calls' in d or 'response' in d)
                        ]
                        if candidates:
                            parsed_json = candidates[-1]
                        elif decoded:
                            parsed_json = decoded[-1]
                    elif isinstance(decoded, dict):
                        parsed_json = decoded
                except Exception:
                    pass
            
            # Validate structure
            if isinstance(parsed_json, dict):
                # Basic check: should have at least one meaningful key from the system prompt schema
                if 'thought' in parsed_json or 'tool_calls' in parsed_json or 'response' in parsed_json:
                    is_valid = True
            
            if is_valid:
                final_result = parsed_json
                break
            else:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to produce valid JSON for {filename}. Output snippet: {str(response)[:100]}...")
                final_result = response # Keep last response even if invalid
        
        results[filename] = final_result
        
        # Save incrementally
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

    logger.info(f"Finished. Saved {len(results)} baselines to {output_file}")

if __name__ == "__main__":
    import fire
    fire.Fire(generate_benign_baselines)
