import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path

# Configuration matching DefenseConfig in defense_module.py
VARIANCE_THRESHOLD = 0.08
SNR_LOW_THRESHOLD = 15.0
SNR_PENALTY = 0.05

def simulate_detection(row, base_threshold):
    """
    Re-implement the detection logic from defense_module.py loosely
    to allow offline threshold experimentation.
    """
    # 1. If it was detected as Type 3 (Dual Speaker) originally, 
    # and the logic for Type 3 is independent of the main similarity threshold,
    # we should likely keep it as a detection.
    # Looking at defense_module.py, Type 3 detection returns early with specific reasons.
    reasons = str(row.get('reasons', ''))
    if "Type 3 Attack" in reasons:
        return True

    # 2. Dynamic Threshold Adjustment based on SNR
    current_threshold = base_threshold
    snr = row.get('snr', 20.0)
    
    if snr < SNR_LOW_THRESHOLD:
        current_threshold -= SNR_PENALTY
        
    # 3. Check Consistency Scores (Matrix Sim & Anchor Sim)
    # Default to 1.0 (perfect sim) if missing to avoid False Positives on missing data
    min_sim = row.get('score_min_sim', 1.0)
    anchor_sim = row.get('score_anchor_sim', 1.0)
    variance = row.get('score_variance', 0.0)
    
    if min_sim < current_threshold:
        return True
    
    if anchor_sim < current_threshold:
        return True
        
    if variance > VARIANCE_THRESHOLD:
        return True
        
    return False

def run_experiment():
    # Setup Paths
    script_dir = Path(__file__).parent.resolve()
    results_dir = script_dir / "results"
    csv_path = results_dir / "defense_results_detailed.csv"
    
    if not csv_path.exists():
        print(f"Error: Results file not found at {csv_path}")
        print("Please run 'evaluate_defense.py' first to generate the base data.")
        return

    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Filter valid data
    # Ensure we have the necessary columns
    required_cols = ['score_min_sim', 'score_anchor_sim', 'ground_truth_is_attack']
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Missing column '{col}' in CSV.")
            return

    # Define Threshold Range
    thresholds = np.arange(0.10, 0.65, 0.025)
    
    experiment_results = []
    
    print(f"Running simulation for {len(thresholds)} threshold values...")
    
    for thresh in thresholds:
        # Apply simulation
        # vectorization would be faster but apply is clearer for logic reproduction
        pred_risk = df.apply(lambda row: simulate_detection(row, thresh), axis=1)
        
        # Calculate Metrics
        # TPR (Recall): Proportion of Attacks detected
        attacks = df[df['ground_truth_is_attack'] == True]
        tp = np.sum(pred_risk[attacks.index])
        total_attacks = len(attacks)
        tpr = tp / total_attacks if total_attacks > 0 else 0
        
        # FPR: Proportion of Benign detected as Risk
        benign = df[df['ground_truth_is_attack'] == False]
        fp = np.sum(pred_risk[benign.index])
        total_benign = len(benign)
        fpr = fp / total_benign if total_benign > 0 else 0
        
        accuracy = (tp + (total_benign - fp)) / len(df)
        
        experiment_results.append({
            "Threshold": thresh,
            "TPR": tpr,
            "FPR": fpr,
            "Accuracy": accuracy,
            "TP": tp,
            "FP": fp
        })

    # Convert to DataFrame
    res_df = pd.DataFrame(experiment_results)
    
    # Save CSV
    out_csv = results_dir / "threshold_experiment_results.csv"
    res_df.to_csv(out_csv, index=False)
    print(f"Experiment results saved to {out_csv}")
    
    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(res_df['Threshold'], res_df['TPR'], label='TPR (Detection Rate)', marker='o', linewidth=2)
    plt.plot(res_df['Threshold'], res_df['FPR'], label='FPR (False Alarm Rate)', marker='x', linewidth=2, linestyle='--')
    
    # Highlight "Sweet Spot" (e.g., FPR around 5%)
    # Find closest threshold to FPR=0.05
    idx = (np.abs(res_df['FPR'] - 0.05)).argmin()
    sweet_thresh = res_df.iloc[idx]['Threshold']
    sweet_tpr = res_df.iloc[idx]['TPR']
    sweet_fpr = res_df.iloc[idx]['FPR']
    
    plt.axvline(x=sweet_thresh, color='green', linestyle=':', alpha=0.7, label=f'~5% FPR (Thresh={sweet_thresh:.3f})')
    
    # Mark TPR
    plt.scatter([sweet_thresh], [sweet_tpr], color='red', zorder=5)
    plt.text(sweet_thresh, sweet_tpr + 0.03, f"TPR={sweet_tpr:.1%}", ha='center', color='red', fontweight='bold')
    
    # Mark FPR
    plt.scatter([sweet_thresh], [sweet_fpr], color='blue', zorder=5)
    plt.text(sweet_thresh, sweet_fpr + 0.03, f"FPR={sweet_fpr:.1%}", ha='center', color='blue', fontweight='bold')
    
    plt.title("Defense: Impact of Similarity Threshold on Performance")
    plt.xlabel("Similarity Threshold")
    plt.ylabel("Rate")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.ylim(-0.05, 1.05)
    
    plot_path = results_dir / "threshold_impact_curve.png"
    plt.savefig(plot_path, dpi=300)
    print(f"Plot saved to {plot_path}")

if __name__ == "__main__":
    run_experiment()
