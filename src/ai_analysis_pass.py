#!/usr/bin/env python3
"""
AI Analysis Pass - Second Pass Processing
Analyzes and structures relevant data items.
Fetches full bill text from LegiScan API before analysis.
"""

import requests
import json
import logging
import os
from typing import Any, Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_FILE = PROJECT_ROOT / 'config.json'
PROMPTS_DIR = PROJECT_ROOT / 'prompts'
LEGISCAN_API_BASE = "https://api.legiscan.com/"
LEGISCAN_CACHE_DIR = PROJECT_ROOT / 'data' / 'cache' / 'legiscan_cache'


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
        legiscan_api_key: Optional[str] = None
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
            legiscan_api_key: LegiScan API key for fetching bill text (optional)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.legiscan_api_key = legiscan_api_key or os.getenv('LEGISCAN_API_KEY')

        self.analysis_prompt = analysis_prompt or self._load_analysis_prompt()
        self.system_prompt = system_prompt or self._load_system_prompt()

        # Create cache directory if it doesn't exist
        if self.legiscan_api_key:
            LEGISCAN_CACHE_DIR.mkdir(exist_ok=True)
            logger.info(f"LegiScan cache directory: {LEGISCAN_CACHE_DIR}")

        logger.info(f"Initialized AIAnalysisPass with model: {model}")
        if self.legiscan_api_key:
            logger.info("LegiScan API integration enabled for bill text fetching")

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
            timeout=90
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

    def _fetch_bill_from_legiscan(self, bill_id: int) -> Optional[Dict]:
        """
        Fetch full bill details from LegiScan API using getBill operation.
        Uses local file cache to avoid re-fetching the same bill.

        Args:
            bill_id: LegiScan bill ID

        Returns:
            Bill details dict or None if fetch fails
        """
        if not self.legiscan_api_key:
            logger.warning("LegiScan API key not set, cannot fetch bill text")
            return None

        # Check cache first
        cache_file = LEGISCAN_CACHE_DIR / f"bill_{bill_id}.json"
        if cache_file.exists():
            logger.info(f"Loading bill {bill_id} from cache: {cache_file}")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                logger.info(f"Successfully loaded bill {bill_id} from cache")
                return cached_data
            except Exception as e:
                logger.warning(f"Error reading cache file for bill {bill_id}: {e}")
                logger.info("Falling back to API fetch...")

        # Fetch from API if not in cache
        try:
            params = {
                'key': self.legiscan_api_key,
                'op': 'getBill',
                'id': bill_id
            }

            logger.info(f"Fetching bill {bill_id} from LegiScan API...")
            response = requests.get(LEGISCAN_API_BASE, params=params, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get('status') == 'OK':
                bill_data = result.get('bill')
                logger.info(f"Successfully fetched bill {bill_id} from API")

                # Save to cache
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(bill_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"Cached bill {bill_id} to: {cache_file}")
                except Exception as e:
                    logger.warning(f"Could not save bill {bill_id} to cache: {e}")

                return bill_data
            else:
                logger.error(f"LegiScan API error: {result.get('alert', {}).get('message', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching bill {bill_id} from LegiScan: {e}")
            return None

    def _extract_bill_text(self, bill_data: Dict) -> str:
        """
        Extract readable text from LegiScan bill data.

        Args:
            bill_data: Bill data from LegiScan API

        Returns:
            Formatted bill text with title, description, and full text
        """
        text_parts = []

        # Add bill metadata
        if bill_data.get('bill_number'):
            text_parts.append(f"Bill Number: {bill_data['bill_number']}")

        if bill_data.get('title'):
            text_parts.append(f"Title: {bill_data['title']}")

        if bill_data.get('description'):
            text_parts.append(f"Description: {bill_data['description']}")

        # Add status info
        if bill_data.get('status'):
            text_parts.append(f"Status: {bill_data['status']}")

        if bill_data.get('status_date'):
            text_parts.append(f"Status Date: {bill_data['status_date']}")

        # Add bill text from documents
        if bill_data.get('texts'):
            texts = bill_data['texts']
            if isinstance(texts, list) and len(texts) > 0:
                # Get the most recent text version
                latest_text = texts[-1]
                if latest_text.get('doc_id'):
                    text_parts.append(f"\nBill Text (Version: {latest_text.get('type', 'Unknown')}):")
                    # Note: LegiScan API's getBill includes doc_id but actual text content
                    # requires a separate getBillText API call or doc download
                    # For now, we'll note the document is available
                    text_parts.append(f"[Full text document ID: {latest_text['doc_id']}]")

        # Add sponsors
        if bill_data.get('sponsors'):
            sponsors = bill_data['sponsors']
            if isinstance(sponsors, list):
                sponsor_names = [s.get('name', 'Unknown') for s in sponsors[:3]]  # First 3 sponsors
                text_parts.append(f"Sponsors: {', '.join(sponsor_names)}")

        # Add subjects/tags
        if bill_data.get('subjects'):
            subjects = bill_data['subjects']
            if isinstance(subjects, list):
                subject_names = [s.get('subject_name', '') for s in subjects]
                text_parts.append(f"Subjects: {', '.join(subject_names)}")

        return "\n".join(text_parts)

    def analyze_data(self, data_item: Any, bill_id: Optional[int] = None) -> Dict:
        """
        Analyze and structure relevant data item.
        If bill_id is provided and LegiScan API key is available, fetches full bill text.

        Args:
            data_item: Data to analyze (bill metadata)
            bill_id: LegiScan bill ID for fetching full text (optional)

        Returns:
            Structured analysis as defined by system_prompt
        """
        # Convert data item to string
        if isinstance(data_item, dict):
            data_str = json.dumps(data_item, indent=2)
        else:
            data_str = str(data_item)

        # If bill_id provided and LegiScan API available, fetch full bill details
        if bill_id and self.legiscan_api_key:
            logger.info(f"Fetching full bill text for bill_id {bill_id}...")
            bill_data = self._fetch_bill_from_legiscan(bill_id)

            if bill_data:
                # Extract and append bill text to data
                bill_text = self._extract_bill_text(bill_data)
                data_str += f"\n\n## Full Bill Details from LegiScan API:\n\n{bill_text}"
                logger.info("Bill text successfully added to analysis")
                logger.info("=" * 80)
                logger.info("FETCHED BILL CONTENT:")
                logger.info("=" * 80)
                logger.info(bill_text)
                logger.info("=" * 80)
            else:
                logger.warning(f"Could not fetch bill text for bill_id {bill_id}, analyzing with metadata only")
        elif bill_id and not self.legiscan_api_key:
            logger.warning("LegiScan API key not configured, analyzing with metadata only")

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
