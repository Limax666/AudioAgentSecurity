import numpy as np
import scipy.signal as signal

def normalize(audio):
    """Normalize audio to [-1, 1]."""
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        return audio / max_val
    return audio

def modulate_am(baseband_signal, fs, carrier_freq, modulation_depth=0.8):
    """
    Amplitude Modulation (AM-DSB) for High-Frequency Narrowband Attack.
    
    Args:
        baseband_signal (np.array): Input audio.
        fs (int): Sampling rate.
        carrier_freq (float): Carrier frequency (e.g., 16000 Hz).
        modulation_depth (float): Modulation index (0.0 to 1.0).
        
    Returns:
        np.array: Modulated signal.
    """
    t = np.arange(len(baseband_signal)) / fs
    
    # Ensure signal is normalized
    norm_signal = normalize(baseband_signal)
    
    # AM Modulation: s(t) = (1 + m * x(t)) * cos(2 * pi * fc * t)
    modulated_signal = (1 + modulation_depth * norm_signal) * np.cos(2 * np.pi * carrier_freq * t)
    
    return normalize(modulated_signal)

def modulate_ring(audio_signal, fs, carrier_freq, waveform='sine'):
    """
    Ring Modulation (DSB-SC) for Electrical/Robotic Sound.
    
    Args:
        audio_signal (np.array): Input audio.
        fs (int): Sampling rate.
        carrier_freq (float): Carrier frequency (e.g., 50 Hz for mains hum).
        waveform (str): 'sine' or 'square'.
        
    Returns:
        np.array: Modulated signal.
    """
    t = np.arange(len(audio_signal)) / fs
    
    if waveform == 'square':
        carrier = signal.square(2 * np.pi * carrier_freq * t)
    elif waveform == 'sawtooth':
        carrier = signal.sawtooth(2 * np.pi * carrier_freq * t)
    elif waveform == 'noise':
        carrier = np.random.normal(0, 1, len(t))
    else:
        carrier = np.sin(2 * np.pi * carrier_freq * t)
        
    # Ring Modulation: y(t) = x(t) * c(t)
    # This suppresses the carrier and baseband, leaving only sidebands.
    # For 50Hz square wave, it sounds like a harsh electrical buzz.
    output_signal = audio_signal * carrier
    
    return normalize(output_signal)

def apply_tremolo(audio_signal, fs, rate=4.0, depth=0.8, waveform='sine'):
    """
    Apply Tremolo (Low-frequency Amplitude Modulation) for Rhythmic Pulse Attack.
    
    Args:
        audio_signal (np.array): Input audio.
        fs (int): Sampling rate.
        rate (float): LFO frequency in Hz (e.g., 1-4 Hz).
        depth (float): Modulation depth (0.0 to 1.0).
        waveform (str): 'sine' or 'square'.
        
    Returns:
        np.array: Signal with tremolo applied.
    """
    t = np.arange(len(audio_signal)) / fs
    
    if waveform == 'sine':
        lfo = np.sin(2 * np.pi * rate * t)
    elif waveform == 'square':
        lfo = signal.square(2 * np.pi * rate * t)
    else:
        lfo = np.sin(2 * np.pi * rate * t)
        
    # Map LFO from [-1, 1] to [1-depth, 1]
    # gain(t) = 1 - depth/2 * (1 - lfo(t))  -> ranges from 1-depth to 1
    # Or simpler: gain = (1 - depth) + depth * (lfo + 1) / 2
    
    gain = (1 - depth) + depth * (lfo + 1) / 2
    
    output_signal = audio_signal * gain
    return normalize(output_signal)

def add_noise(audio_signal, noise_type='pink', snr_db=10):
    """
    Add Noise Texture.
    
    Args:
        audio_signal (np.array): Input audio.
        noise_type (str): 'white', 'pink', or 'brown'.
        snr_db (float): Signal-to-Noise Ratio in dB.
        
    Returns:
        np.array: Noisy signal.
    """
    # Calculate signal power
    sig_power = np.mean(audio_signal ** 2)
    
    if sig_power == 0:
        return audio_signal
        
    # Calculate required noise power
    noise_power = sig_power / (10 ** (snr_db / 10))
    
    # Generate noise
    if noise_type == 'white':
        noise = np.random.normal(0, np.sqrt(noise_power), len(audio_signal))
    elif noise_type == 'pink':
        # Simple 1/f noise approximation
        uneven = np.random.normal(0, 1, len(audio_signal))
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
        a = [1, -2.494956002, 2.017265875, -0.522189400]
        noise = signal.lfilter(b, a, uneven)
        # Adjust power
        current_power = np.mean(noise ** 2)
        noise = noise * np.sqrt(noise_power / current_power)
    else:
        noise = np.random.normal(0, np.sqrt(noise_power), len(audio_signal))
        
    output_signal = audio_signal + noise
    return normalize(output_signal)

def add_rumble(audio_signal, fs, freq=50, snr_db=5, waveform='sine'):
    """
    Add Low-frequency Rumble (Sub-bass).
    
    Args:
        audio_signal (np.array): Input audio.
        fs (int): Sampling rate.
        freq (float): Rumble frequency (e.g., 30-70 Hz).
        snr_db (float): Signal-to-Rumble Ratio (lower means louder rumble).
        waveform (str): 'sine', 'square', or 'sawtooth'.
        
    Returns:
        np.array: Signal with rumble.
    """
    t = np.arange(len(audio_signal)) / fs
    
    if waveform == 'square':
        rumble = signal.square(2 * np.pi * freq * t)
    elif waveform == 'sawtooth':
        rumble = signal.sawtooth(2 * np.pi * freq * t)
    else:
        rumble = np.sin(2 * np.pi * freq * t)
    
    # Calculate powers
    sig_power = np.mean(audio_signal ** 2)
    rumble_power = np.mean(rumble ** 2)
    
    if sig_power == 0:
        return rumble
        
    # Scale rumble to achieve target SNR
    # SNR = 10 * log10(P_sig / P_rumble_scaled)
    # P_rumble_scaled = P_sig / 10^(SNR/10)
    target_rumble_power = sig_power / (10 ** (snr_db / 10))
    scale_factor = np.sqrt(target_rumble_power / rumble_power)
    
    output_signal = audio_signal + rumble * scale_factor
    return normalize(output_signal)


def spectral_inversion(audio_signal, fs, carrier_freq=3000, blend_ratio=0.7):
    """
    Spectral Inversion Attack - Classic DSB-SC implementation.
    
    Principle: Uses Double Sideband Suppressed Carrier (DSB-SC) modulation to invert the spectrum around the carrier frequency.
    This is a classic voice encryption technique that produces a "Donald Duck" sound effect.
    Low frequencies become high, and high frequencies become low.
    
    Principle: Uses Double Sideband Suppressed Carrier (DSB-SC) modulation
    to invert the spectrum around a carrier frequency. This is the classic
    voice scrambling technique producing a "Donald Duck" effect.
    Args:
        audio_signal (np.array): Input audio signal [-1, 1].
        fs (int): Sampling rate.
        carrier_freq (float): Carrier frequency for inversion (Hz).
            - 2000-2500 Hz: Heavy inversion, very distorted
            - 3000-3500 Hz: Moderate inversion, "Donald Duck" sound
            - 4000+ Hz: Light inversion, still somewhat intelligible
        blend_ratio (float): Blend with original (0.0=original, 1.0=fully inverted).
            
    Returns:
        np.array: Spectrally inverted signal with characteristic "Donald Duck" sound.
    """
    t = np.arange(len(audio_signal)) / fs
    
    # Step 1: DSB-SC Modulation - multiply by carrier
    # This shifts all frequencies: f -> (fc + f) and (fc - f)
    carrier = np.cos(2 * np.pi * carrier_freq * t)
    modulated = audio_signal * carrier
    
    # Step 2: Low-pass filter to extract lower sideband (inverted spectrum)
    # Cutoff should be below carrier frequency
    nyquist = fs / 2
    cutoff = min(carrier_freq * 0.9, nyquist * 0.9)
    
    # Design 6th order Butterworth low-pass filter for clean cutoff
    b, a = signal.butter(6, cutoff / nyquist, btype='low')
    inverted = signal.filtfilt(b, a, modulated)
    
    # Step 3: Normalize and blend with original
    inverted = normalize(inverted)
    output = (1 - blend_ratio) * audio_signal + blend_ratio * inverted
    
    return normalize(output)


def spectral_scramble(audio_signal, fs, num_bands=4, permutation=None, blend_ratio=0.7):
    """
    Frequency Band Permutation Attack.
    
    Balanced version: Frequency band permutation + pitch region phase randomization.
    - Phase randomization in the pitch region (80-500Hz) disrupts pitch perception, making it unintelligible to humans.
    - Phase is preserved in the formant region, allowing AI to still recognize it via MFCC.
    
    Args:
        audio_signal (np.array): Input audio signal [-1, 1].
        fs (int): Sampling rate.
        num_bands (int): Number of frequency bands (2-8 recommended).
        permutation (list): Custom permutation, or None for auto.
        blend_ratio (float): 0.0=original, 1.0=fully scrambled.
            
    Returns:
        np.array: Scrambled signal.
    """
    # ========== STFT Frequency Domain Processing ==========
    # Increase nperseg to 4096 for 192kHz (approx 21ms window) to get enough frequency bins
    nperseg = 4096 
    hop_length = nperseg // 4
    
    f, t_stft, Zxx = signal.stft(audio_signal, fs, nperseg=nperseg, 
                                  noverlap=nperseg - hop_length)
    
    Zxx_scrambled = Zxx.copy()
    
    # ========== Phase 1: Full Voice Frequency Band Phase Randomization (Disrupt Human Intelligibility) ==========
    # Randomize phase for the entire speech frequency range (80-4000Hz)
    speech_low, speech_high = 80, 4000
    low_idx = np.argmin(np.abs(f - speech_low))
    high_idx = np.argmin(np.abs(f - speech_high))
    
    magnitude = np.abs(Zxx_scrambled[low_idx:high_idx, :])
    np.random.seed(42)
    random_phase = np.random.uniform(-np.pi, np.pi, magnitude.shape)
    Zxx_scrambled[low_idx:high_idx, :] = magnitude * np.exp(1j * random_phase)
    
    # ========== Phase 2: Formant Region Band Permutation (Optional, Increase Confusion) ==========
    speech_low, speech_high = 500, 3500
    low_idx = np.argmin(np.abs(f - speech_low))
    high_idx = np.argmin(np.abs(f - speech_high))
    speech_range = high_idx - low_idx
    
    # Ensure num_bands doesn't exceed available bins
    actual_num_bands = min(num_bands, speech_range)
    if actual_num_bands < 1: actual_num_bands = 1
    
    band_size = speech_range // actual_num_bands
    
    # Generate derangement
    if permutation is None:
        np.random.seed(42)
        permutation = list(range(actual_num_bands))
        for _ in range(100):
            np.random.shuffle(permutation)
            if all(permutation[i] != i for i in range(actual_num_bands)):
                break
        else:
            permutation = [(i + actual_num_bands // 2) % actual_num_bands for i in range(actual_num_bands)]
    
    # Apply band permutation
    Zxx_temp = Zxx_scrambled.copy()
    for dst_band, src_band in enumerate(permutation):
        src_start = low_idx + src_band * band_size
        src_end = min(low_idx + (src_band + 1) * band_size, high_idx)
        dst_start = low_idx + dst_band * band_size
        dst_end = min(low_idx + (dst_band + 1) * band_size, high_idx)
        
        # Safety check for shape mismatch
        h_src = src_end - src_start
        h_dst = dst_end - dst_start
        
        if h_src > 0 and h_dst > 0:
            # If slight mismatch due to rounding, take min height
            min_h = min(h_src, h_dst)
            band_data = Zxx_scrambled[src_start:src_start+min_h, :].copy()
            Zxx_temp[dst_start:dst_start+min_h, :] = band_data
    
    Zxx_scrambled = Zxx_temp
    
    # Blend with original
    Zxx_blended = (1 - blend_ratio) * Zxx + blend_ratio * Zxx_scrambled
    
    # Inverse STFT
    _, output = signal.istft(Zxx_blended, fs, nperseg=nperseg, 
                              noverlap=nperseg - hop_length)
    
    # Match length
    if len(output) > len(audio_signal):
        output = output[:len(audio_signal)]
    elif len(output) < len(audio_signal):
        output = np.pad(output, (0, len(audio_signal) - len(output)))
    
    return normalize(output)


def whisper_attack(audio_signal, fs, whisper_intensity=0.8):
    """
    Whisper/Breathiness Attack.
    
    Principle: Converts speech into a whisper-like form by increasing breathiness and reducing voiced characteristics.
    This makes it difficult for humans to understand at normal volume, but preserves the temporal and spectral envelope features for AI recognition.
    
    Principle: Convert speech to whisper-like form by adding breathiness and
    reducing voiced components. Humans struggle to understand at normal volume,
    but temporal and spectral envelope features are preserved for AI.
    
    Args:
        audio_signal (np.array): Input audio signal [-1, 1].
        fs (int): Sampling rate.
        whisper_intensity (float): How much to "whisperize" (0.0-1.0).
            Higher = more whisper-like, harder for humans.
            
    Returns:
        np.array: Whisperized speech.
        
    Scientific Basis:
        1. Whispering removes pitch (F0) information, which humans heavily rely on.
        2. AI ASR systems often use features that work even without clear pitch.
        3. Spectral envelope (formants) is preserved in whispers, aiding AI.
        4. Adding white noise simulates aspiration noise in whispered speech.
    """
    nperseg = 2048
    hop_length = nperseg // 4
    
    # Compute STFT
    f, t_stft, Zxx = signal.stft(audio_signal, fs, nperseg=nperseg, 
                                  noverlap=nperseg - hop_length)
    
    # Get magnitude and phase
    magnitude = np.abs(Zxx)
    
    # Replace harmonic structure with noise-like phase (whisper characteristic)
    random_phase = np.random.uniform(-np.pi, np.pi, Zxx.shape)
    
    # Blend original phase with random phase based on intensity
    blended_phase = (1 - whisper_intensity) * np.angle(Zxx) + whisper_intensity * random_phase
    
    # Reconstruct with original magnitude but modified phase
    Zxx_whisper = magnitude * np.exp(1j * blended_phase)
    
    # Inverse STFT
    _, whispered = signal.istft(Zxx_whisper, fs, nperseg=nperseg, 
                                 noverlap=nperseg - hop_length)
    
    # Ensure length matches
    if len(whispered) > len(audio_signal):
        whispered = whispered[:len(audio_signal)]
    elif len(whispered) < len(audio_signal):
        whispered = np.pad(whispered, (0, len(audio_signal) - len(whispered)))
    
    # Add subtle aspiration noise
    # Reduced from 0.1 to 0.01 to improve intelligibility for ASR
    aspiration = np.random.normal(0, 0.01 * whisper_intensity, len(whispered))
    # High-pass filter aspiration to simulate breath noise
    b, a = signal.butter(2, 1000 / (fs/2), btype='high')
    aspiration = signal.filtfilt(b, a, aspiration)
    
    output = whispered + aspiration
    
    return normalize(output)


def apply_drc(audio, fs, threshold_db=-20.0, ratio=4.0, attack_ms=5.0, release_ms=50.0, makeup_gain_db=0.0):
    """
    Apply Dynamic Range Compression (DRC).
    
    Args:
        audio (np.array): Input audio signal.
        fs (int): Sampling rate.
        threshold_db (float): Threshold in dB.
        ratio (float): Compression ratio (e.g., 4.0 for 4:1).
        attack_ms (float): Attack time in milliseconds.
        release_ms (float): Release time in milliseconds.
        makeup_gain_db (float): Makeup gain in dB.
        
    Returns:
        np.array: Compressed audio signal.
    """
    eps = 1e-10
    audio_abs = np.abs(audio)
    audio_db = 20 * np.log10(audio_abs + eps)
    
    alpha_attack = np.exp(-1.0 / (fs * attack_ms / 1000.0))
    alpha_release = np.exp(-1.0 / (fs * release_ms / 1000.0))
    
    detected_level = np.zeros_like(audio_db)
    current_level = -100.0
    
    for i in range(len(audio_db)):
        if audio_db[i] > current_level:
            current_level = alpha_attack * current_level + (1 - alpha_attack) * audio_db[i]
        else:
            current_level = alpha_release * current_level + (1 - alpha_release) * audio_db[i]
        detected_level[i] = current_level
        
    gain_reduction = np.zeros_like(detected_level)
    over_threshold = detected_level > threshold_db
    gain_reduction[over_threshold] = (threshold_db - detected_level[over_threshold]) * (1.0 - 1.0 / ratio)
    
    total_gain_db = gain_reduction + makeup_gain_db
    total_gain_linear = 10 ** (total_gain_db / 20.0)
    
    compressed_audio = audio * total_gain_linear
    
    return normalize(compressed_audio)
