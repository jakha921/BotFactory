"""
OpenAI API integration service.

Supports GPT-4, GPT-4 Turbo, GPT-4o, and GPT-3.5-turbo.
"""
import os
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings

from .ai_base import BaseAIService, AIServiceError

logger = logging.getLogger(__name__)


# Model information for OpenAI models
OPENAI_MODELS = {
    'gpt-4o': {
        'id': 'gpt-4o',
        'name': 'GPT-4o',
        'max_tokens': 128000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.0025,
        'output_cost_per_1k': 0.01,
    },
    'gpt-4o-mini': {
        'id': 'gpt-4o-mini',
        'name': 'GPT-4o Mini',
        'max_tokens': 128000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.00015,
        'output_cost_per_1k': 0.0006,
    },
    'gpt-4-turbo': {
        'id': 'gpt-4-turbo',
        'name': 'GPT-4 Turbo',
        'max_tokens': 128000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.01,
        'output_cost_per_1k': 0.03,
    },
    'gpt-4': {
        'id': 'gpt-4',
        'name': 'GPT-4',
        'max_tokens': 8192,
        'supports_vision': False,
        'supports_thinking': False,
        'input_cost_per_1k': 0.03,
        'output_cost_per_1k': 0.06,
    },
    'gpt-3.5-turbo': {
        'id': 'gpt-3.5-turbo',
        'name': 'GPT-3.5 Turbo',
        'max_tokens': 16385,
        'supports_vision': False,
        'supports_thinking': False,
        'input_cost_per_1k': 0.0005,
        'output_cost_per_1k': 0.0015,
    },
}


class OpenAIService(BaseAIService):
    """Service for interacting with OpenAI API."""

    def __init__(self, api_key: str = None):
        """
        Initialize OpenAI service with API key.

        Args:
            api_key: OpenAI API key (uses env var if not provided)
        """
        super().__init__('openai')
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')

        if not self.api_key:
            logger.error("OPENAI_API_KEY is not configured")
            raise AIServiceError(
                "OpenAI service is not configured. Please add an API key.",
                provider='openai'
            )

        if not self.validate_api_key(self.api_key):
            logger.error("OPENAI_API_KEY appears to be invalid")
            raise AIServiceError(
                "OpenAI API key is invalid. Please check your configuration.",
                provider='openai'
            )

        self.create_client()

    def create_client(self):
        """Create OpenAI client instance."""
        try:
            import openai
        except ImportError:
            raise AIServiceError(
                "OpenAI package is not installed. Run: pip install openai",
                provider='openai'
            )

        self.client = openai.OpenAI(api_key=self.api_key)
        logger.info(f"OpenAI client initialized")

    async def generate_response(
        self,
        model_name: str,
        prompt: str,
        system_instruction: str = "You are a helpful AI assistant.",
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response using OpenAI API.

        Args:
            model_name: Model to use (e.g., 'gpt-4o', 'gpt-4-turbo')
            prompt: User prompt
            system_instruction: System message
            history: Chat history
            temperature: Sampling temperature (0-2)
            max_tokens: Max tokens to generate
            **kwargs: Additional parameters

        Returns:
            Dict with 'text', 'input_tokens', 'output_tokens'
        """
        try:
            # Prepare messages
            messages = []
            if system_instruction:
                messages.append({
                    "role": "system",
                    "content": system_instruction
                })

            # Add history
            if history:
                formatted_history = self.format_history(history)
                messages.extend(formatted_history)

            # Add current prompt
            messages.append({
                "role": "user",
                "content": prompt
            })

            # Prepare generation parameters
            generation_params = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                generation_params["max_tokens"] = max_tokens

            # Generate response
            response = self.client.chat.completions.create(**generation_params)

            # Extract response
            text = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            logger.info(
                f"OpenAI generation successful: model={model_name}, "
                f"input_tokens={input_tokens}, output_tokens={output_tokens}"
            )

            return {
                'text': text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            }

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)

            # Convert common errors to friendly messages
            error_str = str(e).lower()

            if 'quota' in error_str or 'rate' in error_str:
                raise AIServiceError(
                    "OpenAI service is temporarily busy. Please try again in a moment.",
                    provider='openai',
                    original_error=e
                )
            elif 'invalid' in error_str and 'key' in error_str:
                raise AIServiceError(
                    "OpenAI API key is invalid. Please check your configuration.",
                    provider='openai',
                    original_error=e
                )
            elif 'timeout' in error_str:
                raise AIServiceError(
                    "OpenAI service timed out. Please try a shorter message.",
                    provider='openai',
                    original_error=e
                )
            else:
                raise AIServiceError(
                    "Failed to generate response with OpenAI. Please try again.",
                    provider='openai',
                    original_error=e
                )

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get model information.

        Args:
            model_id: Model identifier

        Returns:
            Dict with model information
        """
        # Default to gpt-4o if not found
        return OPENAI_MODELS.get(model_id, OPENAI_MODELS['gpt-4o'])

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate OpenAI API key format.

        OpenAI keys typically start with 'sk-' and are 51 characters long.

        Args:
            api_key: API key to validate

        Returns:
            True if format is valid
        """
        if not api_key:
            return False

        # OpenAI keys start with 'sk-'
        if not api_key.startswith('sk-'):
            return False

        # Standard OpenAI keys are 51 characters (sk- + 48 chars)
        # Project-scoped keys are longer (sk-proj- + more chars)
        return len(api_key) >= 51
