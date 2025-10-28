#!/usr/bin/env python3
"""
AI Analysis Pass - Second Pass Processing
Analyzes and structures relevant data items.
Supports pluggable data enrichment hooks via HookManager.
"""

import requests
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_FILE = PROJECT_ROOT / 'config.json'
PROMPTS_DIR = PROJECT_ROOT / 'prompts'


class AIAnalysisPass:
    """
    Second pass processor that analyzes and structures relevant data.
    Uses AI to extract insights and format according to output schema.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.portkey.ai/v1",
        analysis_prompt: str | None = None,
        system_prompt: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 800,
        timeout: int = 90,
        hook_manager = None
    ):
        """
        Initialize analysis pass processor.

        Args:
            api_key: Portkey API key
            base_url: API endpoint URL
            analysis_prompt: Custom prompt template for analysis (user message)
            system_prompt: System instructions for output format and behavior
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            hook_manager: Optional HookManager for data enrichment hooks
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.hook_manager = hook_manager

        self.analysis_prompt = analysis_prompt or self._load_analysis_prompt()
        self.system_prompt = system_prompt or self._load_system_prompt()

        logger.info(f"Initialized AIAnalysisPass with model: {model}")
        if self.hook_manager:
            logger.info("Hook system enabled for data enrichment")

    def _load_analysis_prompt(self) -> str:
        """
        Load analysis prompt from prompts directory or return default.

        Returns:
            Analysis prompt string
        """
        prompt_file = PROMPTS_DIR / 'analysis_prompt.md'
        try:
            if prompt_file.exists():
                content = prompt_file.read_text()
                logger.info("Loaded analysis prompt from analysis_prompt.md")
                return content
            else:
                logger.warning("analysis_prompt.md not found, using default")
                return self._get_default_analysis_prompt()
        except Exception as e:
            logger.warning(f"Could not load analysis_prompt.md: {e}. Using default.")
            return self._get_default_analysis_prompt()

    def _get_default_analysis_prompt(self) -> str:
        """
        Get default analysis prompt.

        Returns:
            Default analysis prompt string
        """
        return """Analyze the following data and provide structured output.

Data:
{data}

Respond with a JSON object containing your analysis."""

    def _load_system_prompt(self) -> str:
        """
        Load system prompt from prompts directory or return default.

        Returns:
            System prompt string
        """
        prompt_file = PROMPTS_DIR / 'system_prompt.md'
        try:
            if prompt_file.exists():
                content = prompt_file.read_text()
                logger.info("Loaded system prompt from system_prompt.md")
                return content
            else:
                logger.warning("system_prompt.md not found, using default")
                return self._get_default_system_prompt()
        except Exception as e:
            logger.warning(f"Could not load system_prompt.md: {e}. Using default.")
            return self._get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        """
        Get default system prompt.

        Returns:
            Default system prompt string
        """
        return """You are an expert data analyst. Analyze the provided data and extract structured insights.

Respond with ONLY valid JSON in the following format:
{
  "summary": "Brief summary of the data",
  "categories": ["category1", "category2"],
  "tags": ["tag1", "tag2", "tag3"],
  "key_points": ["point 1", "point 2"]
}

Do not include any text before or after the JSON."""

    def _call_ai(self, system_prompt: str, user_prompt: str) -> Dict:
        """
        Make API call to AI service.

        Args:
            system_prompt: System context/instructions
            user_prompt: User query/data

        Returns:
            Parsed JSON response from AI

        Raises:
            requests.exceptions.RequestException: If API call fails
            json.JSONDecodeError: If response is not valid JSON
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()

        result = response.json()
        content = result['choices'][0]['message']['content']

        # Strip markdown code fences if present
        content_clean = content.strip()
        if content_clean.startswith('```json'):
            content_clean = content_clean[7:]
        if content_clean.startswith('```'):
            content_clean = content_clean[3:]
        if content_clean.endswith('```'):
            content_clean = content_clean[:-3]
        content_clean = content_clean.strip()

        try:
            return json.loads(content_clean)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON")
            logger.error(f"Raw response (first 500 chars): {content[:500]}")
            logger.error(f"Cleaned response (first 500 chars): {content_clean[:500]}")
            logger.error(f"JSON error: {e}")
            raise

    def analyze_data(self, data_item: Any, item_id: Optional[Any] = None) -> Dict:
        """
        Analyze and structure relevant data item.
        If hook_manager is configured, runs pre_analysis hooks for data enrichment.

        Args:
            data_item: Data to analyze
            item_id: Optional item identifier for hooks (e.g., bill_id for LegiScan)

        Returns:
            Structured analysis as defined by system_prompt
        """
        # Convert data item to string
        if isinstance(data_item, dict):
            data_str = json.dumps(data_item, indent=2)
        else:
            data_str = str(data_item)

        # Execute pre-analysis hooks if configured
        if self.hook_manager:
            context = {'item_id': item_id} if item_id else {}
            data_str = self.hook_manager.execute_hooks('pre_analysis', data_str, context)

        # Format analysis prompt with data
        user_prompt = self.analysis_prompt.format(data=data_str)

        try:
            result = self._call_ai(self.system_prompt, user_prompt)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in analyze_data: {e}")
            logger.error(f"JSON error at line {e.lineno}, column {e.colno}")
            logger.error(f"Error details: {e.msg}")
            return {"error": f"JSON parsing failed: {e.msg}"}
        except Exception as e:
            logger.error(f"Error in analyze_data: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e)}
