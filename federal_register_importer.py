#!/usr/bin/env python3
"""
Federal Register → Portkey AI → Drupal Importer
Proof of Concept
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / 'config.json'
SYSTEM_PROMPT_FILE = SCRIPT_DIR / 'prompts' / 'system_prompt.md'
ANALYSIS_PROMPT_FILE = SCRIPT_DIR / 'prompts' / 'analysis_prompt.md'


class FederalRegisterFetcher:
    """
    Fetches documents from the Federal Register API.
    
    Handles HTTP requests to the Federal Register API with proper headers
    and parameter formatting.
    """
    BASE_URL = "https://www.federalregister.gov/api/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FederalRegisterImporter/1.0',
            'Accept': 'application/json'
        })
    
    def fetch_documents(
        self,
        agencies: Optional[List[str]] = None,
        document_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        term: Optional[str] = None,
        per_page: int = 20
    ) -> List[Dict]:
        """
        Fetch documents from the Federal Register API.
        
        Args:
            agencies: List of agency slugs to filter by
            document_types: List of document types (e.g., 'RULE', 'PRORULE', 'NOTICE')
            start_date: Start date in YYYY-MM-DD format
            term: Search term to filter documents
            per_page: Number of results per page (max 1000)
            
        Returns:
            List of document dictionaries from the API response
        """
        params = {
            'per_page': per_page,
            'order': 'newest',
            'fields[]': [
                'title',
                'document_number',
                'publication_date',
                'agency_names',
                'type',
                'abstract',
                'html_url',
                'pdf_url',
                'body_html_url'
            ]
        }
        
        if agencies:
            params['conditions[agencies][]'] = agencies
        
        if document_types:
            params['conditions[type][]'] = document_types
        
        if start_date:
            params['conditions[publication_date][gte]'] = start_date
        
        if term:
            params['conditions[term]'] = term
        
        try:
            response = self.session.get(f"{self.BASE_URL}/documents.json", params=params)
            logger.debug(f"Request URL: {response.url}")
            response.raise_for_status()
            data = response.json()
            logger.info(f"Fetched {len(data.get('results', []))} documents from Federal Register (total count: {data.get('count', 0)})")
            return data.get('results', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from Federal Register: {e}")
            return []


class PortkeyAIProcessor:
    """
    Processes Federal Register documents using AI via Portkey.
    
    Sends documents to an LLM through Portkey's API to generate summaries,
    categories, tags, and extract key entities.
    """
    def __init__(
        self, 
        api_key: str, 
        base_url: str = "https://api.portkey.ai/v1",
        system_prompt: Optional[str] = None,
        analysis_prompt_template: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 800
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
        if system_prompt:
            self.system_prompt = system_prompt
        else:
            self.system_prompt = self._load_default_system_prompt()
        
        if analysis_prompt_template:
            self.analysis_prompt_template = analysis_prompt_template
        else:
            self.analysis_prompt_template = self._load_default_analysis_prompt()
    
    def _load_default_system_prompt(self) -> str:
        """
        Load system prompt from file or return default.
        
        Returns:
            System prompt string for AI context
        """
        try:
            if SYSTEM_PROMPT_FILE.exists():
                return SYSTEM_PROMPT_FILE.read_text()
            else:
                return "You are an expert at analyzing federal regulatory documents. Provide structured, accurate analysis."
        except Exception as e:
            logger.warning(f"Could not load system prompt: {e}. Using default.")
            return "You are an expert at analyzing federal regulatory documents. Provide structured, accurate analysis."
    
    def _load_default_analysis_prompt(self) -> str:
        """
        Load analysis prompt template from file or return built-in default.
        
        Returns:
            Analysis prompt template string with placeholders
        """
        try:
            if ANALYSIS_PROMPT_FILE.exists():
                return ANALYSIS_PROMPT_FILE.read_text()
            else:
                return self._get_builtin_prompt()
        except Exception as e:
            logger.warning(f"Could not load analysis prompt: {e}. Using default.")
            return self._get_builtin_prompt()
    
    def _get_builtin_prompt(self) -> str:
        """
        Get the built-in default analysis prompt template.
        
        Returns:
            Default prompt template with format placeholders
        """
        return """Analyze this Federal Register document and provide:

1. A concise 2-3 sentence executive summary
2. Up to 5 relevant categories (e.g., Healthcare, Environment, Finance, Labor, Technology)
3. Up to 10 specific tags/keywords
4. Key entities mentioned (agencies, organizations, locations)

Document Title: {title}
{doc_type_label}Content: {content}

Respond in JSON format:
{{
  "summary": "...",
  "categories": ["...", "..."],
  "tags": ["...", "..."],
  "key_entities": ["...", "..."]
}}"""
    
    def process_document(self, document: Dict) -> Dict:
        """
        Process a Federal Register document through AI analysis.
        
        Args:
            document: Document dictionary from Federal Register API
            
        Returns:
            Dictionary with AI-generated analysis:
            - summary: Executive summary
            - categories: List of relevant categories
            - tags: List of keywords/tags
            - key_entities: List of mentioned entities
        """
        title = document.get('title', '')
        abstract = document.get('abstract', '')
        doc_type = document.get('type', '')
        agencies = document.get('agency_names', [])
        
        # Fallback to title and metadata if abstract is missing
        if not abstract or abstract.strip() == '':
            logger.warning(f"No abstract for document {document.get('document_number')}, using title only")
            content = f"Title: {title}\nDocument Type: {doc_type}\nAgencies: {', '.join(agencies)}"
        else:
            content = abstract
        
        if doc_type:
            doc_type_label = f"Document Type: {doc_type}\n"
        else:
            doc_type_label = ""
        
        prompt = self.analysis_prompt_template.format(
            title=title,
            doc_type_label=doc_type_label,
            content=content
        )
        
        try:
            payload = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': self.temperature,
                'max_tokens': self.max_tokens
            }
            
            response = self.session.post(f"{self.base_url}/chat/completions", json=payload, timeout=30)
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
            
            parsed = json.loads(content_clean)
            logger.info(f"AI processed document {document.get('document_number')}")
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error for document {document.get('document_number')}: {e}")
            logger.debug(f"Response content: {content[:200] if 'content' in locals() else 'N/A'}")
            return {
                'summary': '',
                'categories': [],
                'tags': [],
                'key_entities': []
            }
        except Exception as e:
            logger.error(f"Error processing document {document.get('document_number')} with Portkey: {e}")
            return {
                'summary': '',
                'categories': [],
                'tags': [],
                'key_entities': []
            }


class DrupalImporter:
    """
    Imports processed Federal Register documents into Drupal via JSON:API.
    
    Handles authentication and content creation using Drupal's JSON:API endpoint.
    """
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.csrf_token = None
        self.authenticate()
    
    def authenticate(self):
        """
        Authenticate with Drupal and obtain CSRF token.
        
        Raises:
            requests.exceptions.RequestException: If authentication fails
        """
        try:
            login_url = f"{self.base_url}/user/login?_format=json"
            payload = {
                'name': self.username,
                'pass': self.password
            }
            
            response = self.session.post(login_url, json=payload)
            response.raise_for_status()
            
            token_url = f"{self.base_url}/session/token"
            token_response = self.session.get(token_url)
            token_response.raise_for_status()
            self.csrf_token = token_response.text
            
            self.session.headers.update({
                'Content-Type': 'application/vnd.api+json',
                'Accept': 'application/vnd.api+json',
                'X-CSRF-Token': self.csrf_token
            })
            
            logger.info("Successfully authenticated with Drupal")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def import_document(self, fed_reg_doc: Dict, ai_analysis: Dict) -> bool:
        """
        Import a Federal Register document with AI analysis into Drupal.
        
        Args:
            fed_reg_doc: Document from Federal Register API
            ai_analysis: AI-generated analysis results
            
        Returns:
            True if import successful, False otherwise
        """
        node_data = {
            'data': {
                'type': 'node--federal_register_document',
                'attributes': {
                    'title': fed_reg_doc.get('title', '')[:255],
                    'field_document_number': fed_reg_doc.get('document_number', ''),
                    'field_publication_date': fed_reg_doc.get('publication_date', ''),
                    'field_document_type': fed_reg_doc.get('type', ''),
                    'field_agencies': fed_reg_doc.get('agency_names', []),
                    'field_original_abstract': fed_reg_doc.get('abstract', ''),
                    'field_ai_summary': ai_analysis.get('summary', ''),
                    'field_html_url': fed_reg_doc.get('html_url', ''),
                    'field_pdf_url': fed_reg_doc.get('pdf_url', ''),
                    'field_ai_categories': ai_analysis.get('categories', []),
                    'field_ai_tags': ai_analysis.get('tags', []),
                    'field_key_entities': ai_analysis.get('key_entities', [])
                }
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/jsonapi/node/federal_register_document",
                json=node_data
            )
            
            if response.status_code == 201:
                logger.info(f"Successfully imported document {fed_reg_doc.get('document_number')}")
                return True
            else:
                logger.error(f"Failed to import document: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error importing to Drupal: {e}")
            return False


class FederalRegisterPipeline:
    """
    Orchestrates the complete Federal Register import pipeline.
    
    Coordinates fetching documents from Federal Register, processing with AI,
    and optionally importing to Drupal and/or saving to JSON file.
    """
    def __init__(
        self,
        portkey_api_key: str,
        drupal_url: Optional[str] = None,
        drupal_username: Optional[str] = None,
        drupal_password: Optional[str] = None,
        output_file: Optional[str] = None,
        ai_config: Optional[Dict] = None
    ):
        self.fetcher = FederalRegisterFetcher()
        
        ai_config = ai_config or {}
        self.ai_processor = PortkeyAIProcessor(
            api_key=portkey_api_key,
            model=ai_config.get('model', 'gpt-4o-mini'),
            temperature=ai_config.get('temperature', 0.3),
            max_tokens=ai_config.get('max_tokens', 800)
        )
        
        self.drupal_importer = None
        self.output_file = output_file
        
        if drupal_url and drupal_username and drupal_password:
            try:
                self.drupal_importer = DrupalImporter(drupal_url, drupal_username, drupal_password)
                logger.info("Drupal integration enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Drupal importer: {e}. Continuing without Drupal.")
        else:
            logger.info("Drupal credentials not provided - running in fetch + AI mode only")
        
        if output_file:
            logger.info(f"Results will be written to {output_file}")
    
    def run(
        self,
        agencies: Optional[List[str]] = None,
        document_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        term: Optional[str] = None,
        limit: Optional[int] = None
    ):
        """
        Execute the complete import pipeline.
        
        Args:
            agencies: Agency slugs to filter documents
            document_types: Document types to filter
            start_date: Start date for document search
            term: Search term filter
            limit: Maximum number of documents to process
        """
        logger.info("Starting Federal Register import pipeline")
        
        documents = self.fetcher.fetch_documents(
            agencies=agencies,
            document_types=document_types,
            start_date=start_date,
            term=term,
            per_page=limit or 20
        )
        
        if not documents:
            logger.warning("No documents fetched")
            return
        
        success_count = 0
        error_count = 0
        results = []
        
        for idx, doc in enumerate(documents, 1):
            logger.info(f"Processing document {idx}/{len(documents)}: {doc.get('document_number')}")
            
            ai_analysis = self.ai_processor.process_document(doc)
            
            # Rate limiting for API
            time.sleep(1)
            
            result_data = {
                'document_number': doc.get('document_number', ''),
                'title': doc.get('title', ''),
                'publication_date': doc.get('publication_date', ''),
                'document_type': doc.get('type', ''),
                'agencies': doc.get('agency_names', []),
                'original_abstract': doc.get('abstract', ''),
                'html_url': doc.get('html_url', ''),
                'pdf_url': doc.get('pdf_url', ''),
                'ai_summary': ai_analysis.get('summary', ''),
                'ai_categories': ai_analysis.get('categories', []),
                'ai_tags': ai_analysis.get('tags', []),
                'ai_key_entities': ai_analysis.get('key_entities', [])
            }
            
            results.append(result_data)
            
            logger.info(f"Document: {doc.get('title', '')[:80]}...")
            logger.info(f"AI Summary: {ai_analysis.get('summary', 'N/A')}")
            logger.info(f"Categories: {', '.join(ai_analysis.get('categories', []))}")
            logger.info(f"Tags: {', '.join(ai_analysis.get('tags', [])[:5])}")
            logger.info("-" * 80)
            
            if self.drupal_importer:
                if self.drupal_importer.import_document(doc, ai_analysis):
                    success_count += 1
                else:
                    error_count += 1
            else:
                success_count += 1
            
            # Brief pause between documents
            time.sleep(0.5)
        
        if self.output_file:
            try:
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'metadata': {
                            'timestamp': datetime.now().isoformat(),
                            'total_documents': len(results),
                            'drupal_enabled': self.drupal_importer is not None
                        },
                        'documents': results
                    }, f, indent=2, ensure_ascii=False)
                logger.info(f"Results written to {self.output_file}")
            except Exception as e:
                logger.error(f"Failed to write output file: {e}")
        
        if self.drupal_importer:
            logger.info(f"Pipeline complete: {success_count} successful, {error_count} errors")
        else:
            logger.info(f"Pipeline complete: {success_count} documents fetched and processed (Drupal import skipped)")


def load_config() -> Dict:
    """
    Load configuration from config.json file.
    
    Returns:
        Configuration dictionary or empty dict if file not found
    """
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {CONFIG_FILE}")
                return config
        else:
            logger.warning(f"Config file not found at {CONFIG_FILE}, using defaults")
            return {}
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        return {}


def main():
    """
    Main entry point for the Federal Register importer.
    
    Reads configuration from environment variables and config.json,
    then executes the import pipeline.
    """
    import os
    
    # Load credentials from environment
    PORTKEY_API_KEY = os.getenv('PORTKEY_API_KEY', '')
    DRUPAL_URL = os.getenv('DRUPAL_URL', '')
    DRUPAL_USER = os.getenv('DRUPAL_USER', '')
    DRUPAL_PASS = os.getenv('DRUPAL_PASS', '')
    
    if not PORTKEY_API_KEY:
        logger.error("PORTKEY_API_KEY environment variable not set")
        return
    
    config = load_config()
    fed_reg_config = config.get('federal_register', {})
    ai_config = config.get('ai', {})
    
    # Check if Drupal integration is fully configured
    drupal_enabled = bool(DRUPAL_URL and DRUPAL_USER and DRUPAL_PASS)
    if not drupal_enabled:
        logger.info("Drupal credentials not found in environment - running without Drupal import")
    
    output_filename = f"federal_register_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    pipeline = FederalRegisterPipeline(
        portkey_api_key=PORTKEY_API_KEY,
        drupal_url=DRUPAL_URL if drupal_enabled else None,
        drupal_username=DRUPAL_USER if drupal_enabled else None,
        drupal_password=DRUPAL_PASS if drupal_enabled else None,
        output_file=output_filename,
        ai_config=ai_config
    )
    
    # Get query parameters from config
    agencies = fed_reg_config.get('agencies') or None
    document_types = fed_reg_config.get('document_types') or None
    start_date = fed_reg_config.get('start_date')
    if not start_date:
        # Default to yesterday's documents
        start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    term = fed_reg_config.get('term')
    limit = fed_reg_config.get('limit', 10)
    
    logger.info(f"Federal Register query: agencies={agencies}, types={document_types}, start_date={start_date}, term={term}, limit={limit}")
    
    pipeline.run(
        agencies=agencies,
        document_types=document_types,
        start_date=start_date,
        term=term,
        limit=limit
    )


if __name__ == '__main__':
    main()
