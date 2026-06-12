import os
import glob
import pandas as pd
from tqdm import tqdm
import sys
import concurrent.futures
from pathlib import Path
import logging
import torch
from typing import List, Dict, Optional, Any

# Add project root to sys.path
current_file = Path(__file__).resolve()
project_root = current_file.parents[1] # Go up 2 levels: defense -> ProjectRoot
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    # Try importing as a package module (e.g. from main_attack.py context)
    from defense.defense_module import AudioAgentSecurityDefense
except ImportError:
    try:
        # Try local import (if script runs directly in folder)
        sys.path.append(str(current_file.parent))
        from defense_module import AudioAgentSecurityDefense
    except ImportError as e:
        logger.critical(f"Could not import defense_module: {e}")
        raise

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ATTACK_METHODS = [
    'dolphin', 'high_freq', 'pulse', 'spectral_inversion', 'spectral_scramble',
    'texture', 'whisper', 'dialect', 'foreign', 'speed'
]

def extract_attack_info(file_path: str, base_dir: str) -> tuple[str, str]:
    """Extract attack_type and attack_method from file path for V5 mixed dataset."""
    try:
        rel_path = os.path.relpath(file_path, base_dir)
    except ValueError:
        rel_path = file_path
        
    parts = rel_path.replace("\\", "/").split("/")
    
    # New V5 Structure: 
    # benign/file.wav -> type="benign", method="none"
    # mixed/method/file.wav -> type="mixed", method="method"
    
    attack_type = "unknown"
    attack_method = "none"
    
    if "benign" in parts:
        attack_type = "benign"
    elif "mixed" in parts:
        attack_type = "mixed"
        # Find which part is the method (the one after "mixed")
        try:
            idx = parts.index("mixed")
            if idx + 1 < len(parts):
                method_part = parts[idx+1]
                if method_part in ATTACK_METHODS:
                    attack_method = method_part
        except ValueError:
            pass
            
    return attack_type, attack_method

def collect_files(folder_path: Path, label_is_attack: bool, attack_type_override: Optional[str] = None) -> List[Dict]:
    """Recursively find all audio files in a folder."""
    tasks = []
    folder_path = Path(folder_path)
    if not folder_path.exists():
        logger.warning(f"Folder not found: {folder_path}")
        return []

    files = list(folder_path.rglob("*.wav")) + list(folder_path.rglob("*.mp3"))
        
    logger.info(f"Scanning {folder_path}: Found {len(files)} files. Expected Attack: {label_is_attack}")
    
    for audio_file in files:
        tasks.append({
            "path": str(audio_file),
            "label_is_attack": label_is_attack,
            "attack_type_override": attack_type_override
        })
    return tasks

def process_single_file(detector: AudioAgentSecurityDefense, task: Dict, base_dir: str) -> Optional[Dict]:
    """Helper function to process a single file."""
    audio_file = task["path"]
    label_is_attack = task["label_is_attack"]
    attack_type_override = task["attack_type_override"]
    
    try:
        res = detector.detect_risk(audio_file)
        
        attack_type, attack_method = extract_attack_info(audio_file, base_dir)
        
        # Override for legacy benign noise folders which aren't in the main dataset structure
        if attack_type_override:
            attack_type = attack_type_override
            attack_method = "none"
        
        entry = {
            "file": os.path.basename(audio_file),
            "path": audio_file,
            "attack_type": attack_type,
            "attack_method": attack_method,
            "label": "Attack" if label_is_attack else "Benign",
            "ground_truth_is_attack": label_is_attack,
            "predicted_is_risk": res["risk"],
            "score_min_sim": res.get("min_sim", 1.0),
            "score_variance": res.get("variance", 0.0),
            "score_anchor_sim": res.get("anchor_min_sim", 1.0),
            "snr": res.get("snr_db", 0.0),
            "threshold_used": res.get("threshold_used", 0.45),
            "reasons": res.get("reasons", "")
        }
        return entry
    except Exception as e:
        logger.error(f"Failed to process {audio_file}: {e}")
        return None

def process_tasks(detector: AudioAgentSecurityDefense, tasks: List[Dict], base_dir: str) -> List[Dict]:
    """Process a list of tasks with a parallel ThreadPoolExecutor."""
    results = []
    max_workers = 4 
    
    logger.info(f"Processing tasks with {max_workers} threads...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(process_single_file, detector, task, base_dir): task 
            for task in tasks
        }
        
        for future in tqdm(concurrent.futures.as_completed(future_to_task), total=len(tasks), desc="Evaluating", unit="file"):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                task = future_to_task[future]
                logger.error(f"Unhandled exception for {task['path']}: {e}")
            
    return results

def print_breakdown_stats(df: pd.DataFrame):
    """Print detection rates grouped by attack_type and attack_method."""
    print("\n" + "="*60)
    print("       BREAKDOWN BY ATTACK TYPE & METHOD")
    print("="*60)
    
    # Group by attack_type first
    for attack_type in sorted(df['attack_type'].unique()):
        df_type = df[df['attack_type'] == attack_type]
        
        if attack_type == 'benign' or attack_type == 'benign_noise':
            # For benign, calculate FPR
            fp = len(df_type[df_type['predicted_is_risk'] == True])
            total = len(df_type)
            fpr = fp / total if total > 0 else 0
            print(f"\n[{str(attack_type).upper()}] (Total: {total})")
            print(f"  False Positive Rate: {fpr:.2%} ({fp}/{total})")
            continue
            
        print(f"\n[{str(attack_type).upper()}]")
        
        # Group by attack_method within this type
        for attack_method in sorted(df_type['attack_method'].unique()):
            df_method = df_type[df_type['attack_method'] == attack_method]
            tp = len(df_method[(df_method['ground_truth_is_attack'] == True) & (df_method['predicted_is_risk'] == True)])
            fn = len(df_method[(df_method['ground_truth_is_attack'] == True) & (df_method['predicted_is_risk'] == False)])
            total = tp + fn
            tpr = tp / total if total > 0 else 0
            print(f"  {str(attack_method):20s}: TPR={tpr:.2%}  ({tp}/{total})")
        
        # Summary for this type
        tp_type = len(df_type[(df_type['ground_truth_is_attack'] == True) & (df_type['predicted_is_risk'] == True)])
        fn_type = len(df_type[(df_type['ground_truth_is_attack'] == True) & (df_type['predicted_is_risk'] == False)])
        total_type = tp_type + fn_type
        tpr_type = tp_type / total_type if total_type > 0 else 0
        print(f"  {'[TOTAL]':20s}: TPR={tpr_type:.2%}  ({tp_type}/{total_type})")

def main():
    script_dir = Path(__file__).parent.resolve()
    # Updated to V5 Mixed Dataset
    base_dir = project_root / "benchmark_dataset_v5" / "benchmark_dataset_mixed"
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Check imports
    try:
        detector = AudioAgentSecurityDefense(device=device)
    except Exception as e:
        logger.critical(f"Failed to initialize Defense Module: {e}")
        return

    all_tasks = []
    
    # 0. Benign Environmental Noise (External folder for FPR calculation)
    path_benign_noise = project_root / "benign_noise"
    if path_benign_noise.exists():
        tasks = collect_files(path_benign_noise, label_is_attack=False, attack_type_override="benign_noise")
        all_tasks.extend(tasks)
    else:
        logger.warning(f"Benign noise dataset not found at {path_benign_noise}.")

    # 1. Mixed Attacks (For TPR calculation)
    path_mixed = base_dir / "mixed"
    if path_mixed.exists():
        tasks = collect_files(path_mixed, label_is_attack=True)
        all_tasks.extend(tasks)

    if not all_tasks:
        logger.warning("No files found to evaluate.")
        return

    logger.info(f"Starting evaluation on {len(all_tasks)} total files...")
    all_results = process_tasks(detector, all_tasks, str(base_dir))

    if not all_results:
        logger.error("No results generated.")
        return

    df = pd.DataFrame(all_results)
    
    # --- Print Console Report (Restored) ---
    tp = len(df[(df['ground_truth_is_attack'] == True) & (df['predicted_is_risk'] == True)])
    fn = len(df[(df['ground_truth_is_attack'] == True) & (df['predicted_is_risk'] == False)])
    tn = len(df[(df['ground_truth_is_attack'] == False) & (df['predicted_is_risk'] == False)])
    fp = len(df[(df['ground_truth_is_attack'] == False) & (df['predicted_is_risk'] == True)])
    
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    accuracy = (tp + tn) / len(df) if len(df) > 0 else 0
    
    print("\n" + "="*60)
    print("            OVERALL DEFENSE EVALUATION REPORT")
    print("="*60)
    print(f"Total Samples:   {len(df)}")
    print(f"Accuracy:        {accuracy:.2%}")
    print(f"Recall (TPR):    {tpr:.2%}  (Detection Rate)")
    print(f"False Pos Rate:  {fpr:.2%}  (False Alarms)")
    print("-" * 60)
    print(f"True Positives:  {tp}")
    print(f"False Negatives: {fn}")
    print(f"True Negatives:  {tn}")
    print(f"False Positives: {fp}")
    print("="*60)
    
    print_breakdown_stats(df)
    
    # Save results
    results_dir = script_dir / "results"
    results_dir.mkdir(exist_ok=True)
    
    save_path = results_dir / "defense_results_detailed.csv"
    df.to_csv(save_path, index=False)
    logger.info(f"Detailed results saved to {save_path}.")

    # Generate Summary
    summary_data = []
    for attack_type in df['attack_type'].unique():
        df_type = df[df['attack_type'] == attack_type]
        is_attack_group = 'benign' not in str(attack_type).lower()
        
        # Per Method
        for attack_method in sorted(df_type['attack_method'].unique()):
            df_method = df_type[df_type['attack_method'] == attack_method]
            total = len(df_method)
            detected = len(df_method[df_method['predicted_is_risk'] == True])
            rate = detected / total if total > 0 else 0.0
            
            summary_data.append({
                "attack_type": attack_type,
                "attack_method": attack_method,
                "total_samples": total,
                "detected_samples": detected,
                "rate": round(rate, 4),
                "metric_type": "TPR" if is_attack_group else "FPR"
            })
            
        # Total
        total_type = len(df_type)
        detected_type = len(df_type[df_type['predicted_is_risk'] == True])
        rate_type = detected_type / total_type if total_type > 0 else 0.0
        
        summary_data.append({
            "attack_type": attack_type,
            "attack_method": "ALL",
            "total_samples": total_type,
            "detected_samples": detected_type,
            "rate": round(rate_type, 4),
            "metric_type": "TPR" if is_attack_group else "FPR"
        })

    summary_path = results_dir / "defense_metrics_summary.csv"
    pd.DataFrame(summary_data).to_csv(summary_path, index=False)
    logger.info(f"Summary metrics saved to {summary_path}.")

if __name__ == "__main__":
    main()