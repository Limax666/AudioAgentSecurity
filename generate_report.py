import os
import json
import glob
import logging

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def parse_percentage(value_str):
    """Parses a percentage string like '12.34%' to a float 12.34"""
    try:
        return float(value_str.replace('%', '').split()[0]) # split to handle ' (N/A)' etc
    except (ValueError, AttributeError):
        return 0.0

def parse_score(value_str):
    """Parses a score string like '12.34/100' to a float 12.34"""
    try:
        if isinstance(value_str, (int, float)):
            return float(value_str)
        return float(value_str.split('/')[0])
    except (ValueError, AttributeError):
        return 0.0

def generate_markdown_table(data, headers):
    """Generates a Markdown table from a list of dicts."""
    if not data:
        return "No data found."

    # Create header row
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    
    lines = [header_row, separator_row]
    
    for row in data:
        line = "| " + " | ".join(str(row.get(h, "N/A")) for h in headers) + " |"
        lines.append(line)
    
    return "\n".join(lines)

def main():
    log_dir = 'logs'
    output_md = 'results_summary.md'
    output_csv = 'results_summary.csv'
    
    logger.info(f"Scanning {log_dir} for result files...")
    
    # Recursively find all json files ending with _results.json
    # Pattern: logs/**/?*_results.json
    # Using os.walk to be safe across OS and python versions
    result_files = []
    for root, dirs, files in os.walk(log_dir):
        for file in files:
            if file.endswith('_results.json'):
                result_files.append(os.path.join(root, file))

    if not result_files:
        logger.warning("No result files found.")
        return

    all_summaries = []

    for file_path in result_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if "summary" in data:
                summary = data["summary"]
                # Add file path for reference if needed, or extract implicit info
                summary['source_file'] = file_path
                all_summaries.append(summary)
            else:
                logger.warning(f"Skipping {file_path}: No 'summary' key found.")
        
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")

    # Sort by Model, then Dataset Type, then Attack Method
    all_summaries.sort(key=lambda x: (x.get('model', ''), x.get('dataset_type', ''), x.get('attack_method', '')))

    # Define columns to display
    columns = [
        "model", 
        "dataset_type", 
        "attack_method", 
        "total_samples", 
        "attack_success_rate", 
        "critical_failure_rate", 
        "weighted_risk_score", 
        "instruction_completion_rate", 
        "avg_deviation_score"
    ]
    
    # Mapping for cleaner headers
    headers = [
        "Model", 
        "Dataset", 
        "Method", 
        "Samples", 
        "ASR", 
        "CFR", 
        "WRS", 
        "ICR", 
        "ADS"
    ]
    
    # Prepare data for table
    table_data = []
    for s in all_summaries:
        row = {}
        for col, head in zip(columns, headers):
            row[head] = s.get(col, "N/A")
        table_data.append(row)

    # Generate Markdown
    md_content = "# AttackBench Evaluation Results\n\n"
    md_content += f"Generated on: {logging.Formatter().formatTime(logging.LogRecord('',0,'','',0,0,0), '%Y-%m-%d %H:%M:%S')}\n\n"
    md_content += generate_markdown_table(table_data, headers)
    
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    logger.info(f"Markdown report generated: {output_md}")

    # Generate CSV
    import csv
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(table_data)
        
    logger.info(f"CSV report generated: {output_csv}")
    
    # Print to console
    print("\n" + generate_markdown_table(table_data, headers) + "\n")

if __name__ == "__main__":
    main()
