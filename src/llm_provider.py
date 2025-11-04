"""
LLM Provider Abstraction Layer

Provides a unified interface for different LLM backends:
- Portkey (OpenAI via Portkey.ai gateway)
- Ollama (Local LLM server)
- Extensible for future providers (vLLM, llama.cpp, etc.)

This allows the application to switch between remote and local LLMs
via configuration without code changes.
"""

import os
import requests
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2000,
        timeout: int = 90,
        **kwargs
    ) -> str:
        """
        Generate chat completion from messages

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            **kwargs: Provider-specific additional parameters

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of this provider"""
        pass


class PortkeyProvider(LLMProvider):
    """
    Portkey/OpenAI provider (current default)

    Uses Portkey.ai as a gateway to OpenAI models.
    Requires PORTKEY_API_KEY environment variable.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.portkey.ai/v1",
        **kwargs
    ):
        """
        Initialize Portkey provider

        Args:
            api_key: Portkey API key (or reads from PORTKEY_API_KEY env var)
            model: Model identifier (e.g., "gpt-4o-mini")
            base_url: Portkey API base URL
            **kwargs: Additional provider-specific parameters
        """
        self.api_key = api_key or os.getenv('PORTKEY_API_KEY')
        if not self.api_key:
            raise ValueError("Portkey API key required (set PORTKEY_API_KEY env var or pass api_key)")

        self.model = model
        self.base_url = base_url.rstrip('/')
        self.kwargs = kwargs

        logger.info(f"Initialized PortkeyProvider with model: {model}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2000,
        timeout: int = 90,
        **kwargs
    ) -> str:
        """Call Portkey API for chat completion"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            **self.kwargs,
            **kwargs
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()

            result = response.json()
            return result['choices'][0]['message']['content']

        except requests.exceptions.Timeout:
            raise Exception(f"Portkey API request timed out after {timeout}s")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Portkey API request failed: {e}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Unexpected Portkey API response format: {e}")

    def get_provider_name(self) -> str:
        return f"portkey/{self.model}"


class OllamaProvider(LLMProvider):
    """
    Ollama provider for local LLMs

    Connects to Ollama server (typically http://localhost:11434)
    No API key required for local usage.

    Recommended models:
    - llama3.1:8b-instruct (fast, good quality)
    - llama3.1:70b-instruct (best quality, slower)
    - mistral:7b-instruct (efficient baseline)
    """

    def __init__(
        self,
        model: str = "llama3.1:8b-instruct",
        base_url: str = "http://localhost:11434/v1",
        **kwargs
    ):
        """
        Initialize Ollama provider

        Args:
            model: Ollama model identifier (e.g., "llama3.1:8b-instruct")
            base_url: Ollama server URL (default: http://localhost:11434/v1)
            **kwargs: Additional parameters to pass to Ollama
        """
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.kwargs = kwargs

        # Verify Ollama is accessible
        try:
            response = requests.get(f"{self.base_url.replace('/v1', '')}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info(f"Connected to Ollama server at {self.base_url}")
            logger.info(f"Initialized OllamaProvider with model: {model}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not connect to Ollama server: {e}")
            logger.warning("Make sure Ollama is running: `ollama serve`")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2000,
        timeout: int = 90,
        **kwargs
    ) -> str:
        """Call Ollama API for chat completion"""
        headers = {
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            # Ollama uses 'num_predict' instead of 'max_tokens'
            'options': {
                'num_predict': max_tokens,
                **self.kwargs.get('options', {})
            },
            **{k: v for k, v in kwargs.items() if k != 'options'}
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()

            result = response.json()
            return result['choices'][0]['message']['content']

        except requests.exceptions.Timeout:
            raise Exception(f"Ollama request timed out after {timeout}s")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama request failed: {e}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Unexpected Ollama response format: {e}")

    def get_provider_name(self) -> str:
        return f"ollama/{self.model}"


class LLMProviderFactory:
    """Factory for creating LLM providers from configuration"""

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> LLMProvider:
        """
        Create LLM provider from configuration dictionary

        Args:
            config: Configuration dict with structure:
                {
                    "llm": {
                        "provider": "portkey" | "ollama",
                        "model": "model-name",
                        "base_url": "...",  # optional
                        "api_key": "...",   # optional, for portkey
                        ... # provider-specific options
                    },
                    # Fallback to root level if llm section doesn't exist
                    "model": "model-name"
                }

        Returns:
            Configured LLM provider instance
        """
        # Check for new llm section first, fall back to root level
        llm_config = config.get('llm', {})

        # Determine provider type
        provider_type = llm_config.get('provider', 'portkey').lower()

        # Get model (prefer llm.model, fallback to root model)
        model = llm_config.get('model') or config.get('model', 'gpt-4o-mini')

        # Create provider based on type
        if provider_type == 'portkey':
            return PortkeyProvider(
                api_key=llm_config.get('api_key'),
                model=model,
                base_url=llm_config.get('base_url', 'https://api.portkey.ai/v1')
            )

        elif provider_type == 'ollama':
            return OllamaProvider(
                model=model,
                base_url=llm_config.get('base_url', 'http://localhost:11434/v1')
            )

        else:
            raise ValueError(f"Unknown LLM provider type: {provider_type}")

    @staticmethod
    def create_from_env(config: Optional[Dict[str, Any]] = None) -> LLMProvider:
        """
        Create LLM provider from environment variables + config

        Environment variables take precedence:
        - LLM_PROVIDER: "portkey" or "ollama"
        - LLM_MODEL: Model identifier
        - LLM_BASE_URL: Custom base URL
        - PORTKEY_API_KEY: For Portkey provider

        Args:
            config: Optional configuration dict (for defaults)

        Returns:
            Configured LLM provider instance
        """
        config = config or {}

        # Build effective config from env vars + config
        env_provider = os.getenv('LLM_PROVIDER')
        env_model = os.getenv('LLM_MODEL')
        env_base_url = os.getenv('LLM_BASE_URL')

        # Merge with config
        if env_provider or env_model or env_base_url:
            # Environment variables override config
            effective_config = {
                'llm': {
                    'provider': env_provider or config.get('llm', {}).get('provider', 'portkey'),
                    'model': env_model or config.get('llm', {}).get('model') or config.get('model', 'gpt-4o-mini'),
                    'base_url': env_base_url or config.get('llm', {}).get('base_url'),
                    **config.get('llm', {})
                }
            }
            logger.info(f"Using LLM provider from environment: {effective_config['llm']['provider']}")
        else:
            # Use config as-is
            effective_config = config

        return LLMProviderFactory.create_from_config(effective_config)


# Convenience function for backward compatibility
def create_llm_provider(
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
    base_url: str = "https://api.portkey.ai/v1",
    config: Optional[Dict[str, Any]] = None
) -> LLMProvider:
    """
    Create LLM provider with backward compatibility

    If config is provided and has llm section, uses factory.
    Otherwise creates PortkeyProvider with provided parameters.

    Args:
        api_key: API key for Portkey
        model: Model identifier
        base_url: API base URL
        config: Optional config dict

    Returns:
        LLM provider instance
    """
    if config and 'llm' in config:
        # New configuration style
        return LLMProviderFactory.create_from_config(config)
    else:
        # Legacy configuration - default to Portkey
        return PortkeyProvider(
            api_key=api_key,
            model=model,
            base_url=base_url
        )
