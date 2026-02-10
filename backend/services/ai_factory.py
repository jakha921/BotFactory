"""
AI Service Factory - Provides appropriate AI service based on provider.

This module implements the factory pattern to create AI service instances
for different providers (Gemini, OpenAI, Anthropic).
"""
import logging
from typing import Literal, Optional, Dict, Any

from .ai_base import BaseAIService, AIServiceError
from .gemini import GeminiService, GEMINI_MODELS
from .openai import OpenAIService, OPENAI_MODELS
from .anthropic import AnthropicService, ANTHROPIC_MODELS

logger = logging.getLogger(__name__)


# Supported AI providers
Provider = Literal['gemini', 'openai', 'anthropic']

# Service classes for each provider
_SERVICE_CLASSES = {
    'gemini': GeminiService,
    'openai': OpenAIService,
    'anthropic': AnthropicService,
}

# Model information for all providers
_ALL_MODELS: Dict[Provider, Dict[str, Dict[str, Any]]] = {
    'gemini': GEMINI_MODELS,
    'openai': OPENAI_MODELS,
    'anthropic': ANTHROPIC_MODELS,
}


class AIServiceFactory:
    """
    Factory for creating AI service instances.

    This factory manages the creation of AI service instances based on
    the provider name, ensuring consistent API across different providers.
    """

    # Cache for service instances (one instance per provider)
    _service_cache: Dict[Provider, Optional[BaseAIService]] = {
        'gemini': None,
        'openai': None,
        'anthropic': None,
    }

    @classmethod
    def get_service(cls, provider: Provider, api_key: str = None) -> BaseAIService:
        """
        Get or create an AI service instance for the specified provider.

        This method implements caching to avoid creating multiple instances
        of the same service.

        Args:
            provider: Name of the AI provider ('gemini', 'openai', 'anthropic')
            api_key: Optional API key (uses env var if not provided)

        Returns:
            Configured AI service instance

        Raises:
            AIServiceError: If provider is unknown or service creation fails

        Examples:
            >>> factory = AIServiceFactory()
            >>> gemini_service = factory.get_service('gemini')
            >>> openai_service = factory.get_service('openai', api_key='sk-...')
        """
        if provider not in _SERVICE_CLASSES:
            raise AIServiceError(
                f"Unknown AI provider: {provider}. "
                f"Supported providers: {', '.join(_SERVICE_CLASSES.keys())}",
                provider=provider
            )

        # Return cached instance if available
        if cls._service_cache[provider] is not None:
            return cls._service_cache[provider]

        # Create new service instance
        try:
            service_class = _SERVICE_CLASSES[provider]
            service = service_class(api_key=api_key)
            cls._service_cache[provider] = service
            logger.info(f"Created AI service instance for provider: {provider}")
            return service
        except AIServiceError:
            # Re-raise AIServiceError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to create AI service for {provider}: {e}", exc_info=True)
            raise AIServiceError(
                f"Failed to initialize {provider} service. Please check your API key configuration.",
                provider=provider,
                original_error=e
            )

    @classmethod
    def clear_cache(cls, provider: Optional[Provider] = None):
        """
        Clear cached service instances.

        This is useful for testing or when API keys need to be refreshed.

        Args:
            provider: Specific provider to clear (clears all if None)
        """
        if provider:
            cls._service_cache[provider] = None
            logger.info(f"Cleared AI service cache for provider: {provider}")
        else:
            for key in cls._service_cache:
                cls._service_cache[key] = None
            logger.info("Cleared all AI service caches")

    @classmethod
    def get_available_models(cls, provider: Optional[Provider] = None) -> Dict[str, Any]:
        """
        Get available models for one or all providers.

        Args:
            provider: Specific provider (returns all if None)

        Returns:
            Dict mapping model_id to model information

        Examples:
            >>> AIServiceFactory.get_available_models('gemini')
            {'gemini-2.5-flash': {...}, 'gemini-3-pro-preview': {...}}
        """
        if provider:
            if provider not in _ALL_MODELS:
                raise AIServiceError(
                    f"Unknown provider: {provider}",
                    provider=provider
                )
            return _ALL_MODELS[provider]
        return _ALL_MODELS

    @classmethod
    def get_model_info(cls, model_id: str, provider: Provider) -> Dict[str, Any]:
        """
        Get information about a specific model.

        Args:
            model_id: Model identifier
            provider: Provider name

        Returns:
            Dict with model information

        Examples:
            >>> AIServiceFactory.get_model_info('gpt-4o', 'openai')
            {'id': 'gpt-4o', 'name': 'GPT-4o', ...}
        """
        models = cls.get_available_models(provider)
        return models.get(model_id, {})

    @classmethod
    def validate_provider(cls, provider: str) -> bool:
        """
        Check if a provider is supported.

        Args:
            provider: Provider name to validate

        Returns:
            True if provider is supported
        """
        return provider in _SERVICE_CLASSES


# Convenience function for direct usage
def get_ai_service(provider: Provider, api_key: str = None) -> BaseAIService:
    """
    Get an AI service instance for the specified provider.

    This is a convenience function that delegates to AIServiceFactory.get_service().

    Args:
        provider: Name of the AI provider ('gemini', 'openai', 'anthropic')
        api_key: Optional API key (uses env var if not provided)

    Returns:
        Configured AI service instance

    Examples:
        >>> service = get_ai_service('gemini')
        >>> result = await service.generate_response(...)
    """
    return AIServiceFactory.get_service(provider, api_key)


def get_available_models(provider: Optional[Provider] = None) -> Dict[str, Any]:
    """
    Get available models for one or all providers.

    Args:
        provider: Specific provider (returns all if None)

    Returns:
        Dict mapping model_id to model information
    """
    return AIServiceFactory.get_available_models(provider)


def get_model_info(model_id: str, provider: Provider) -> Dict[str, Any]:
    """
    Get information about a specific model.

    Args:
        model_id: Model identifier
        provider: Provider name

    Returns:
        Dict with model information
    """
    return AIServiceFactory.get_model_info(model_id, provider)
