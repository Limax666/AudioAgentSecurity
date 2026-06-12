import pandas as pd
import numpy as np
import os

def calculate_threshold():
    # Determine script directory to ensure paths are relative to this file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "results", "benign_noise_evaluation_details.csv")
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Run evaluate_benign_noise.py first.")
        return

    df = pd.read_csv(csv_path)
    scores = df['score_anchor_sim'].dropna().values
    
    # 5% FPR means 5% of benign samples are below the threshold
    # So we want the 5th percentile
    threshold_5pct = np.percentile(scores, 10)
    
    print(f"Total samples: {len(scores)}")
    print(f"Mean score: {np.mean(scores):.4f}")
    print(f"Min score: {np.min(scores):.4f}")
    print(f"Max score: {np.max(scores):.4f}")
    print(f"Suggested Threshold for 5% FPR: {threshold_5pct:.4f}")

if __name__ == "__main__":
    calculate_threshold()
