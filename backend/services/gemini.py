"""
Google Gemini API integration service.

Supports Gemini 2.5 Flash, Gemini 3.0 Pro, and other Gemini models.
"""
import os
import re
import logging
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from django.conf import settings

from .ai_base import BaseAIService, AIServiceError

logger = logging.getLogger(__name__)


# Model information for Gemini models
GEMINI_MODELS = {
    'gemini-2.5-flash': {
        'id': 'gemini-2.5-flash',
        'name': 'Gemini 2.5 Flash',
        'max_tokens': 1000000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.000075,
        'output_cost_per_1k': 0.0003,
    },
    'gemini-2.5-flash-lite': {
        'id': 'gemini-2.5-flash-lite',
        'name': 'Gemini 2.5 Flash Lite',
        'max_tokens': 1000000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.0000375,
        'output_cost_per_1k': 0.00015,
    },
    'gemini-3-pro-preview': {
        'id': 'gemini-3-pro-preview',
        'name': 'Gemini 3.0 Pro (Thinking)',
        'max_tokens': 1000000,
        'supports_vision': True,
        'supports_thinking': True,
        'input_cost_per_1k': 0.000125,
        'output_cost_per_1k': 0.0005,
    },
    'gemini-1.5-pro': {
        'id': 'gemini-1.5-pro',
        'name': 'Gemini 1.5 Pro',
        'max_tokens': 2800000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.00175,
        'output_cost_per_1k': 0.0021,
    },
    'gemini-1.5-flash': {
        'id': 'gemini-1.5-flash',
        'name': 'Gemini 1.5 Flash',
        'max_tokens': 2800000,
        'supports_vision': True,
        'supports_thinking': False,
        'input_cost_per_1k': 0.000075,
        'output_cost_per_1k': 0.00015,
    },
}


# Backward compatibility alias
GeminiAPIError = AIServiceError


class GeminiService(BaseAIService):
    """Service for interacting with Google Gemini API."""

    def __init__(self, api_key: str = None):
        """
        Initialize Gemini service with API key.

        Args:
            api_key: Gemini API key (uses env var if not provided)
        """
        super().__init__('gemini')
        self.api_key = api_key or os.environ.get(
            'GEMINI_API_KEY'
        ) or getattr(settings, 'GEMINI_API_KEY', None)

        if not self.api_key:
            logger.error("GEMINI_API_KEY is not configured")
            raise AIServiceError(
                "AI service is not configured. Please contact administrator.",
                provider='gemini'
            )

        # Validate API key format (basic check)
        if not self.validate_api_key(self.api_key):
            logger.error("GEMINI_API_KEY appears to be invalid")
            raise AIServiceError(
                "AI service configuration error. Please contact administrator.",
                provider='gemini'
            )

        self.create_client()

    def create_client(self):
        """Create Gemini client instance."""
        genai.configure(api_key=self.api_key)
        self.client = genai
        logger.info("Gemini client initialized")

    async def generate_response(
        self,
        model_name: str,
        prompt: str,
        system_instruction: str = "You are a helpful AI assistant.",
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response using Gemini API.

        Args:
            model_name: Model name (e.g., 'gemini-2.5-flash')
            prompt: User prompt
            system_instruction: System instruction for the model
            history: Chat history as list of {role, content} dicts
            temperature: Temperature parameter (0-2)
            max_tokens: Maximum tokens to generate
            thinking_budget: Thinking budget in tokens (for thinking models)
            **kwargs: Additional parameters (including grounding)

        Returns:
            Dict with 'text', 'input_tokens', 'output_tokens', and optional 'groundingChunks'
        """
        try:
            # Create model instance
            model = self.client.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )

            # Prepare generation config
            generation_config = {
                'temperature': temperature,
            }

            # Apply thinking config if budget is provided
            # CRITICAL: maxOutputTokens must NOT be set when using thinkingConfig
            if thinking_budget:
                generation_config['thinkingConfig'] = {
                    'thinkingBudget': thinking_budget
                }
                # Ensure maxOutputTokens is undefined
                generation_config.pop('maxOutputTokens', None)
            elif max_tokens:
                generation_config['maxOutputTokens'] = max_tokens

            # Start chat if history exists
            if history and len(history) > 0:
                # Convert history format for Gemini
                chat_history = []
                for msg in history:
                    role = 'user' if msg['role'] == 'user' else 'model'
                    chat_history.append({
                        'role': role,
                        'parts': [msg['content']]
                    })

                chat = model.start_chat(history=chat_history)
                response = chat.send_message(
                    prompt,
                    generation_config=generation_config
                )
            else:
                # Simple generation without history
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )

            # Extract response text
            text = response.text if hasattr(response, 'text') else str(response)

            # Clean markdown formatting from response
            text = self._clean_response_text(text)

            # Extract grounding chunks if available
            grounding_chunks = self._extract_grounding_chunks(response)

            # Get token usage if available
            result = {
                'text': text,
                'groundingChunks': grounding_chunks
            }

            # Try to get token usage from response metadata
            if hasattr(response, 'usage_metadata'):
                result['input_tokens'] = response.usage_metadata.prompt_token_count or 0
                result['output_tokens'] = response.usage_metadata.candidates_token_count or 0

            return result

        except genai.types.BlockedPromptException as e:
            logger.warning(f"Gemini blocked prompt: {str(e)}")
            raise AIServiceError(
                "Your message was blocked by content filters. Please rephrase.",
                provider='gemini',
                original_error=e
            )
        except genai.types.StopCandidateException as e:
            logger.warning(f"Gemini stopped generation: {str(e)}")
            raise AIServiceError(
                "Response generation was interrupted. Please try again.",
                provider='gemini',
                original_error=e
            )
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}", exc_info=True)

            # Check for common error patterns and provide helpful messages
            error_str = str(e).lower()
            if 'quota' in error_str or 'rate' in error_str:
                raise AIServiceError(
                    "AI service is temporarily busy. Please try again in a moment.",
                    provider='gemini',
                    original_error=e
                )
            elif 'invalid' in error_str and 'key' in error_str:
                raise AIServiceError(
                    "AI service configuration error. Please contact administrator.",
                    provider='gemini',
                    original_error=e
                )
            elif 'timeout' in error_str:
                raise AIServiceError(
                    "AI service timed out. Please try a shorter message.",
                    provider='gemini',
                    original_error=e
                )
            else:
                raise AIServiceError(
                    "Failed to generate response. Please try again.",
                    provider='gemini',
                    original_error=e
                )

    def _clean_response_text(self, text: str) -> str:
        """Clean markdown formatting from response text."""
        # Remove bold/italic markers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **text**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # *text*
        text = re.sub(r'__([^_]+)__', r'\1', text)  # __text__
        text = re.sub(r'_([^_]+)_', r'\1', text)  # _text_
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)  # ```code```
        text = re.sub(r'`([^`]+)`', r'\1', text)  # `code`
        # Remove headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)  # # Header
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](url)
        # Clean up extra spaces
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to one
        text = text.strip()

        return text

    def _extract_grounding_chunks(self, response) -> List[Dict[str, Any]]:
        """Extract grounding chunks from Gemini response."""
        grounding_chunks = []
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata'):
                grounding_metadata = candidate.grounding_metadata
                if hasattr(grounding_metadata, 'grounding_chunks'):
                    # Convert protobuf RepeatedComposite to list of dicts
                    for chunk in grounding_metadata.grounding_chunks:
                        chunk_dict = {}
                        # Extract common fields from grounding chunk
                        if hasattr(chunk, 'web'):
                            chunk_dict['web'] = {
                                'uri': str(chunk.web.uri) if hasattr(chunk.web, 'uri') else None,
                                'title': str(chunk.web.title) if hasattr(chunk.web, 'title') else None,
                            }
                        if hasattr(chunk, 'retrieved_context'):
                            chunk_dict['retrieved_context'] = {
                                'uri': str(chunk.retrieved_context.uri) if hasattr(chunk.retrieved_context, 'uri') else None,
                                'title': str(chunk.retrieved_context.title) if hasattr(chunk.retrieved_context, 'title') else None,
                            }
                        if chunk_dict:  # Only add if we extracted something
                            grounding_chunks.append(chunk_dict)

        return grounding_chunks

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get model information.

        Args:
            model_id: Model identifier

        Returns:
            Dict with model information
        """
        # Default to gemini-2.5-flash if not found
        return GEMINI_MODELS.get(model_id, GEMINI_MODELS['gemini-2.5-flash'])

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate Gemini API key format.

        Gemini keys typically start with 'AI' and are at least 30 characters.

        Args:
            api_key: API key to validate

        Returns:
            True if format is valid
        """
        if not api_key:
            return False

        # Gemini keys start with 'AI'
        if not api_key.startswith('AI'):
            return False

        # Gemini keys are typically at least 30 characters
        return len(api_key) >= 30


# Global service instance for backward compatibility
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """
    Get or create Gemini service instance.

    This function provides backward compatibility with existing code.
    """
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
