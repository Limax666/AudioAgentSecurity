(dual-agent) E:\AI Agent\ai-agent-projects-main\Telephone_Agent\AudioAgentSecurity-BB64>python main_attack.py --model_name qwen3.5-omni-plus  --data_dir "./distance/2m" --dataset_type "distance/2m" --attack_method all
05/26/2026 22:21:59 - INFO - __main__ - Found 6 attack method(s): ['dialect', 'foreign', 'inversion', 'pulse', 'speed', 'whisper']
05/26/2026 22:21:59 - INFO - __main__ - 
>>> Starting batch task: dialect <<<
05/26/2026 22:21:59 - INFO - __main__ - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:21:59 - INFO - __main__ - Starting Task Evaluation
05/26/2026 22:21:59 - INFO - __main__ - Model: qwen3.5-omni-plus
05/26/2026 22:21:59 - INFO - __main__ - Data Directory: ./distance/2m
05/26/2026 22:21:59 - INFO - __main__ - Dataset Type: distance/2m
05/26/2026 22:21:59 - INFO - __main__ - Attack Method: dialect
05/26/2026 22:21:59 - INFO - __main__ - Defense Mode: none
05/26/2026 22:21:59 - INFO - __main__ - Workers: 1
05/26/2026 22:21:59 - INFO - __main__ - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:21:59 - INFO - __main__ - Loading dataset...
05/26/2026 22:21:59 - INFO - __main__ - Found 1 test cases for dialect.
05/26/2026 22:21:59 - INFO - __main__ - Loading model: qwen3.5-omni-plus
05/26/2026 22:21:59 - INFO - src.model_src.universal_model - Loading Qwen model (OpenAI-compatible): qwen3.5-omni-plus
05/26/2026 22:21:59 - INFO - src.model_src.universal_model - Client loaded for deployment: qwen3.5-omni-plus
05/26/2026 22:21:59 - INFO - src.model - Loaded model: qwen3.5-omni-plus
05/26/2026 22:21:59 - INFO - src.model - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:21:59 - INFO - __main__ - Initializing Judge...
05/26/2026 22:21:59 - INFO - src.judge - Loading Judge client with provided DASHSCOPE_API_KEY/QWEN_BASE_URL
05/26/2026 22:21:59 - INFO - __main__ - Loaded 1 benign baselines from ./distance\benign_baselines_qwen3.5-omni-plus.json
05/26/2026 22:21:59 - INFO - __main__ - Starting inference and evaluation loop...
Evaluating dialect:   0%|                                                                                                                                            | 0/1 [00:00<?, ?it/sE 
:\AI Agent\ai-agent-projects-main\Telephone_Agent\AudioAgentSecurity-BB64\src\inference.py:63: UserWarning: PySoundFile failed. Trying audioread instead.
  data, sr = librosa.load(file_path, sr=target_sr, mono=True)
D:\anaconda\envs\dual-agent\Lib\site-packages\librosa\core\audio.py:183: FutureWarning: librosa.core.audio.__audioread_load
        Deprecated as of librosa version 0.10.0.
        It will be removed in librosa version 1.0.
  y, sr_native = __audioread_load(path, offset, duration, dtype)
05/26/2026 22:22:04 - INFO - httpx - HTTP Request: POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions "HTTP/1.1 200 OK"
05/26/2026 22:22:04 - ERROR - src.model_src.universal_model - Inference Error for qwen3.5-omni-plus: <400> InternalError.Algo.InvalidParameter: The thinking_budget parameter must be a positive integer and not greater than 0
Evaluating dialect:   0%|                                                                                                                                            | 0/1 [00:31<?, ?it/s]
05/26/2026 22:22:30 - INFO - __main__ -
Evaluation interrupted by user. Progress saved.
05/26/2026 22:22:30 - INFO - __main__ -
>>> Completed batch task: dialect <<<
05/26/2026 22:22:30 - INFO - __main__ -
>>> Starting batch task: foreign <<<
05/26/2026 22:22:30 - INFO - __main__ - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:22:30 - INFO - __main__ - Starting Task Evaluation
05/26/2026 22:22:30 - INFO - __main__ - Model: qwen3.5-omni-plus
05/26/2026 22:22:30 - INFO - __main__ - Data Directory: ./distance/2m
05/26/2026 22:22:30 - INFO - __main__ - Dataset Type: distance/2m
05/26/2026 22:22:30 - INFO - __main__ - Attack Method: foreign
05/26/2026 22:22:30 - INFO - __main__ - Defense Mode: none
05/26/2026 22:22:30 - INFO - __main__ - Workers: 1
05/26/2026 22:22:30 - INFO - __main__ - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:22:30 - INFO - __main__ - Loading dataset...
05/26/2026 22:22:30 - INFO - __main__ - Found 1 test cases for foreign.
05/26/2026 22:22:30 - INFO - __main__ - Loading model: qwen3.5-omni-plus
05/26/2026 22:22:30 - INFO - src.model_src.universal_model - Loading Qwen model (OpenAI-compatible): qwen3.5-omni-plus
05/26/2026 22:22:30 - INFO - src.model_src.universal_model - Client loaded for deployment: qwen3.5-omni-plus
05/26/2026 22:22:30 - INFO - src.model - Loaded model: qwen3.5-omni-plus
05/26/2026 22:22:30 - INFO - src.model - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:22:30 - INFO - __main__ - Initializing Judge...
05/26/2026 22:22:30 - INFO - src.judge - Loading Judge client with provided DASHSCOPE_API_KEY/QWEN_BASE_URL
05/26/2026 22:22:30 - INFO - __main__ - Loaded 1 benign baselines from ./distance\benign_baselines_qwen3.5-omni-plus.json
05/26/2026 22:22:30 - INFO - __main__ - Starting inference and evaluation loop...
Evaluating foreign:   0%|                                                                                                                                            | 0/1 [00:00<?, ?it/s]E:\AI Agent\ai-agent-projects-main\Telephone_Agent\AudioAgentSecurity-BB64\src\inference.py:63: UserWarning: PySoundFile failed. Trying audioread instead.
  data, sr = librosa.load(file_path, sr=target_sr, mono=True)
D:\anaconda\envs\dual-agent\Lib\site-packages\librosa\core\audio.py:183: FutureWarning: librosa.core.audio.__audioread_load
        Deprecated as of librosa version 0.10.0.
        It will be removed in librosa version 1.0.
  y, sr_native = __audioread_load(path, offset, duration, dtype)
05/26/2026 22:22:31 - INFO - httpx - HTTP Request: POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions "HTTP/1.1 200 OK"
05/26/2026 22:22:31 - ERROR - src.model_src.universal_model - Inference Error for qwen3.5-omni-plus: <400> InternalError.Algo.InvalidParameter: The thinking_budget parameter must be a positive integer and not greater than 0
Evaluating foreign:   0%|                                                                                                                                            | 0/1 [00:02<?, ?it/s]
05/26/2026 22:22:33 - INFO - __main__ -
Evaluation interrupted by user. Progress saved.
05/26/2026 22:22:33 - INFO - __main__ -
>>> Completed batch task: foreign <<<
05/26/2026 22:22:33 - INFO - __main__ -
>>> Starting batch task: inversion <<<
05/26/2026 22:22:33 - INFO - __main__ - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:22:33 - INFO - __main__ - Starting Task Evaluation
05/26/2026 22:22:33 - INFO - __main__ - Model: qwen3.5-omni-plus
05/26/2026 22:22:33 - INFO - __main__ - Data Directory: ./distance/2m
05/26/2026 22:22:33 - INFO - __main__ - Dataset Type: distance/2m
05/26/2026 22:22:33 - INFO - __main__ - Attack Method: inversion
05/26/2026 22:22:33 - INFO - __main__ - Defense Mode: none
05/26/2026 22:22:33 - INFO - __main__ - Workers: 1
05/26/2026 22:22:33 - INFO - __main__ - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:22:33 - INFO - __main__ - Loading dataset...
05/26/2026 22:22:33 - INFO - __main__ - Found 1 test cases for inversion.
05/26/2026 22:22:33 - INFO - __main__ - Loading model: qwen3.5-omni-plus
05/26/2026 22:22:33 - INFO - src.model_src.universal_model - Loading Qwen model (OpenAI-compatible): qwen3.5-omni-plus
05/26/2026 22:22:33 - INFO - src.model_src.universal_model - Client loaded for deployment: qwen3.5-omni-plus
05/26/2026 22:22:33 - INFO - src.model - Loaded model: qwen3.5-omni-plus
05/26/2026 22:22:33 - INFO - src.model - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:22:33 - INFO - __main__ - Initializing Judge...
05/26/2026 22:22:33 - INFO - src.judge - Loading Judge client with provided DASHSCOPE_API_KEY/QWEN_BASE_URL
05/26/2026 22:22:33 - INFO - __main__ - Loaded 1 benign baselines from ./distance\benign_baselines_qwen3.5-omni-plus.json
05/26/2026 22:22:33 - INFO - __main__ - Starting inference and evaluation loop...
Evaluating inversion:   0%|                                                                                                                                          | 0/1 [00:00<?, ?it/s] 
05/26/2026 22:22:33 - INFO - __main__ -
Evaluation interrupted by user. Progress saved.
05/26/2026 22:22:33 - INFO - __main__ -
>>> Completed batch task: inversion <<<
05/26/2026 22:22:33 - INFO - __main__ -
>>> Starting batch task: pulse <<<
05/26/2026 22:22:33 - INFO - __main__ - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:22:33 - INFO - __main__ - Starting Task Evaluation
05/26/2026 22:22:33 - INFO - __main__ - Model: qwen3.5-omni-plus
05/26/2026 22:22:33 - INFO - __main__ - Data Directory: ./distance/2m
05/26/2026 22:22:33 - INFO - __main__ - Dataset Type: distance/2m
05/26/2026 22:22:33 - INFO - __main__ - Attack Method: pulse
05/26/2026 22:22:33 - INFO - __main__ - Defense Mode: none
05/26/2026 22:22:33 - INFO - __main__ - Workers: 1
05/26/2026 22:22:33 - INFO - __main__ - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:22:33 - INFO - __main__ - Loading dataset...
05/26/2026 22:22:33 - INFO - __main__ - Found 1 test cases for pulse.
05/26/2026 22:22:33 - INFO - __main__ - Loading model: qwen3.5-omni-plus
05/26/2026 22:22:33 - INFO - src.model_src.universal_model - Loading Qwen model (OpenAI-compatible): qwen3.5-omni-plus
05/26/2026 22:22:33 - INFO - src.model_src.universal_model - Client loaded for deployment: qwen3.5-omni-plus
05/26/2026 22:22:33 - INFO - src.model - Loaded model: qwen3.5-omni-plus
05/26/2026 22:22:33 - INFO - src.model - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:22:33 - INFO - __main__ - Initializing Judge...
05/26/2026 22:22:33 - INFO - src.judge - Loading Judge client with provided DASHSCOPE_API_KEY/QWEN_BASE_URL
05/26/2026 22:22:33 - INFO - __main__ - Loaded 1 benign baselines from ./distance\benign_baselines_qwen3.5-omni-plus.json
05/26/2026 22:22:33 - INFO - __main__ - Starting inference and evaluation loop...
Evaluating pulse:   0%|                                                                                                                                              | 0/1 [00:00<?, ?it/s] 
05/26/2026 22:22:34 - INFO - __main__ -
Evaluation interrupted by user. Progress saved.
05/26/2026 22:22:34 - INFO - __main__ -
>>> Completed batch task: pulse <<<
05/26/2026 22:22:34 - INFO - __main__ -
>>> Starting batch task: speed <<<
05/26/2026 22:22:34 - INFO - __main__ - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:22:34 - INFO - __main__ - Starting Task Evaluation
05/26/2026 22:22:34 - INFO - __main__ - Model: qwen3.5-omni-plus
05/26/2026 22:22:34 - INFO - __main__ - Data Directory: ./distance/2m
05/26/2026 22:22:34 - INFO - __main__ - Dataset Type: distance/2m
05/26/2026 22:22:34 - INFO - __main__ - Attack Method: speed
05/26/2026 22:22:34 - INFO - __main__ - Defense Mode: none
05/26/2026 22:22:34 - INFO - __main__ - Workers: 1
05/26/2026 22:22:34 - INFO - __main__ - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:22:34 - INFO - __main__ - Loading dataset...
05/26/2026 22:22:34 - INFO - __main__ - Found 1 test cases for speed.
05/26/2026 22:22:34 - INFO - __main__ - Loading model: qwen3.5-omni-plus
05/26/2026 22:22:34 - INFO - src.model_src.universal_model - Loading Qwen model (OpenAI-compatible): qwen3.5-omni-plus
05/26/2026 22:22:34 - INFO - src.model_src.universal_model - Client loaded for deployment: qwen3.5-omni-plus
05/26/2026 22:22:34 - INFO - src.model - Loaded model: qwen3.5-omni-plus
05/26/2026 22:22:34 - INFO - src.model - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
05/26/2026 22:22:34 - INFO - __main__ - Initializing Judge...
05/26/2026 22:22:34 - INFO - src.judge - Loading Judge client with provided DASHSCOPE_API_KEY/QWEN_BASE_URL