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
import time
import base64
import io
from typing import Any, Dict, Optional
from pathlib import Path
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
from docx import Document

from src.llm_provider import LLMProvider, create_llm_provider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_FILE = PROJECT_ROOT / 'config.json'
PROMPTS_DIR = PROJECT_ROOT / 'prompts'
LEGISCAN_API_BASE = "https://api.legiscan.com/"


class AIAnalysisPass:
    """
    Second pass processor that analyzes and structures relevant data.
    Uses AI to extract insights and format according to output schema.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.portkey.ai/v1",
        analysis_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 800,
        timeout: int = 90,
        legiscan_api_key: Optional[str] = None,
        api_delay: float = 0.0,
        storage_provider=None,
        provider: Optional[LLMProvider] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize analysis pass processor.

        Args:
            api_key: Portkey API key (optional if using provider)
            base_url: API endpoint URL (for backward compatibility)
            analysis_prompt: Custom prompt template for analysis (user message)
            system_prompt: System instructions for output format and behavior
            model: LLM model to use (for backward compatibility)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            legiscan_api_key: LegiScan API key for fetching bill text (optional)
            api_delay: Delay in seconds between LegiScan API calls (default: 0.0, no delay)
            storage_provider: StorageProvider instance for caching (optional)
            provider: LLMProvider instance (new preferred method)
            config: Configuration dict for creating provider
        """
        # Store parameters for LLM calls
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.legiscan_api_key = legiscan_api_key or os.getenv('LEGISCAN_API_KEY')
        self.api_delay = api_delay
        self.storage_provider = storage_provider

        # Use provided provider, or create one from legacy parameters
        if provider:
            self.provider = provider
        elif config:
            self.provider = create_llm_provider(config=config)
        else:
            # Legacy mode: create provider from individual parameters
            self.provider = create_llm_provider(
                api_key=api_key,
                model=model,
                base_url=base_url
            )

        self.analysis_prompt = analysis_prompt or self._load_analysis_prompt()
        self.system_prompt = system_prompt or self._load_system_prompt()

        logger.info(f"Initialized AIAnalysisPass with provider: {self.provider.get_provider_name()}")
        if self.legiscan_api_key:
            logger.info("LegiScan API integration enabled for bill text fetching")
        if self.storage_provider:
            logger.info(f"Using storage provider: {type(self.storage_provider).__name__}")

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
        Make API call to AI service via provider.

        Args:
            system_prompt: System context/instructions
            user_prompt: User query/data

        Returns:
            Parsed JSON response from AI

        Raises:
            Exception: If API call fails
            json.JSONDecodeError: If response is not valid JSON
        """
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        # Call provider
        content = self.provider.chat_completion(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout
        )

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
        Uses storage provider cache to avoid re-fetching the same bill.

        Args:
            bill_id: LegiScan bill ID

        Returns:
            Bill details dict or None if fetch fails
        """
        if not self.legiscan_api_key:
            logger.warning("LegiScan API key not set, cannot fetch bill text")
            return None

        # Check cache first (via storage provider if available)
        if self.storage_provider:
            cached_data = self.storage_provider.get_bill_from_cache(bill_id)
            if cached_data:
                logger.info(f"Loading bill {bill_id} from storage provider cache")
                self._last_fetch_was_cached = True
                return cached_data

        # Fetch from API if not in cache
        self._last_fetch_was_cached = False
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

                # Save to cache (via storage provider if available)
                if self.storage_provider:
                    try:
                        self.storage_provider.save_bill_to_cache(bill_id, bill_data)
                        logger.info(f"Cached bill {bill_id} via storage provider")
                    except Exception as e:
                        logger.warning(f"Could not save bill {bill_id} to cache: {e}")

                # Add delay after API call (only when not using cache)
                if self.api_delay > 0:
                    logger.info(f"Waiting {self.api_delay}s before next API call...")
                    time.sleep(self.api_delay)

                return bill_data
            else:
                logger.error(f"LegiScan API error: {result.get('alert', {}).get('message', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching bill {bill_id} from LegiScan: {e}")
            return None

    def _extract_text_from_pdf(self, base64_pdf: str) -> Optional[str]:
        """
        Extract text from base64-encoded PDF document.

        Args:
            base64_pdf: Base64-encoded PDF string

        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Decode base64 to bytes
            pdf_bytes = base64.b64decode(base64_pdf)

            # Create PDF reader from bytes
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PdfReader(pdf_file)

            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num}: {e}")
                    continue

            if text_parts:
                full_text = "\n\n".join(text_parts)
                logger.info(f"Successfully extracted {len(full_text)} characters from {len(pdf_reader.pages)} pages")
                return full_text
            else:
                logger.warning("No text could be extracted from PDF")
                return None

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return None

    def _extract_text_from_html(self, base64_html: str) -> Optional[str]:
        """
        Extract text from base64-encoded HTML document.

        Args:
            base64_html: Base64-encoded HTML string

        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Decode base64 to bytes, then to string
            html_bytes = base64.b64decode(base64_html)
            html_string = html_bytes.decode('utf-8', errors='ignore')

            # Parse HTML and extract text
            soup = BeautifulSoup(html_string, 'lxml')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator='\n', strip=True)

            # Clean up extra whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = '\n'.join(lines)

            logger.info(f"Successfully extracted {len(clean_text)} characters from HTML")
            return clean_text

        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return None

    def _extract_text_from_docx(self, base64_docx: str) -> Optional[str]:
        """
        Extract text from base64-encoded DOCX document.

        Args:
            base64_docx: Base64-encoded DOCX string

        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Decode base64 to bytes
            docx_bytes = base64.b64decode(base64_docx)

            # Create DOCX document from bytes
            docx_file = io.BytesIO(docx_bytes)
            doc = Document(docx_file)

            # Extract text from all paragraphs
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)

            full_text = '\n\n'.join(paragraphs)
            logger.info(f"Successfully extracted {len(full_text)} characters from DOCX ({len(paragraphs)} paragraphs)")
            return full_text

        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return None

    def _extract_text_from_plain_text(self, base64_text: str) -> Optional[str]:
        """
        Extract text from base64-encoded plain text document.

        Args:
            base64_text: Base64-encoded text string

        Returns:
            Decoded text or None if extraction fails
        """
        try:
            # Decode base64 to bytes, then to string
            text_bytes = base64.b64decode(base64_text)
            text_string = text_bytes.decode('utf-8', errors='ignore')

            logger.info(f"Successfully decoded {len(text_string)} characters from plain text")
            return text_string

        except Exception as e:
            logger.error(f"Error extracting text from plain text: {e}")
            return None

    def _extract_text_by_format(self, base64_content: str, mime_type: str) -> Optional[str]:
        """
        Extract text from base64-encoded document based on MIME type.

        Args:
            base64_content: Base64-encoded document content
            mime_type: MIME type of the document

        Returns:
            Extracted text or None if extraction fails
        """
        if not base64_content:
            return None

        # Normalize mime type
        mime_type = mime_type.lower() if mime_type else ''

        # Route to appropriate extractor
        if 'pdf' in mime_type or mime_type == 'application/pdf':
            logger.info("Extracting text from PDF format")
            return self._extract_text_from_pdf(base64_content)

        elif 'html' in mime_type or mime_type == 'text/html':
            logger.info("Extracting text from HTML format")
            return self._extract_text_from_html(base64_content)

        elif 'wordprocessingml' in mime_type or 'msword' in mime_type or mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            logger.info("Extracting text from DOCX format")
            return self._extract_text_from_docx(base64_content)

        elif 'plain' in mime_type or mime_type == 'text/plain':
            logger.info("Extracting text from plain text format")
            return self._extract_text_from_plain_text(base64_content)

        else:
            logger.warning(f"Unknown MIME type '{mime_type}', attempting plain text extraction")
            # Fallback: try plain text
            return self._extract_text_from_plain_text(base64_content)

    def _fetch_bill_text_from_legiscan(self, bill_id: int, doc_id: str, mime_type: str = 'application/pdf') -> Optional[str]:
        """
        Fetch actual bill text from LegiScan API using getBillText operation.
        Uses storage provider cache to avoid re-fetching the same document.

        Note: LegiScan returns bill text as base64-encoded documents in various formats
        (PDF, HTML, DOCX, plain text). This method decodes and extracts readable text
        based on the MIME type.

        Args:
            bill_id: LegiScan bill ID
            doc_id: LegiScan document ID
            mime_type: MIME type of the document (default: 'application/pdf')

        Returns:
            Extracted bill text or None if fetch/extraction fails
        """
        if not self.legiscan_api_key:
            logger.warning("LegiScan API key not set, cannot fetch bill text")
            return None

        # Check cache first (via storage provider if available)
        if self.storage_provider:
            cached_text = self.storage_provider.get_bill_text_from_cache(doc_id)
            if cached_text:
                logger.info(f"Loading bill text for doc_id {doc_id} from cache")
                return cached_text

        # Fetch from API if not in cache
        try:
            params = {
                'key': self.legiscan_api_key,
                'op': 'getBillText',
                'id': doc_id
            }

            logger.info(f"Fetching bill text for doc_id {doc_id} from LegiScan API...")
            response = requests.get(LEGISCAN_API_BASE, params=params, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get('status') == 'OK':
                text_data = result.get('text', {})
                base64_content = text_data.get('doc', '')

                logger.info(f"Successfully fetched bill text for doc_id {doc_id} from API")

                # Extract text from base64-encoded document based on MIME type
                bill_text = None
                if base64_content:
                    bill_text = self._extract_text_by_format(base64_content, mime_type)

                    if bill_text:
                        # Save extracted text to cache (via storage provider if available)
                        if self.storage_provider:
                            try:
                                self.storage_provider.save_bill_text_to_cache(doc_id, bill_text)
                                logger.info(f"Cached extracted bill text for doc_id {doc_id}")
                            except Exception as e:
                                logger.warning(f"Could not save bill text for doc_id {doc_id} to cache: {e}")
                    else:
                        logger.warning(f"Could not extract text from document (mime: {mime_type}) for doc_id {doc_id}")

                # Add delay after API call (only when not using cache)
                if self.api_delay > 0:
                    logger.info(f"Waiting {self.api_delay}s before next API call...")
                    time.sleep(self.api_delay)

                return bill_text
            else:
                logger.error(f"LegiScan API error: {result.get('alert', {}).get('message', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching bill text for doc_id {doc_id} from LegiScan: {e}")
            return None

    def _extract_bill_text(self, bill_data: Dict) -> str:
        """
        Extract readable text from LegiScan bill data.
        Fetches actual bill text via getBillText API if available.

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

        # Fetch and add actual bill text from documents
        if bill_data.get('texts'):
            texts = bill_data['texts']
            if isinstance(texts, list) and len(texts) > 0:
                # Get the most recent text version
                latest_text = texts[-1]
                doc_id = latest_text.get('doc_id')
                mime_type = latest_text.get('mime', 'application/pdf')  # Get MIME type, default to PDF

                if doc_id:
                    bill_id = bill_data.get('bill_id')
                    text_parts.append(f"\nBill Text (Version: {latest_text.get('type', 'Unknown')}, Format: {mime_type}):")

                    # Fetch actual bill text via getBillText API with MIME type
                    bill_text = self._fetch_bill_text_from_legiscan(bill_id, str(doc_id), mime_type)

                    if bill_text:
                        text_parts.append(bill_text)
                        logger.info(f"Added full bill text ({len(bill_text)} characters)")
                    else:
                        text_parts.append(f"[Full text unavailable for document ID: {doc_id}]")
                        logger.warning(f"Could not fetch bill text for doc_id {doc_id}")

        return "\n".join(text_parts)

    def analyze_data(self, data_item: Any, bill_id: Optional[int] = None) -> Dict:
        """
        Analyze and structure relevant data item.
        If bill_id is provided and LegiScan API key is available, fetches full bill text.

        Args:
            data_item: Data to analyze (bill metadata)
            bill_id: LegiScan bill ID for fetching full text (optional)

        Returns:
            Dictionary containing:
            - analysis results as defined by system_prompt
            - full_bill_text: the complete bill text that was analyzed (if fetched)
            - timing: dict with processing time breakdown
        """
        # Start overall timing
        start_time = time.time()

        # Initialize timing trackers
        timing = {
            'total_seconds': 0.0,
            'legiscan_api_seconds': 0.0,
            'text_extraction_seconds': 0.0,
            'ai_analysis_seconds': 0.0,
            'cache_hit': False
        }

        # Convert data item to string
        if isinstance(data_item, dict):
            data_str = json.dumps(data_item, indent=2)
        else:
            data_str = str(data_item)

        # Track the full bill text for inclusion in results
        full_bill_text = None

        # If bill_id provided and LegiScan API available, fetch full bill details
        if bill_id and self.legiscan_api_key:
            logger.info(f"Fetching full bill text for bill_id {bill_id}...")

            # Track LegiScan API time
            legiscan_start = time.time()
            bill_data = self._fetch_bill_from_legiscan(bill_id)
            legiscan_time = time.time() - legiscan_start

            if bill_data:
                # Track text extraction time
                extraction_start = time.time()
                bill_text = self._extract_bill_text(bill_data)
                extraction_time = time.time() - extraction_start

                timing['legiscan_api_seconds'] = round(legiscan_time, 2)
                timing['text_extraction_seconds'] = round(extraction_time, 2)

                # Check if data was from cache
                if self.storage_provider and hasattr(self, '_last_fetch_was_cached'):
                    timing['cache_hit'] = self._last_fetch_was_cached

                full_bill_text = bill_text  # Save for inclusion in results
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
            # Track AI analysis time
            ai_start = time.time()
            result = self._call_ai(self.system_prompt, user_prompt)
            ai_time = time.time() - ai_start
            timing['ai_analysis_seconds'] = round(ai_time, 2)

            # Calculate total time
            timing['total_seconds'] = round(time.time() - start_time, 2)

            # Add full bill text to result if it was fetched
            if full_bill_text:
                result['full_bill_text'] = full_bill_text

            # Add timing data to result
            result['timing'] = timing

            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in analyze_data: {e}")
            logger.error(f"JSON error at line {e.lineno}, column {e.colno}")
            logger.error(f"Error details: {e.msg}")
            timing['total_seconds'] = round(time.time() - start_time, 2)
            return {"error": f"JSON parsing failed: {e.msg}", "full_bill_text": full_bill_text, "timing": timing}
        except Exception as e:
            logger.error(f"Error in analyze_data: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            timing['total_seconds'] = round(time.time() - start_time, 2)
            return {"error": str(e), "full_bill_text": full_bill_text, "timing": timing}
