import numpy as np
import scipy.signal as signal

def modulate(baseband_signal, fs_base, carrier_freq, fs_high=192000, modulation_depth=0.8):
    """
    Modulate baseband signal onto an ultrasonic carrier using AM-DSB.
    
    Args:
        baseband_signal (np.array): Input audio signal (normalized).
        fs_base (int): Sampling rate of input signal.
        carrier_freq (float): Carrier frequency in Hz (e.g., 25000).
        fs_high (int): Target sampling rate for simulation (default 192kHz).
        modulation_depth (float): Modulation index (0.0 to 1.0).
        
    Returns:
        np.array: Modulated ultrasonic signal at fs_high.
    """
    # 1. Upsample to high sampling rate
    num_samples = int(len(baseband_signal) * fs_high / fs_base)
    upsampled_signal = signal.resample(baseband_signal, num_samples)
    
    # 2. Generate time vector
    t = np.arange(len(upsampled_signal)) / fs_high
    
    # 3. Apply AM-DSB Modulation
    # s(t) = (1 + m * x(t)) * cos(2 * pi * fc * t)
    # Ensure x(t) is within [-1, 1] for correct modulation depth application
    max_val = np.max(np.abs(upsampled_signal))
    if max_val > 0:
        norm_signal = upsampled_signal / max_val
    else:
        norm_signal = upsampled_signal
        
    modulated_signal = (1 + modulation_depth * norm_signal) * np.cos(2 * np.pi * carrier_freq * t)
    
    # Normalize output to avoid clipping in transmission (optional, but good practice)
    if np.max(np.abs(modulated_signal)) > 0:
        modulated_signal = modulated_signal / np.max(np.abs(modulated_signal))
    
    return modulated_signal

def apply_agc(audio_signal, fs, target_level_db=-20, max_gain_db=30, attack_time_ms=20, release_time_ms=500):
    """
    Digital Automatic Gain Control (AGC).
    
    Args:
        audio_signal (np.array): Input audio signal.
        fs (int): Sampling rate.
        target_level_db (float): Target RMS level in dBFS.
        max_gain_db (float): Maximum gain to apply in dB.
        attack_time_ms (float): Attack time in milliseconds.
        release_time_ms (float): Release time in milliseconds.
        
    Returns:
        np.array: Signal with AGC applied.
    """
    target_amp = 10 ** (target_level_db / 20)
    max_gain = 10 ** (max_gain_db / 20)
    
    # Time constants
    dt = 1.0 / fs
    attack_coeff = np.exp(-dt / (attack_time_ms / 1000.0))
    release_coeff = np.exp(-dt / (release_time_ms / 1000.0))
    
    output_signal = np.zeros_like(audio_signal)
    envelope = 0.0
    
    for i, sample in enumerate(audio_signal):
        # Envelope detection (rectified)
        abs_sample = abs(sample)
        if abs_sample > envelope:
            envelope = attack_coeff * envelope + (1 - attack_coeff) * abs_sample
        else:
            envelope = release_coeff * envelope + (1 - release_coeff) * abs_sample
            
        # Avoid division by zero
        if envelope < 1e-9:
            desired_gain = max_gain
        else:
            desired_gain = target_amp / envelope
            
        # Clamp gain
        desired_gain = min(desired_gain, max_gain)
        
        output_signal[i] = sample * desired_gain
        
    # Hard limiter to prevent clipping after AGC
    output_signal = np.clip(output_signal, -1.0, 1.0)
    
    return output_signal

def acoustic_frontend(signal_in, fs, mic_model='MEMS', nonlinearity_cfg=None, agc_enabled=True):
    """
    Simulate the acoustic frontend: Physical Response -> Nonlinearity -> LPF -> Noise -> AGC.
    
    Args:
        signal_in (np.array): Input ultrasonic signal.
        fs (int): Sampling rate (e.g., 192000).
        mic_model (str): Microphone model type ('MEMS' or 'Ideal').
        nonlinearity_cfg (dict): Configuration for nonlinearity (k1, k2, k3...).
                                 Default: {'k1': 1.0, 'k2': 0.01}
        agc_enabled (bool): Whether to enable Automatic Gain Control.
                                 
    Returns:
        np.array: Recovered (demodulated) and processed audio signal.
    """
    if nonlinearity_cfg is None:
        nonlinearity_cfg = {'k1': 1.0, 'k2': 0.01} # Default small nonlinearity
        
    y = signal_in.copy()
    
    # ---------------------------------------------------
    # Stage 1: Physical Response (Resonance/Attenuation)
    # ---------------------------------------------------
    if mic_model == 'MEMS':
        f0 = 25000.0  # Resonance frequency
        Q = 5.0       # Quality factor
        boost_db = 10.0
        
        # Design peaking filter
        b, a = signal.iirpeak(f0, Q, fs)
        
        # Apply resonance
        y_res = signal.lfilter(b, a, y)
        
        # Mix resonance with original signal (simplified model of resonance on top of flat response)
        # Or assume resonance dominates at high freq.
        # Let's add the resonance component scaled by boost
        y = y + y_res * (10**(boost_db/20))
        
    # ---------------------------------------------------
    # Stage 2: Nonlinearity (Demodulation)
    # ---------------------------------------------------
    # V_out = k1*V_in + k2*V_in^2 + k3*V_in^3 ...
    k1 = nonlinearity_cfg.get('k1', 1.0)
    k2 = nonlinearity_cfg.get('k2', 0.0)
    k3 = nonlinearity_cfg.get('k3', 0.0)
    
    y_nonlin = k1 * y + k2 * (y**2) + k3 * (y**3)
    
    # ---------------------------------------------------
    # Stage 3: Analog LPF & Noise
    # ---------------------------------------------------
    # LPF to simulate anti-aliasing filter before ADC
    # Use Chebyshev Type II for steeper roll-off to reject carrier
    cutoff_freq = 15000  # Lower cutoff to 15kHz to reject 25kHz carrier
    nyquist = 0.5 * fs
    normal_cutoff = cutoff_freq / nyquist
    
    # Order 8, 60dB stopband attenuation
    b_lpf, a_lpf = signal.cheby2(8, 60, normal_cutoff, btype='low', analog=False)
    
    y_filtered = signal.lfilter(b_lpf, a_lpf, y_nonlin)
    
    # High Pass Filter to remove DC offset from demodulation (important for AGC)
    # Cutoff at 20Hz (audible range start)
    hpf_cutoff = 20
    normal_hpf_cutoff = hpf_cutoff / nyquist
    b_hpf, a_hpf = signal.butter(4, normal_hpf_cutoff, btype='high', analog=False)
    y_filtered = signal.lfilter(b_hpf, a_hpf, y_filtered)
    
    # Add Noise (Thermal/Quantization)
    # Assume -60dB noise floor
    noise_level = 10**(-60/20)
    noise = np.random.normal(0, noise_level, len(y_filtered))
    y_noisy = y_filtered + noise
    
    # ---------------------------------------------------
    # Stage 4: Automatic Gain Control (AGC)
    # ---------------------------------------------------
    if agc_enabled:
        y_agc = apply_agc(y_noisy, fs)
        return y_agc
    else:
        return y_noisy

def demodulate(modulated_signal, fs_high=192000, fs_base=44100, mic_model='MEMS', nonlinearity_cfg=None):
    """
    Full demodulation pipeline: Acoustic Frontend -> Downsample.
    
    Args:
        modulated_signal (np.array): Ultrasonic signal.
        fs_high (int): Input sampling rate.
        fs_base (int): Target output sampling rate.
        mic_model (str): Microphone model.
        nonlinearity_cfg (dict): Nonlinearity config.
        
    Returns:
        np.array: Recovered audible signal at fs_base.
    """
    # Run acoustic frontend simulation
    recovered_high_fs = acoustic_frontend(modulated_signal, fs_high, mic_model, nonlinearity_cfg)
    
    # Downsample to base audio rate (e.g., 44.1kHz)
    num_samples = int(len(recovered_high_fs) * fs_base / fs_high)
    recovered_signal = signal.resample(recovered_high_fs, num_samples)
    
    return recovered_signal
