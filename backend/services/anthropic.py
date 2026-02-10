"""
Anthropic (Claude) API integration service.

Supports Claude 4 Opus, Claude 3.5 Sonnet, Claude 3 Haiku.
"""
import os
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings

from .ai_base import BaseAIService, AIServiceError

logger = logging.getLogger(__name__)


# Model information for Anthropic models
ANTHROPIC_MODELS = {
    'claude-4-opus-20250114': {
        'id': 'claude-4-opus-20250114',
        'name': 'Claude 4 Opus',
        'max_tokens': 200000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.015,
        'output_cost_per_1k': 0.075,
    },
    'claude-3.5-sonnet-20241022': {
        'id': 'claude-3.5-sonnet-20241022',
        'name': 'Claude 3.5 Sonnet',
        'max_tokens': 200000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.003,
        'output_cost_per_1k': 0.015,
    },
    'claude-3.5-sonnet-20240620': {
        'id': 'claude-3.5-sonnet-20240620',
        'name': 'Claude 3.5 Sonnet',
        'max_tokens': 200000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.003,
        'output_cost_per_1k': 0.015,
    },
    'claude-3-haiku-20240307': {
        'id': 'claude-3-haiku-20240307',
        'name': 'Claude 3 Haiku',
        'max_tokens': 200000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.00025,
        'output_cost_per_1k': 0.00125,
    },
    'claude-3-opus-20240229': {
        'id': 'claude-3-opus-20240229',
        'name': 'Claude 3 Opus',
        'max_tokens': 200000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.015,
        'output_cost_per_1k': 0.075,
    },
}


class AnthropicService(BaseAIService):
    """Service for interacting with Anthropic Claude API."""

    def __init__(self, api_key: str = None):
        """
        Initialize Anthropic service with API key.

        Args:
            api_key: Anthropic API key (uses env var if not provided)
        """
        super().__init__('anthropic')
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')

        if not self.api_key:
            logger.error("ANTHROPIC_API_KEY is not configured")
            raise AIServiceError(
                "Anthropic service is not configured. Please add an API key.",
                provider='anthropic'
            )

        if not self.validate_api_key(self.api_key):
            logger.error("ANTHROPIC_API_KEY appears to be invalid")
            raise AIServiceError(
                "Anthropic API key is invalid. Please check your configuration.",
                provider='anthropic'
            )

        self.create_client()

    def create_client(self):
        """Create Anthropic client instance."""
        try:
            import anthropic
        except ImportError:
            raise AIServiceError(
                "Anthropic package is not installed. Run: pip install anthropic",
                provider='anthropic'
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info("Anthropic client initialized")

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
        Generate response using Anthropic Claude API.

        Args:
            model_name: Model to use (e.g., 'claude-3.5-sonnet', 'claude-4-opus')
            prompt: User prompt
            system_instruction: System message
            history: Chat history
            temperature: Sampling temperature (0-1)
            max_tokens: Max tokens to generate
            **kwargs: Additional parameters

        Returns:
            Dict with 'text', 'input_tokens', 'output_tokens'
        """
        try:
            # Prepare messages
            messages = []

            # Add history
            if history:
                formatted_history = self.format_history(history)
                messages.extend(formatted_history)

            # Add current prompt
            messages.append({
                "role": "user",
                "content": prompt
            })

            # Get model info for max_tokens
            model_info = self.get_model_info(model_name)
            default_max_tokens = model_info['max_tokens'] // 4  # Use 1/4 of context for output
            final_max_tokens = max_tokens or default_max_tokens

            # Ensure max_tokens doesn't exceed model limit
            if final_max_tokens > model_info['max_tokens']:
                final_max_tokens = model_info['max_tokens']

            # Generate response
            response = self.client.messages.create(
                model=model_name,
                system=system_instruction,
                messages=messages,
                temperature=temperature,
                max_tokens=final_max_tokens,
            )

            # Extract response
            text = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            logger.info(
                f"Anthropic generation successful: model={model_name}, "
                f"input_tokens={input_tokens}, output_tokens={output_tokens}"
            )

            return {
                'text': text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            }

        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}", exc_info=True)

            # Convert common errors to friendly messages
            error_str = str(e).lower()

            if 'quota' in error_str or 'rate' in error_str:
                raise AIServiceError(
                    "Anthropic service is temporarily busy. Please try again in a moment.",
                    provider='anthropic',
                    original_error=e
                )
            elif 'invalid' in error_str and 'key' in error_str:
                raise AIServiceError(
                    "Anthropic API key is invalid. Please check your configuration.",
                    provider='anthropic',
                    original_error=e
                )
            elif 'timeout' in error_str:
                raise AIServiceError(
                    "Anthropic service timed out. Please try a shorter message.",
                    provider='anthropic',
                    original_error=e
                )
            else:
                raise AIServiceError(
                    "Failed to generate response with Anthropic. Please try again.",
                    provider='anthropic',
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
        # Default to claude-3.5-sonnet if not found
        return ANTHROPIC_MODELS.get(
            model_id,
            ANTHROPIC_MODELS['claude-3.5-sonnet-20241022']
        )

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate Anthropic API key format.

        Anthropic keys start with 'sk-ant-' and are typically 40+ characters.

        Args:
            api_key: API key to validate

        Returns:
            True if format is valid
        """
        if not api_key:
            return False

        # Anthropic keys start with 'sk-ant-'
        if not api_key.startswith('sk-ant-'):
            return False

        # Anthropic keys are typically at least 40 characters
        return len(api_key) >= 40
