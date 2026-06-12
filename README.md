# Piggybacking on Perception: Stealthy Concurrent Audio Prompt Injections against Multimodal LLM Agents

This repository contains the source code and evaluation framework for **AttackBench**, a systematic study on **covert concurrent audio prompt injections against multimodal LLM agents**.

In addition to the main CADV defense, the repository now supports two lightweight **prompt-level defense baselines** requested by reviewers:

- **Explicit Instruction Defense**: strengthens the system prompt with a clear rule to ignore any audio segment that claims to update, override, or replace the current task.
- **Sandwich Defense**: wraps the user transcription with a reminder to execute only the original intent and ignore any injected override-like text.

---

## 1. Repository structure

Important files for the main and supplementary experiments:

- `main_attack.py` — main attack evaluation entry; now supports `--defense_mode`.
- `src/inference.py` — model inference wrapper; now composes prompt-level defenses.
- `src/dataset.py` — loads benchmark metadata and resolves audio paths.
- `src/judge.py` — judges whether the original task was completed and whether the attack succeeded.
- `defense/defense_module.py` — CADV implementation.
- `defense/evaluate_defense.py` — CADV evaluation script.
- `generate_benign_baselines.py` — generate benign text baselines.
- `generate_analysis_data.py` — aggregate `logs/` into CSV summaries.
- `generate_report.py` — generate summary tables and markdown reports.

The repository also includes previously generated evaluation outputs under `logs/` and `defense_log/`.

---

## 2. Environment setup

### 2.1 Recommended Python version

Python 3.10 or 3.11 is recommended.

### 2.2 Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If you prefer `uv`:

```bash
uv venv
uv sync
```

### 2.3 Configure API keys

Create a `.env` file in the project root.

```ini
# OpenAI-compatible API
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# Qwen family (optional)
QWEN_API_KEY=your_qwen_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Custom local endpoints for certain models
CUSTOM_API_KEY=your_custom_key
CUSTOM_BASE_URL=http://127.0.0.1:18000/v1

# DashScope for TTS / related utilities
DASHSCOPE_API_KEY=your_dashscope_key
```

The exact keys depend on the model family you evaluate.

---

## 3. Obtain the benchmark dataset from Hugging Face

The benchmark dataset is hosted at:

- `https://huggingface.co/datasets/Limax11/AudioAgentSecurity`

### 3.1 Install Hugging Face tools

```bash
pip install -U huggingface_hub datasets
```

### 3.2 Download the dataset

#### Option A — Python

```python
from datasets import load_dataset

ds = load_dataset("Limax11/AudioAgentSecurity")
print(ds)
```

#### Option B — CLI

```bash
huggingface-cli download Limax11/AudioAgentSecurity --repo-type dataset --local-dir benchmark_dataset_v5
```

### 3.3 Expected local layout

The evaluation pipeline expects the mixed benchmark to be available locally at:

```text
benchmark_dataset_mixed/
```

A typical layout is:

```text
benchmark_dataset_mixed/
├── metadata.json
└── mixed/
    ├── dialect/
    ├── dolphin/
    ├── foreign/
    ├── high_freq/
    ├── pulse/
    ├── spectral_inversion/
    ├── spectral_scramble/
    ├── speed/
    ├── texture/
    └── whisper/
```

If your local path differs, pass `--data_dir` explicitly.

---

## 4. Benign baselines

Before evaluating attacks, generate benign text baselines. These are used by `main_attack.py` to decide whether the original user task was completed.

```bash
python generate_benign_baselines.py --model_name qwen2.5-omni-7b
```

This should create the baseline JSON file required by the evaluation pipeline.

---

## 5. Main attack evaluation

### 5.1 Evaluate one attack method

```bash
python main_attack.py --model_name gemini-2.5-flash --dataset_type mixed --attack_method dolphin
```

### 5.2 Evaluate all attack methods

```bash
python main_attack.py --model_name gemini-2.5-flash --dataset_type mixed --attack_method all
```

### 5.3 Evaluate real-world distance and angle experiments

The repository includes two additional physical-world benchmark metadata folders:

- `distance_dataset/` — distance-controlled over-the-air attack benchmark.
- `angle_dataset/` — angle-controlled directional attack benchmark.

Use `main_attack.py` with `--data_dir` pointing to the corresponding dataset folder. The `--dataset_type` value is used as the result namespace; for these real-world experiments, use `distance` and `angle` respectively.

#### Distance experiment

Evaluate one attack method:

```bash
python main_attack.py --model_name gemini-2.5-flash --data_dir distance_dataset --dataset_type distance --attack_method dolphin
```

Evaluate all attack methods in `distance_dataset/metadata.json`:

```bash
python main_attack.py --model_name gemini-2.5-flash --data_dir distance_dataset --dataset_type distance --attack_method all
```

#### Angle experiment

Evaluate one attack method:

```bash
python main_attack.py --model_name gemini-2.5-flash --data_dir angle_dataset --dataset_type angle --attack_method dolphin
```

Evaluate all attack methods in `angle_dataset/metadata.json`:

```bash
python main_attack.py --model_name gemini-2.5-flash --data_dir angle_dataset --dataset_type angle --attack_method all
```

For faster reviewer-side smoke tests, add `--limit` and `--workers`, for example:

```bash
python main_attack.py --model_name gemini-2.5-flash --data_dir distance_dataset --dataset_type distance --attack_method all --limit 5 --workers 4
python main_attack.py --model_name gemini-2.5-flash --data_dir angle_dataset --dataset_type angle --attack_method all --limit 5 --workers 4
```

Full runs write outputs to:

```text
logs/<model_name>/distance/<defense_mode>/<attack_method>_results.json
logs/<model_name>/angle/<defense_mode>/<attack_method>_results.json
```

For example:

```text
logs/gemini-2.5-flash/distance/none/dolphin_results.json
logs/gemini-2.5-flash/angle/none/dolphin_results.json
```

### 5.4 Useful flags

- `--limit N` — evaluate only the first `N` samples.
- `--workers N` — use multithreaded evaluation.
- `--rerun_failed` — rerun previously failed samples.
- `--defense_mode` — choose prompt-level defense mode.
- `--data_dir PATH` — choose the local benchmark folder, e.g., `benchmark_dataset_mixed`, `distance_dataset`, or `angle_dataset`.

Example:

```bash
python main_attack.py --model_name gemini-2.5-flash --dataset_type mixed --attack_method all --workers 4
```

Results are stored under:

```text
logs/<model_name>/<dataset_type>/<defense_mode>/<attack_method>_results.json
```

For example, the explicit-defense run is saved under:

```text
logs/gemini-2.5-flash/mixed/explicit/
```

Each result file contains:
- `summary` — aggregate metrics such as ASR, ICR, CFR, WRS, and average deviation score.
- `results` — per-sample outputs and evaluation decisions.

---

## 6. Supplemental prompt-level defense experiments

The repository now supports two reviewer-requested prompt baselines.

### 6.1 Defense modes

- `none` — original system prompt.
- `explicit` — adds a system-prompt instruction to ignore any segment that attempts to update, override, or replace the task.
- `sandwich` — adds a sandwich-style wrapper reminding the model to obey only the user’s original intent.

### 6.2 Run the supplementary defense baselines

#### No defense baseline

You do **not** need to rerun this if the baseline logs already exist under `logs/`.

#### Explicit instruction defense

```bash
python main_attack.py --model_name gemini-2.5-flash --dataset_type mixed --attack_method all --defense_mode explicit
```

#### Sandwich defense

```bash
python main_attack.py --model_name gemini-2.5-flash --dataset_type mixed --attack_method all --defense_mode sandwich
```

### 6.3 Recommended experiment matrix

For the paper supplement or rebuttal, run the following conditions on the same dataset split and model:

- `none`
- `explicit`
- `sandwich`
- `CADV`
- optionally `explicit + CADV`
- optionally `sandwich + CADV`

This lets you answer both reviewer questions:

1. Does a simple system-prompt instruction reduce ASR?
2. Does CADV still provide extra benefit beyond prompt-level mitigation?

---

## 7. CADV evaluation

Run the CADV defense evaluation with:

```bash
python defense/evaluate_defense.py
```

This script writes detailed results to the `defense/` results folder and generates summary metrics for the mixed benchmark.

If necessary, adjust the internal benchmark path in the script to match your local dataset location.

---

## 8. Aggregate and summarize results

### 8.1 Aggregate attack logs

```bash
python generate_analysis_data.py
```

This scans `logs/` and writes summary CSVs under `analysis_result/`.

### 8.2 Generate a report

```bash
python generate_report.py
```

This is useful after you have both attack results and defense results.

---

## 9. How to structure the supplementary results

For the rebuttal or appendix, report:

- ASR under `none`, `explicit`, `sandwich`, and `CADV`
- ASR reduction relative to no defense
- extra gain from CADV on top of prompt-level defenses
- per-attack-method breakdown across all 10 attack patterns

A compact table is recommended:

| Attack Method | No Defense ASR | Explicit ASR | Sandwich ASR | CADV ASR | Prompt + CADV ASR |
|---|---:|---:|---:|---:|---:|

This directly addresses the reviewer’s concern about low-cost prompt-level mitigations.

---

## 10. Practical notes

- Use the same model and dataset split across all conditions.
- Use the same `metadata.json` and benign baselines across all comparisons.
- If a run is interrupted, `main_attack.py` resumes from the existing JSON log.
- For the rebuttal, emphasize that prompt-level defenses and CADV are **complementary** rather than redundant.

---

## 11. Citation-ready summary statement

> We additionally evaluated two lightweight prompt-level baselines, explicit instruction defense and sandwich defense, both of which require no extra ML components. These baselines can reduce ASR on some attack types, confirming that concurrent injection prefixes contribute to the attack mechanism. However, residual success remains non-trivial, and CADV still provides additional gains, indicating that audio-level detection and prompt-level mitigation are complementary defenses.
