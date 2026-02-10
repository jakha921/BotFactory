"""
Abstract base class for AI service providers.

This module defines the interface that all AI providers (Gemini, OpenAI, Anthropic)
must implement, ensuring consistent API across different providers.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """
    Base exception for AI service errors.

    Use this exception when you need to raise an error from an AI provider
    but don't want to expose provider-specific details to users.
    """

    def __init__(
        self,
        message: str,
        provider: str = None,
        original_error: Exception = None,
        status_code: int = None
    ):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error
        self.status_code = status_code

    def __str__(self):
        if self.original_error:
            return f"{super().__str__()} (caused by: {type(self.original_error).__name__})"
        return super().__str__()


class BaseAIService(ABC):
    """
    Abstract base class for AI service providers.

    All AI providers (Gemini, OpenAI, Anthropic) must inherit from this class
    and implement the required methods.

    Attributes:
        provider: Name of the AI provider (e.g., 'gemini', 'openai', 'anthropic')
        client: The underlying provider client instance
    """

    def __init__(self, provider: str):
        """
        Initialize the AI service.

        Args:
            provider: Name of the AI provider
        """
        self.provider = provider
        self.client = None

    @abstractmethod
    def create_client(self) -> Any:
        """
        Create and configure the provider client.

        Returns:
            Configured client instance for the provider

        Raises:
            AIServiceError: If client creation fails
        """
        pass

    @abstractmethod
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
        Generate an AI response using the provider's API.

        Args:
            model_name: Model identifier (e.g., 'gemini-2.5-flash', 'gpt-4')
            prompt: User prompt to generate response for
            system_instruction: System instruction for the model
            history: Chat history as list of {role, content} dicts
            temperature: Temperature parameter (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict with keys:
                - 'text': Generated response text
                - 'input_tokens': Input tokens used (optional)
                - 'output_tokens': Output tokens used (optional)

        Raises:
            AIServiceError: If generation fails
        """
        pass

    @abstractmethod
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get information about a specific model.

        Args:
            model_id: Model identifier

        Returns:
            Dict with model information:
                - 'id': Model ID
                - 'name': Display name
                - 'max_tokens': Maximum context window
                - 'supports_vision': Whether model supports vision
                - 'supports_thinking': Whether model supports thinking
                - 'input_cost_per_1k': Cost per 1k input tokens
                - 'output_cost_per_1k': Cost per 1k output tokens
        """
        pass

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key format (basic check).

        Args:
            api_key: API key to validate

        Returns:
            True if key format is valid, False otherwise
        """
        if not api_key or len(api_key) < 20:
            return False
        return True

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_info: Dict[str, Any]
    ) -> float:
        """
        Estimate cost in USD for a request.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model_info: Model info dict from get_model_info()

        Returns:
            Estimated cost in USD
        """
        input_cost = (input_tokens / 1000) * model_info.get('input_cost_per_1k', 0)
        output_cost = (output_tokens / 1000) * model_info.get('output_cost_per_1k', 0)
        return input_cost + output_cost

    def format_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Format chat history for provider API.

        Args:
            history: List of {role, content} dicts

        Returns:
            Formatted history for the provider
        """
        return [
            {
                'role': 'assistant' if msg['role'] == 'model' else msg['role'],
                'content': msg['content']
            }
            for msg in (history or [])
        ]
