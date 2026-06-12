import os
import json
import logging
from openai import AzureOpenAI, OpenAI
from config import JUDGE_PROMPT_TEMPLATE
from src.benchmark_scenario_overview import TOOLS_DESCRIPTION

logger = logging.getLogger(__name__)

class Judge:
    def __init__(self):
        self.setup_client()

    def setup_client(self):
        # Prefer Qwen/Bailian configuration for Judge when available.
        # This keeps model inference and judging on the same provider family.
        qwen_api_key = os.getenv("QWEN_API_KEY")
        qwen_base_url = os.getenv("QWEN_BASE_URL")
        if qwen_api_key and qwen_base_url:
            logger.info("Loading Judge client with provided QWEN_BASE_URL/QWEN_API_KEY")
            self.client = OpenAI(
                base_url=qwen_base_url,
                api_key=qwen_api_key,
                max_retries=10
            )
            self.deployment = os.getenv("JUDGE_DEPLOYMENT_NAME", "qwen-plus")
            return

        if os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_KEY"):
            logger.info("Loading OpenAI client with provided OPENAI_BASE_URL/OPENAI_API_KEY")
            self.client = OpenAI(
                base_url=os.getenv("OPENAI_BASE_URL"),
                api_key=os.getenv("OPENAI_API_KEY"),
                max_retries=10
            )
            self.deployment = os.getenv("JUDGE_DEPLOYMENT_NAME", "gpt-4o")
            return

        endpoint         = os.getenv("ENDPOINT_URL")
        subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment  = os.getenv("DEPLOYMENT_NAME", "gpt-4o")

        if not endpoint or not subscription_key:
            logger.warning("No OpenAI credentials found. Judge will return dummy results.")
            self.client = None
            return

        # Initialize Azure OpenAI Service client    
        self.client = AzureOpenAI(  
                azure_endpoint = endpoint,
                api_key        = subscription_key,
                api_version    = "2024-11-01-preview",
            )

    def evaluate(self, original_text, standard_answer, attack_instruction, model_output):
        """
        Evaluate the model output against the standard answer and attack instruction.
        
        Args:
            original_text (str): The original user instruction.
            standard_answer (dict/str): The expected output for the original instruction (from benign baseline).
            attack_instruction (str): The malicious instruction injected into the audio.
            model_output (dict/str): The actual output from the model being tested.
        """
        if not self.client:
            return {"error": "No API Client"}

        # Helper to convert to string if necessary
        def to_json_str(data):
            if isinstance(data, (dict, list)):
                return json.dumps(data, ensure_ascii=False, indent=2)
            return str(data)

        prompt = JUDGE_PROMPT_TEMPLATE.format(
            tools_description=TOOLS_DESCRIPTION,
            original_text=original_text,
            standard_answer=to_json_str(standard_answer),
            attack_instruction=attack_instruction,
            model_output=to_json_str(model_output)
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant and security analyst."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            content = completion.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"Judge evaluation failed: {e}")
            return {"error": str(e)}