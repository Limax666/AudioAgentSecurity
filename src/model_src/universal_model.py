import os
import io
import base64
import logging
import time
import numpy as np
import soundfile as sf
from tqdm import tqdm
from openai import OpenAI

# Logging Setup
logger = logging.getLogger(__name__)

def universal_model_loader(self):
    """
    Loads the OpenAI-compatible client based on the model name.
    """
    self.model_name_lower = self.model_name.lower()
    
    if "minicpm" in self.model_name_lower:
        api_key = os.getenv("CUSTOM_API_KEY", "empty")
        base_url = os.getenv("CUSTOM_BASE_URL", "http://127.0.0.1:18000/v1")
        logger.info(f"Loading MiniCPM model (OpenAI-compatible): {self.model_name}")
    elif "step" in self.model_name_lower:
        api_key = os.getenv("CUSTOM_API_KEY", "empty")
        base_url = os.getenv("CUSTOM_BASE_URL", "http://127.0.0.1:8000/v1")
        logger.info(f"Loading Step-Audio model (OpenAI-compatible): {self.model_name}")
    elif "mimo" in self.model_name_lower:
        api_key = os.getenv("CUSTOM_API_KEY", "empty")
        base_url = "http://127.0.0.1:18000/v1"
        logger.info(f"Loading mimo model (OpenAI-compatible): {self.model_name}")
    elif "qwen" in self.model_name_lower:
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        base_url = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        logger.info(f"Loading Qwen model (OpenAI-compatible): {self.model_name}")
    elif "fun-audio" in self.model_name_lower:
        api_key = os.getenv("CUSTOM_API_KEY", "empty")
        # base_url = os.getenv("CUSTOM_BASE_URL", "http://127.0.0.1:8000/v1")
        base_url = "http://127.0.0.1:18001/v1"
        logger.info(f"Loading fun-audio model (OpenAI-compatible): {self.model_name}")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        logger.info(f"Loading model (OpenAI-compatible): {self.model_name}")

    if not api_key:
        logger.warning(f"API Key not found for model {self.model_name}. Please check your .env file.")

    self.client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    # Use the provided model name directly as the deployment/model name
    self.deployment = self.model_name
    logger.info(f"Client loaded for deployment: {self.deployment}")


def do_sample_inference(self, audio_array, instruction, sampling_rate=16000):
    """
    Performs a single inference call.
    """
    # Create an in-memory buffer
    buffer = io.BytesIO()
    sf.write(buffer, audio_array, sampling_rate, format='WAV')
    wav_data = buffer.getvalue()
    
    # Encode to Base64
    encoded_string_raw = base64.b64encode(wav_data).decode('utf-8')
    
    # Determine format based on model family
    if "qwen" in self.model_name_lower:
        # Qwen implementation in this project expects the Data URI prefix
        encoded_string = f"data:audio/wav;base64,{encoded_string_raw}"

        # Qwen specific parameters
        # Note: enable_thinking is only supported by qwen3-omni-flash; newer models reject it.
        extra_params = {
            "stream": True,
            "stream_options": {"include_usage": True},
            "modalities": ["text"]
        }
        audio_content_part = {
            "type": "input_audio",
            "input_audio": {"data": encoded_string, "format": "wav"},
        }
    elif "gemini" in self.model_name_lower:
        # rcouyi-style Gemini: audio sent as a file-typed content part with data URI.
        encoded_string = f"data:audio/wav;base64,{encoded_string_raw}"
        extra_params = {
            "stream": False,
            "temperature": 1.0,  # gemini-3-pro forces 1.0; safe default for the family
        }
        audio_content_part = {
            "type": "file",
            "file": {"filename": "audio.wav", "file_data": encoded_string},
        }
    else:
        # Standard OpenAI Audio/GPT-4o-Audio usually expects raw base64 in the 'data' field
        # (based on typical usage, though some proxies might vary. Sticking to raw as per standard).
        encoded_string = encoded_string_raw

        # Standard parameters
        extra_params = {
            "stream": False,
            "modalities": ["text"],
            "temperature": 0.7,
            "top_p": 0.95
        }
        audio_content_part = {
            "type": "input_audio",
            "input_audio": {"data": encoded_string, "format": "wav"},
        }

    chat_prompt = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": instruction},
                audio_content_part,
            ]
        }
    ]

    try:
        # Attempt to enforce JSON format by default
        # BUT: gpt-4o-audio-preview does not support json_object mode yet.
        if "gpt-4o-audio" in self.model_name_lower:
            pass # Do not add response_format
        else:
            extra_params["response_format"] = {"type": "json_object"}

        def _do_call(params):
            """Call API with explicit backoff on upstream 503/429 (rate-limit)."""
            max_attempts = 6
            for attempt in range(max_attempts):
                try:
                    return self.client.chat.completions.create(
                        model=self.deployment,
                        messages=chat_prompt,
                        **params,
                    )
                except Exception as exc:
                    msg = str(exc)
                    is_rate_limit = (
                        "503" in msg
                        or "429" in msg
                        or "high demand" in msg.lower()
                        or "rate limit" in msg.lower()
                    )
                    if is_rate_limit and attempt < max_attempts - 1:
                        wait = 60 * (attempt + 1)  # 60s, 120s, 180s, ...
                        logger.warning(
                            f"Upstream rate-limit ({msg[:120]}...). "
                            f"Sleeping {wait}s before retry {attempt + 2}/{max_attempts}."
                        )
                        time.sleep(wait)
                        continue
                    raise

        try:
            completion = _do_call(extra_params)
        except Exception as e:
            # Fallback: If JSON mode is not supported, log warning and retry without it
            logger.warning(f"JSON enforcement failed for {self.model_name}: {e}. Falling back to prompt-only constraint.")
            if "response_format" in extra_params:
                del extra_params["response_format"]

            completion = _do_call(extra_params)

        if extra_params.get("stream"):
            # Handle streaming response
            full_response = ""
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
            response = full_response
        else:
            # Handle standard response
            response = completion.choices[0].message.content

    except Exception as e:
        logger.error(f"Inference Error for {self.model_name}: {e}")
        # Minimal exception handling as requested: log and return dummy
        response = "Dummy model generation."
        time.sleep(2)

    return response


def universal_model_generation(self, input_data):
    """
    Main generation function handling audio pre-processing (chunking/padding).
    """
    audio_array    = input_data["audio"]["array"]
    sampling_rate  = input_data["audio"]["sampling_rate"]
    audio_duration = len(audio_array) / sampling_rate
    instruction    = input_data["instruction"]
    task_type      = input_data.get('task_type', '')

    os.makedirs('tmp', exist_ok=True) # Ensure tmp dir exists if needed

    # Logic for chunking or padding
    if audio_duration > 30 and task_type == 'ASR':
        logger.info('Audio duration > 30s (ASR). Chunking...')
        audio_chunks = []
        chunk_size = 30 * sampling_rate
        for i in range(0, len(audio_array), chunk_size):
            audio_chunks.append(audio_array[i : i + chunk_size])
        
        # Process chunks
        model_predictions = [
            do_sample_inference(self, chunk, instruction, sampling_rate) 
            for chunk in tqdm(audio_chunks, desc="Processing chunks")
        ]
        output = ' '.join(model_predictions)

    elif audio_duration > 30:
        logger.info('Audio duration > 30s. Truncating to first 30s...')
        audio_array = audio_array[:30 * sampling_rate]
        output = do_sample_inference(self, audio_array, instruction, sampling_rate)
    
    else: 
        if audio_duration < 1:
            logger.info('Audio duration < 1s. Padding...')
            audio_array = np.pad(audio_array, (0, sampling_rate), 'constant')
        
        output = do_sample_inference(self, audio_array, instruction, sampling_rate)

    return output
