import os
import glob
import numpy as np
import librosa
import soundfile as sf
import random
import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate benign noise samples.")
    parser.add_argument("--mode", choices=["fixed_10s", "trimmed"], default="trimmed",
                        help="Generation mode: 'fixed_10s' (full 10s noise with command at start) or 'trimmed' (audio length equals command length).")
    parser.add_argument("--snr", type=float, default=None, help="Signal-to-Noise Ratio in dB. If set, scales noise to achieve target SNR relative to the command.")
    args = parser.parse_args()

    print(f"Starting Benign Noise Generation in mode: [{args.mode}]")
    if args.snr is not None:
        print(f"Applying Fixed SNR: {args.snr} dB")
    else:
        print("Applying Random SNR: [5.0, 20.0] dB")

    # Configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    benign_source_dir = os.path.join(script_dir, "../benchmark_dataset_v5/benchmark_dataset_mixed", "benign")
    noise_source_dir = os.path.join(script_dir, "../noise")
    output_root_dir = os.path.join(script_dir, "../benign_noise")
    
    target_sr = 16000
    
    # Scenarios to process (excluding OOFFICE_16k)
    # The noise files are named like 'loudest_10s_NPARK_16k.wav'
    scenarios = [
        "NPARK_16k",
        "OMEETING_16k",
        "PCAFETER_16k",
        "PSTATION_16k",
        "STRAFFIC_16k",
        "TBUS_16k"
    ]
    
    # Ensure output root exists
    os.makedirs(output_root_dir, exist_ok=True)
    
    # Get list of benign files
    benign_files = glob.glob(os.path.join(benign_source_dir, "*.wav"))
    if not benign_files:
        print(f"Error: No benign files found in {benign_source_dir}")
        return
        
    print(f"Found {len(benign_files)} benign command files.")
    
    # Process each scenario
    for scene in scenarios:
        print(f"\n--- Processing Scenario: {scene} ---")
        
        noise_file = os.path.join(noise_source_dir, f"loudest_10s_{scene}.wav")
        if not os.path.exists(noise_file):
            print(f"Warning: Noise file not found: {noise_file}")
            continue
            
        # Create output directory for this scenario
        scene_output_dir = os.path.join(output_root_dir, scene)
        os.makedirs(scene_output_dir, exist_ok=True)
        
        # Load Noise (10s)
        try:
            noise_y_orig, _ = librosa.load(noise_file, sr=target_sr)
        except Exception as e:
            print(f"Error loading noise file {noise_file}: {e}")
            continue
            
        # Process each benign file
        for b_file in benign_files:
            filename = os.path.basename(b_file)
            output_path = os.path.join(scene_output_dir, filename)
            
            try:
                # Load command
                cmd_y, _ = librosa.load(b_file, sr=target_sr)
                
                # Prepare Noise Segment
                if args.mode == "fixed_10s":
                    noise_segment = noise_y_orig.copy()
                else: # trimmed
                    cmd_len = len(cmd_y)
                    if len(noise_y_orig) >= cmd_len:
                        noise_segment = noise_y_orig[:cmd_len]
                    else:
                        tile_count = int(np.ceil(cmd_len / len(noise_y_orig)))
                        noise_segment = np.tile(noise_y_orig, tile_count)[:cmd_len]
                
                # --- SNR Adjustment ---
                # Select SNR: Fixed or Random [5, 20]
                current_snr = args.snr if args.snr is not None else random.uniform(5.0, 20.0)

                # Calculate power
                p_signal = np.mean(cmd_y ** 2)
                p_noise = np.mean(noise_segment ** 2)
                
                if p_noise > 0:
                    # Target noise power = Signal / 10^(SNR/10)
                    target_p_noise = p_signal / (10 ** (current_snr / 10))
                    scale = np.sqrt(target_p_noise / p_noise)
                    noise_segment = noise_segment * scale

                # --- Mixing ---
                if args.mode == "fixed_10s":
                    final_audio = noise_segment # Segment is already full length 10s copy
                    insert_len = min(len(cmd_y), len(final_audio))
                    final_audio[:insert_len] += cmd_y[:insert_len]
                    
                else: # trimmed
                    final_audio = cmd_y + noise_segment

                # Normalize (Peak Normalization to avoid clipping)
                max_val = np.max(np.abs(final_audio))
                if max_val > 0:
                    final_audio = final_audio / max_val
                
                # Write to file
                sf.write(output_path, final_audio, target_sr)
                
            except Exception as e:
                print(f"Failed to process {filename}: {e}")
        
        print(f"Completed {scene}. Saved to {scene_output_dir}")

if __name__ == "__main__":
    main()
