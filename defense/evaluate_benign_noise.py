import os
import glob
import pandas as pd
from tqdm import tqdm
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

try:
    from defense.defense_module import AudioAgentSecurityDefense
except ImportError:
    # Fallback for local execution
    sys.path.append(os.path.dirname(__file__))
    from defense_module import AudioAgentSecurityDefense
import logging
import torch

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def evaluate_noise_scenario(detector, folder_path, scenario_name):
    """
    Evaluate all wav files in a specific noise scenario folder.
    Returns a list of results and a summary dictionary.
    """
    # Recursively find wav files
    files = glob.glob(os.path.join(folder_path, "**/*.wav"), recursive=True)
    if not files:
        files = glob.glob(os.path.join(folder_path, "**/*.mp3"), recursive=True)
    
    total_files = len(files)
    logger.info(f"Scanning Scenario [{scenario_name}]: Found {total_files} files.")
    
    results = []
    false_positives = 0
    
    for audio_file in tqdm(files, desc=f"Evaluating {scenario_name}"):
        try:
            # Run defense detection
            res = detector.detect_risk(audio_file)
            
            is_risk = res["risk"]
            if is_risk:
                false_positives += 1
            
            # Record detailed entry matching evaluate_defense.py structure
            # Added 'scenario' column as requested
            entry = {
                "file": os.path.basename(audio_file),
                "path": audio_file,
                "scenario": scenario_name,      # Kept as requested
                "attack_type": "benign_noise",  # Consistent with "benign" logic
                "attack_method": "none",        # Consistent with benign logic
                "label": "Benign",
                "ground_truth_is_attack": False, # Always False for Benign
                "predicted_is_risk": is_risk,
                "score_min_sim": res.get("min_sim", 1.0),
                "score_variance": res.get("variance", 0.0),
                "score_anchor_sim": res.get("anchor_min_sim", 1.0),
                "snr": res.get("snr_db", 0.0),
                "threshold_used": res.get("threshold_used", 0.45)
            }
            results.append(entry)
            
        except Exception as e:
            logger.error(f"Failed to process {audio_file}: {e}")
            
    # Calculate FPR for this scenario
    fpr = false_positives / total_files if total_files > 0 else 0.0
    
    summary = {
        "Scenario": scenario_name,
        "Total Samples": total_files,
        "False Positives": false_positives,
        "FPR": fpr
    }
    
    return results, summary

def main():
    # Use relative path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Target directory: benign_noise (up 1 level)
    base_noise_dir = os.path.join(script_dir, "../benign_noise")
    
    if not os.path.exists(base_noise_dir):
        logger.error(f"Directory not found: {base_noise_dir}")
        return

    # Initialize Defense (Loads Model)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Initializing Defense Model on {device}...")
    detector = AudioAgentSecurityDefense(device=device)
    
    all_detailed_results = []
    scenario_summaries = []
    
    # Get all subdirectories (scenarios) in benign_noise
    # e.g., NPARK_16k, OMEETING_16k...
    scenarios = [d for d in os.listdir(base_noise_dir) if os.path.isdir(os.path.join(base_noise_dir, d))]
    
    if not scenarios:
        logger.warning(f"No subdirectories found in {base_noise_dir}.")
        return
        
    logger.info(f"Found {len(scenarios)} noise scenarios: {scenarios}")

    # Iterate through each scenario
    for scenario in sorted(scenarios):
        scenario_path = os.path.join(base_noise_dir, scenario)
        results, summary = evaluate_noise_scenario(detector, scenario_path, scenario)
        
        all_detailed_results.extend(results)
        scenario_summaries.append(summary)

    # --- Generate Report ---
    
    # Create Summary DataFrame
    df_summary = pd.DataFrame(scenario_summaries)
    
    print("\n" + "="*80)
    print("          BENIGN NOISE ROBUSTNESS EVALUATION (FALSE POSITIVE RATES)")
    print("="*80)
    # Format FPR as percentage for display
    print(df_summary.to_string(index=False, formatters={'FPR': '{:.2%}'.format}))
    print("-" * 80)
    
    # Calculate Average FPR across all scenarios
    total_fp = df_summary['False Positives'].sum()
    total_samples = df_summary['Total Samples'].sum()
    avg_fpr = total_fp / total_samples if total_samples > 0 else 0
    
    print(f"OVERALL STATISTICS:")
    print(f"  Total Files Processed: {total_samples}")
    print(f"  Total False Positives: {total_fp}")
    print(f"  Average FPR:           {avg_fpr:.2%}")
    print("="*80)
    
    # Save Detailed Results
    df_detailed = pd.DataFrame(all_detailed_results)
    save_path_detailed = os.path.join(script_dir, "results", "benign_noise_evaluation_details.csv")
    df_detailed.to_csv(save_path_detailed, index=False)
    
    # Save Summary
    save_path_summary = os.path.join(script_dir, "results", "benign_noise_evaluation_summary.csv")
    df_summary.to_csv(save_path_summary, index=False)
    
    logger.info(f"Detailed results saved to {save_path_detailed}")
    logger.info(f"Summary report saved to {save_path_summary}")

if __name__ == "__main__":
    main()
