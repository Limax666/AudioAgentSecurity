# DolphinAttack Benchmark: Handover Guide

This document provides short instructions for setting up and running the DolphinAttack benchmark generation pipeline.

## 1. Quick Setup

```bash
# 1. Install dependencies
pip install numpy scipy pydub dashscope faker

# 2. Configure API Key (Required for TTS generation)
set DASHSCOPE_API_KEY=your_actual_api_key_here
```

## 2. File Overview

| File | Description |
| :--- | :--- |
| `generate_high_energy_benchmark.py` | **Entry Point**. Run this to generate the dataset. |
| `dataset_config.py` | Configuration for instruction templates and categories. |
| `audio_attack_lib.py` | DSP library for audible attacks (Whisper, Scramble, etc.). |
| `dolphin_lib.py` | Ultrasonic modulation and hardware simulation library. |

## 3. Usage Examples

### Generate a small test batch
```bash
python generate_high_energy_benchmark.py --count 5
```

### Generate benchmark with specific SNR
```bash
python generate_high_energy_benchmark.py --count 50 --snr -20.0
```

## 4. Key Outputs

- **`benchmark_dataset_mixed/`**: Contains the final wav files.
  - `benign/`: Original user instructions.
  - `mixed/`: Folders categorized by attack method (e.g., `dolphin/`, `whisper/`).
- **`metadata.json`**: Detailed mapping of every sample, including texts, strategies, and timing offsets.

## 5. Notes for Success
- **TTS Generation**: Requires an active internet connection.
- **Energy Injection**: All attacks are processed through DRC (Dynamic Range Compression) to ensure peak power before mixing.
- **FS_HIGH**: The processing uses **192kHz** internally to support ultrasonic simulations.
