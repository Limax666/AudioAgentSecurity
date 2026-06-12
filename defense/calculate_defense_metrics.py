import os
import json
import csv
import glob

# Determine script directory to ensure paths are relative to this file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths relative to defense/ (SCRIPT_DIR)
DEFENSE_CSV = os.path.join(SCRIPT_DIR, "results", "defense_results_detailed.csv")
LOGS_DIR = os.path.join(SCRIPT_DIR, "..", "logs")
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "results", "analysis_defense_impact.csv")

def normalize_path(path):
    # Standardize separators
    path = path.replace("\\", "/")
    # Find the benchmark dataset root (V5)
    marker = "benchmark_dataset_v5/"
    if marker in path:
        return path.split(marker)[-1]
    # Fallback for V4 if still present in some logs
    marker_v4 = "benchmark_dataset_v4/"
    if marker_v4 in path:
        return path.split(marker_v4)[-1]
    return path

def load_defense_results(csv_path):
    defense_map = {}
    print(f"Loading defense results from {csv_path}...")
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                full_path = row.get("path", "")
                if not full_path:
                    continue
                
                key = normalize_path(full_path)
                
                # 'predicted_is_risk' is 'True' or 'False' string
                is_risk = row.get("predicted_is_risk", "False").lower() == "true"
                defense_map[key] = is_risk
                count += 1
            print(f"Loaded {count} defense entries.")
    except Exception as e:
        print(f"Error loading CSV: {e}")
    return defense_map

def calculate_metrics():
    defense_map = load_defense_results(DEFENSE_CSV)
    
    # Structure to hold aggregated results
    report_data = []
    
    # Find all result files
    # Expected structure: logs/<Model>/<Type>/<Method>_results.json
    pattern = os.path.join(LOGS_DIR, "*", "*", "*_results.json")
    files = glob.glob(pattern)
    
    print(f"Found {len(files)} log files. Processing...")
    
    for file_path in files:
        parts = os.path.normpath(file_path).split(os.sep)
        if len(parts) < 4:
            continue
        
        dataset_type = parts[-2] # e.g., type2, type3, or mixed
        # Support mixed and legacy types
        if dataset_type not in ["type2", "type3", "mixed"]:
            continue
            
        model_name = parts[-3]
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")
            continue

        summary = data.get("summary", {})
        results = data.get("results", [])
        attack_method = summary.get("attack_method", "unknown")
        
        total = len(results)
        if total == 0:
            continue
            
        old_success_count = 0
        new_success_count = 0
        defense_triggered_count = 0
        
        matched_in_defense = 0
        
        for item in results:
            audio_path = item.get("audio_path", "")
            key = normalize_path(audio_path)
        
            evaluation = item.get("evaluation", {})
            if not isinstance(evaluation, dict):
                evaluation = {}
                
            is_success = evaluation.get("attack_success", False)
        
            if is_success:
                old_success_count += 1
                
            # Defense Check
            is_blocked = False
            if key in defense_map:
                matched_in_defense += 1
                if defense_map[key]:
                    is_blocked = True
            
            if is_blocked:
                defense_triggered_count += 1
                new_success = False
            else:
                new_success = is_success
            
            if new_success:
                new_success_count += 1

        # Calculate Rates
        old_asr = (old_success_count / total) * 100
        new_asr = (new_success_count / total) * 100
        defense_rate = (defense_triggered_count / total) * 100
        match_rate = (matched_in_defense / total) * 100
        
        report_data.append({
            "model": model_name,
            "dataset_type": dataset_type,
            "attack_method": attack_method,
            "total_samples": total,
            "old_asr": round(old_asr, 2),
            "new_asr": round(new_asr, 2),
            "defense_trigger_rate": round(defense_rate, 2),
            "defense_coverage": round(match_rate, 2)
        })

    # Save to CSV
    headers = ["model", "dataset_type", "attack_method", "total_samples", "old_asr", "new_asr", "defense_trigger_rate", "defense_coverage"]
    
    # Sort nicely
    report_data.sort(key=lambda x: (x.get("dataset_type", ""), x.get("model", ""), x.get("attack_method", "")))
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(report_data)
        
    print(f"Analysis complete. Saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    calculate_metrics()