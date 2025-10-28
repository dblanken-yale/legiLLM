#!/usr/bin/env python3
"""
AI Filter Pass - First Pass Processing
Determines if data items are relevant for further analysis.
"""

import requests
import json
import logging
from typing import Any, Dict, Tuple
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
PROMPTS_DIR = PROJECT_ROOT / 'prompts'


class AIFilterPass:
    """
    First pass processor that filters data for relevance.
    Uses AI to determine if data items should proceed to analysis.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.portkey.ai/v1",
        filter_prompt: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 200,
        timeout: int = 120
    ):
        """
        Initialize filter pass processor.

        Args:
            api_key: Portkey API key
            base_url: API endpoint URL
            filter_prompt: Custom prompt for relevance filtering
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: API request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        self.filter_prompt = filter_prompt or self._load_filter_prompt()

        logger.info(f"Initialized AIFilterPass with model: {model}")

    def _load_filter_prompt(self) -> str:
        """
        Load filter prompt from prompts directory or return default.

        Returns:
            Filter prompt string
        """
        prompt_file = PROMPTS_DIR / 'filter_prompt.md'
        try:
            if prompt_file.exists():
                content = prompt_file.read_text()
                logger.info("Loaded filter prompt from filter_prompt.md")
                return content
            else:
                logger.warning("filter_prompt.md not found, using default")
                return self._get_default_filter_prompt()
        except Exception as e:
            logger.warning(f"Could not load filter_prompt.md: {e}. Using default.")
            return self._get_default_filter_prompt()

    def _get_default_filter_prompt(self) -> str:
        """
        Get default filter prompt.

        Returns:
            Default filter prompt string
        """
        return """You are a data relevance filter. Analyze the provided data and determine if it is relevant.

Respond with ONLY a JSON object in this exact format:
{
  "relevant": true/false,
  "reason": "brief explanation"
}"""

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

        return json.loads(content_clean)

    def filter_data(self, data_item: Any) -> Tuple[bool, str]:
        """
        Determine if data item is relevant for analysis.

        Args:
            data_item: Data to evaluate (string, dict, or other serializable type)

        Returns:
            Tuple of (is_relevant: bool, reason: str)
        """
        if isinstance(data_item, dict):
            data_str = json.dumps(data_item, indent=2)
        else:
            data_str = str(data_item)

        try:
            result = self._call_ai(self.filter_prompt, data_str)
            is_relevant = result.get('relevant', False)
            reason = result.get('reason', 'No reason provided')

            return is_relevant, reason
        except Exception as e:
            logger.error(f"Error in filter_data: {e}")
            return False, f"Error: {str(e)}"

    def filter_batch(self, file_content: str) -> Dict[str, Any]:
        """
        Filter multiple items from a file in a single API call.
        Passes entire file content to LLM for batch processing.

        Args:
            file_content: Raw file content (JSON or text) containing multiple items

        Returns:
            Dict with structure: {
                "results": [
                    {"relevant": bool, "reason": str, "bill_identifier": str},
                    ...
                ]
            }

        Raises:
            Exception: If API call fails or response is invalid
        """
        try:
            # Use higher max_tokens for batch processing
            original_max_tokens = self.max_tokens
            self.max_tokens = 8000  # Allow space for multiple bill results

            result = self._call_ai(self.filter_prompt, file_content)

            # Restore original max_tokens
            self.max_tokens = original_max_tokens

            # Validate response structure
            if 'results' not in result:
                logger.error("Response missing 'results' array")
                raise ValueError("Invalid response structure: missing 'results' array")

            if not isinstance(result['results'], list):
                logger.error("'results' is not an array")
                raise ValueError("Invalid response structure: 'results' must be an array")

            logger.info(f"Batch filter processed {len(result['results'])} items")
            return result

        except Exception as e:
            logger.error(f"Error in filter_batch: {e}")
            raise
