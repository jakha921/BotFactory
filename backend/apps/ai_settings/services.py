"""
AI Settings service - handles limit checking and AI generation with multiple providers.
"""
from typing import Optional, Dict, Any, Tuple
from django.conf import settings
from .models import AIProvider, AIModel, AIFeature, AIUsageLimit, AIUsageLog


class AILimitError(Exception):
    """Exception when usage limit is exceeded."""

    def __init__(self, message: str, limit_type: str = None, current_usage: int = None, max_limit: int = None):
        super().__init__(message)
        self.limit_type = limit_type
        self.current_usage = current_usage
        self.max_limit = max_limit


class AIServiceError(Exception):
    """Exception for AI service errors."""

    def __init__(self, message: str, provider: str = None, original_error: Exception = None):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error


class AIService:
    """Service for working with AI providers with usage limits."""

    def __init__(self, user):
        self.user = user

    def check_limit(self, feature_code: str) -> Tuple[bool, str]:
        """Check if user can use a feature."""
        return AIUsageLog.can_use_feature(self.user, feature_code)

    def log_usage(
        self,
        feature_code: str,
        model: AIModel,
        input_tokens: int = 0,
        output_tokens: int = 0,
        bot=None,
        success: bool = True,
        error_message: str = '',
        metadata: dict = None
    ):
        """Log AI usage."""
        feature = AIFeature.objects.get(code=feature_code)

        # Calculate cost
        cost = (
            (input_tokens / 1000 * float(model.input_cost_per_1k)) +
            (output_tokens / 1000 * float(model.output_cost_per_1k))
        )

        AIUsageLog.objects.create(
            user=self.user,
            feature=feature,
            model_used=model,
            bot=bot,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cents=cost * 100,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )

    def get_model(self, model_id: str = None, feature_code: str = None) -> AIModel:
        """Get model to use."""
        import logging
        logger = logging.getLogger(__name__)

        if model_id:
            try:
                return AIModel.objects.get(model_id=model_id, is_active=True)
            except AIModel.DoesNotExist:
                logger.warning(f"Model {model_id} not found or inactive, will use default")

        if feature_code:
            try:
                feature = AIFeature.objects.get(code=feature_code)
                if feature.default_model and feature.default_model.is_active:
                    return feature.default_model
            except AIFeature.DoesNotExist:
                logger.warning(f"Feature {feature_code} not found, will use global default model")

        # Default model
        return AIModel.objects.filter(is_active=True, is_default=True).first()

    async def generate(
        self,
        prompt: str,
        feature_code: str,
        system_instruction: str = None,
        model_id: str = None,
        history: list = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        bot=None
    ) -> Dict[str, Any]:
        """
        Generate AI response with limit checking using the AI factory.

        This method uses the new AI service abstraction layer to support
        multiple providers (Gemini, OpenAI, Anthropic) through a unified interface.
        """
        # 1. Check limit
        can_use, message = self.check_limit(feature_code)
        if not can_use:
            raise AILimitError(message)

        # 2. Get model
        model = self.get_model(model_id, feature_code)
        if not model:
            raise AIServiceError("No active AI model available")

        # 3. Get AI service from factory
        from services.ai_factory import get_ai_service, AIServiceFactory as Factory
        from services.ai_base import AIServiceError as BaseAIServiceError

        provider_name = model.provider.name

        try:
            # Get service instance (cached by factory)
            service = get_ai_service(provider_name, api_key=self._get_api_key(model))

            # Generate response using unified interface
            result = await service.generate_response(
                model_name=model.model_id,
                prompt=prompt,
                system_instruction=system_instruction or "You are a helpful AI assistant.",
                history=history or [],
                temperature=temperature,
                max_tokens=max_tokens
            )

            # 4. Log usage
            self.log_usage(
                feature_code=feature_code,
                model=model,
                input_tokens=result.get('input_tokens', 0),
                output_tokens=result.get('output_tokens', 0),
                bot=bot,
                success=True
            )

            return result

        except BaseAIServiceError as e:
            # Re-raise AI service errors
            raise AIServiceError(str(e), provider=provider_name, original_error=e)
        except Exception as e:
            # Log error
            self.log_usage(
                feature_code=feature_code,
                model=model,
                bot=bot,
                success=False,
                error_message=str(e)
            )
            raise

    def _get_api_key(self, model: AIModel) -> Optional[str]:
        """
        Get API key from provider configuration.

        Args:
            model: AIModel instance

        Returns:
            API key or None (uses env var if None)
        """
        provider = model.provider
        if hasattr(provider, 'decrypted_api_key') and provider.decrypted_api_key:
            return provider.decrypted_api_key

        # Fall back to environment variable based on provider name
        import os
        env_var_map = {
            'gemini': 'GEMINI_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
        }
        return os.environ.get(env_var_map.get(provider.name, ''))
