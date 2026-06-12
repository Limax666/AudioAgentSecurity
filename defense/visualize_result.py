import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc
import numpy as np
import os

# Set Style for CCS Paper (Academic)
sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")

def plot_distributions(df):
    """Plot distribution of Min Similarity for Benign vs Attack."""
    plt.figure(figsize=(8, 6))
    
    # Min Similarity Distribution
    sns.kdeplot(data=df, x='score_min_sim', hue='label', fill=True, common_norm=False, palette=['#1f77b4', '#d62728'], alpha=0.5)
    plt.axvline(x=0.45, color='black', linestyle='--', label='Threshold (0.45)')
    
    plt.title('Distribution of Minimum Similarity Scores')
    plt.xlabel('Minimum Cosine Similarity')
    plt.ylabel('Density')
    plt.legend(title='Group')
    plt.tight_layout()
    save_path = os.path.join(RESULTS_DIR, 'viz_dist_similarity.png')
    plt.savefig(save_path, dpi=300)
    print(f"Saved {save_path}")

def plot_scatter(df):
    """Scatter plot: Variance vs Min Sim."""
    plt.figure(figsize=(8, 6))
    
    sns.scatterplot(data=df, x='score_min_sim', y='score_variance', hue='label', style='label', s=100, palette=['#1f77b4', '#d62728'], alpha=0.8)
    
    # Draw Decision Boundaries (approx)
    plt.axvline(x=0.45, color='gray', linestyle='--')
    plt.axhline(y=0.08, color='gray', linestyle='--')
    
    plt.title('Decision Boundary Separation')
    plt.xlabel('Minimum Similarity (Consistency)')
    plt.ylabel('Variance (Instability)')
    plt.tight_layout()
    save_path = os.path.join(RESULTS_DIR, 'viz_scatter_boundary.png')
    plt.savefig(save_path, dpi=300)
    print(f"Saved {save_path}")

def plot_roc(df):
    """Plot ROC Curve based on Min Similarity (inverted)."""
    y_true = df['ground_truth_is_attack'].astype(int)
    y_score = 1.0 - df['score_min_sim'] 
    
    fpr, tpr, _ = roc_curve(y_true, y_score)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='#2ca02c', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC)')
    plt.legend(loc="lower right")
    plt.tight_layout()
    save_path = os.path.join(RESULTS_DIR, 'viz_roc_curve.png')
    plt.savefig(save_path, dpi=300)
    print(f"Saved {save_path}")

def plot_tpr_by_attack_method(df):
    """Plot TPR (Detection Rate) grouped by attack_type and attack_method as bar chart."""
    # Filter only attack samples
    df_attacks = df[df['ground_truth_is_attack'] == True].copy()
    
    if df_attacks.empty:
        print("No attack samples found, skipping attack method breakdown plot.")
        return
    
    # Calculate TPR per attack_type + attack_method
    results = []
    for attack_type in df_attacks['attack_type'].unique():
        df_type = df_attacks[df_attacks['attack_type'] == attack_type]
        for attack_method in df_type['attack_method'].unique():
            df_method = df_type[df_type['attack_method'] == attack_method]
            tp = len(df_method[df_method['predicted_is_risk'] == True])
            total = len(df_method)
            tpr = tp / total if total > 0 else 0
            results.append({
                'attack_type': attack_type,
                'attack_method': attack_method,
                'TPR': tpr,
                'total': total
            })
    
    df_tpr = pd.DataFrame(results)
    
    # Create grouped bar chart
    fig, ax = plt.subplots(figsize=(14, 7))
    
    attack_types = df_tpr['attack_type'].unique()
    attack_methods = sorted(df_tpr['attack_method'].unique())
    
    x = np.arange(len(attack_methods))
    width = 0.35
    
    colors = {
        'type2_embedded': '#1f77b4', 
        'type3_superimposed': '#d62728',
        'mixed': '#ff7f0e',
        'benign_noise': '#2ca02c'
    }
    
    for i, attack_type in enumerate(attack_types):
        df_type = df_tpr[df_tpr['attack_type'] == attack_type]
        tprs = []
        for method in attack_methods:
            row = df_type[df_type['attack_method'] == method]
            tprs.append(row['TPR'].values[0] if len(row) > 0 else 0)
        
        offset = (i - len(attack_types)/2 + 0.5) * width
        bars = ax.bar(x + offset, tprs, width, label=attack_type, color=colors.get(attack_type, '#888888'))
        
        # Add value labels on bars
        for bar, tpr in zip(bars, tprs):
            if tpr > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                       f'{tpr:.0%}', ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('Attack Method')
    ax.set_ylabel('True Positive Rate (Detection Rate)')
    ax.set_title('Detection Rate by Attack Type and Method')
    ax.set_xticks(x)
    ax.set_xticklabels(attack_methods, rotation=45, ha='right')
    ax.set_ylim(0, 1.15)
    ax.legend(title='Attack Type')
    ax.axhline(y=1.0, color='green', linestyle=':', alpha=0.5, label='100% Detection')
    
    plt.tight_layout()
    save_path = os.path.join(RESULTS_DIR, 'viz_tpr_by_attack_method.png')
    plt.savefig(save_path, dpi=300)
    print(f"Saved {save_path}")

def plot_heatmap_tpr(df):
    """Plot heatmap of TPR by attack_type x attack_method."""
    df_attacks = df[df['ground_truth_is_attack'] == True].copy()
    
    if df_attacks.empty:
        print("No attack samples found, skipping heatmap.")
        return
    
    # Calculate TPR matrix
    attack_types = sorted(df_attacks['attack_type'].unique())
    attack_methods = sorted(df_attacks['attack_method'].unique())
    
    tpr_matrix = []
    for attack_type in attack_types:
        row = []
        for attack_method in attack_methods:
            df_cell = df_attacks[(df_attacks['attack_type'] == attack_type) & 
                                  (df_attacks['attack_method'] == attack_method)]
            if len(df_cell) > 0:
                tp = len(df_cell[df_cell['predicted_is_risk'] == True])
                tpr = tp / len(df_cell)
            else:
                tpr = np.nan
            row.append(tpr)
        tpr_matrix.append(row)
    
    df_heatmap = pd.DataFrame(tpr_matrix, index=attack_types, columns=attack_methods)
    
    plt.figure(figsize=(12, 5))
    sns.heatmap(df_heatmap, annot=True, fmt='.0%', cmap='RdYlGn', vmin=0, vmax=1,
                cbar_kws={'label': 'Detection Rate (TPR)'}, linewidths=0.5)
    plt.title('Detection Rate Heatmap: Attack Type × Attack Method')
    plt.xlabel('Attack Method')
    plt.ylabel('Attack Type')
    plt.tight_layout()
    save_path = os.path.join(RESULTS_DIR, 'viz_heatmap_tpr.png')
    plt.savefig(save_path, dpi=300)
    print(f"Saved {save_path}")

def main():
    csv_path = os.path.join(RESULTS_DIR, "defense_results_detailed.csv")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Could not read {csv_path}: {e}")
        print("Please run evaluate_defense.py first to generate results.")
        return
        
    print(f"Plotting for {len(df)} samples...")
    
    # Ensure results dir exists (it should, but safety first)
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    # Original plots
    plot_distributions(df)
    plot_scatter(df)
    plot_roc(df)
    
    # New breakdown plots
    if 'attack_type' in df.columns and 'attack_method' in df.columns:
        plot_tpr_by_attack_method(df)
        plot_heatmap_tpr(df)
    else:
        print("Warning: attack_type/attack_method columns not found. Run updated evaluate_defense.py first.")

if __name__ == "__main__":
    main()
