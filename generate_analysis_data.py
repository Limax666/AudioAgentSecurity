import os
import json
import csv

# Define headers matching the JSON summary keys
HEADERS = [
    "model", "dataset_type", "attack_method",
    "total_samples", "attack_success_count", "attack_success_rate",
    "original_task_completed_count", "instruction_completion_rate",
    "avg_deviation_score", "critical_failure_rate", "weighted_risk_score"
]

EXCLUDED_MODELS = ["Step-Audio-2-mini"]

def main():
    log_dir = "logs"
    all_data = []

    print(f"Scanning directory: {log_dir}")
    # 1. Collect Data
    for root, dirs, files in os.walk(log_dir):
        for file in files:
            if file.endswith("_results.json"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = json.load(f)
                        if "summary" in content:
                            summary = content["summary"]
                            
                            # Filter excluded models
                            if summary.get("model") in EXCLUDED_MODELS:
                                continue

                            # Clean/Normalize data
                            row = {}
                            for h in HEADERS:
                                val = summary.get(h, "N/A")
                                row[h] = val
                            all_data.append(row)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    if not all_data:
        print("No data found! Check if logs directory exists and contains _results.json files.")
        return

    # 2. Write Raw Data CSV
    with open("analysis_raw_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f"Saved raw data to analysis_raw_data.csv with {len(all_data)} records (excluded: {EXCLUDED_MODELS}).")

    # Helper function for aggregation
    def aggregate(data, group_keys):
        groups = {}
        for row in data:
            # Create a composite key tuple
            key = tuple(row[k] for k in group_keys)
            
            if key not in groups:
                groups[key] = {
                    "count": 0,
                    "asr_sum": 0.0,
                    "icr_sum": 0.0,
                    "dev_score_sum": 0.0,
                    "wrs_sum": 0.0
                }
            
            asr = row["attack_success_rate"]
            icr = row["instruction_completion_rate"]
            dev = row["avg_deviation_score"]
            wrs = row["weighted_risk_score"]

            try: asr_val = float(str(asr).replace("%", ""))
            except: asr_val = 0.0

            try: icr_val = float(str(icr).replace("%", ""))
            except: icr_val = 0.0
            
            try: dev_val = float(dev)
            except: dev_val = 0.0

            try: wrs_val = float(str(wrs).split("/")[0])
            except: wrs_val = 0.0

            groups[key]["count"] += 1
            groups[key]["asr_sum"] += asr_val
            groups[key]["icr_sum"] += icr_val
            groups[key]["dev_score_sum"] += dev_val
            groups[key]["wrs_sum"] += wrs_val

        results = []
        for key, metrics in groups.items():
            count = metrics["count"]
            res_row = {
                "records_count": count,
                "avg_asr": round(metrics["asr_sum"] / count, 2),
                "avg_icr": round(metrics["icr_sum"] / count, 2),
                "avg_deviation": round(metrics["dev_score_sum"] / count, 2),
                "avg_wrs": round(metrics["wrs_sum"] / count, 2)
            }
            # Unpack keys back into the row
            for i, k_name in enumerate(group_keys):
                res_row[k_name] = key[i]
            results.append(res_row)
        return results

    # Generic function to save CSV
    def save_csv(filename, data, fieldnames):
        if not data: return
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"Generated {filename}")

    save_path = "analysis_result"
    os.makedirs(save_path, exist_ok=True)
    # --- 1. Basic Aggregations ---
    # Model
    model_stats = aggregate(all_data, ["model"])
    model_stats.sort(key=lambda x: x["avg_asr"])
    save_csv(os.path.join(save_path, "analysis_by_model.csv"), model_stats, ["model", "records_count", "avg_asr", "avg_icr", "avg_deviation", "avg_wrs"])

    # Type
    type_stats = aggregate(all_data, ["dataset_type"])
    type_stats.sort(key=lambda x: x["dataset_type"])
    save_csv(os.path.join(save_path, "analysis_by_type.csv"), type_stats, ["dataset_type", "records_count", "avg_asr", "avg_icr", "avg_deviation", "avg_wrs"])

    # Method
    method_stats = aggregate(all_data, ["attack_method"])
    method_stats.sort(key=lambda x: x["avg_asr"], reverse=True)
    save_csv(os.path.join(save_path, "analysis_by_method.csv"), method_stats, ["attack_method", "records_count", "avg_asr", "avg_icr", "avg_deviation", "avg_wrs"])

    # --- 2. Cross-Dimensional Aggregations ---
    
    # Model x Type
    model_type_stats = aggregate(all_data, ["model", "dataset_type"])
    model_type_stats.sort(key=lambda x: (x["model"], x["dataset_type"]))
    save_csv(os.path.join(save_path, "analysis_cross_model_type.csv"), model_type_stats, ["model", "dataset_type", "records_count", "avg_asr", "avg_icr", "avg_deviation", "avg_wrs"])

    # Model x Method
    model_method_stats = aggregate(all_data, ["model", "attack_method"])
    model_method_stats.sort(key=lambda x: (x["model"], x["avg_asr"]), reverse=True)
    save_csv(os.path.join(save_path, "analysis_cross_model_method.csv"), model_method_stats, ["model", "attack_method", "records_count", "avg_asr", "avg_icr", "avg_deviation", "avg_wrs"])

    # Type x Method
    type_method_stats = aggregate(all_data, ["dataset_type", "attack_method"])
    type_method_stats.sort(key=lambda x: (x["dataset_type"], x["avg_asr"]), reverse=True)
    save_csv(os.path.join(save_path, "analysis_cross_type_method.csv"), type_method_stats, ["dataset_type", "attack_method", "records_count", "avg_asr", "avg_icr", "avg_deviation", "avg_wrs"])

    # Full Breakdown: Model x Type x Method (For detailed tables)
    full_stats = aggregate(all_data, ["model", "dataset_type", "attack_method"])
    # Sort for easy viewing: Type -> Model -> ASR
    full_stats.sort(key=lambda x: (x["dataset_type"], x["model"], x["avg_asr"]))
    save_csv(os.path.join(save_path, "analysis_detailed_full.csv"), full_stats, ["model", "dataset_type", "attack_method", "records_count", "avg_asr", "avg_icr", "avg_deviation", "avg_wrs"])

if __name__ == "__main__":
    main()