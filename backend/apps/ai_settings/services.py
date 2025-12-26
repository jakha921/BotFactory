"""
AI Settings service - handles limit checking and AI generation with multiple providers.
"""
from typing import Optional, Dict, Any, Tuple
from django.conf import settings
from .models import AIProvider, AIModel, AIFeature, AIUsageLimit, AIUsageLog


class AILimitError(Exception):
    """Exception when usage limit is exceeded."""
    pass


class AIServiceError(Exception):
    """Exception when AI service fails."""
    pass


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
        if model_id:
            try:
                return AIModel.objects.get(model_id=model_id, is_active=True)
            except AIModel.DoesNotExist:
                pass
        
        if feature_code:
            try:
                feature = AIFeature.objects.get(code=feature_code)
                if feature.default_model and feature.default_model.is_active:
                    return feature.default_model
            except AIFeature.DoesNotExist:
                pass
        
        # Default model
        return AIModel.objects.filter(is_active=True, is_default=True).first()
    
    def generate(
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
        """Generate AI response with limit checking."""
        
        # 1. Check limit
        can_use, message = self.check_limit(feature_code)
        if not can_use:
            raise AILimitError(message)
        
        # 2. Get model
        model = self.get_model(model_id, feature_code)
        if not model:
            raise AIServiceError("No active AI model available")
        
        # 3. Call provider
        provider = model.provider
        
        try:
            if provider.name == 'gemini':
                result = self._call_gemini(model, prompt, system_instruction, history, temperature)
            elif provider.name == 'openai':
                result = self._call_openai(model, prompt, system_instruction, history, temperature)
            elif provider.name == 'anthropic':
                result = self._call_anthropic(model, prompt, system_instruction, history, temperature)
            else:
                raise AIServiceError(f"Unsupported provider: {provider.name}")
            
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
    
    def _call_gemini(self, model, prompt, system_instruction, history, temperature):
        """Call Gemini API."""
        from services.gemini import GeminiService
        
        service = GeminiService()
        response = service.generate_response(
            model_name=model.model_id,
            prompt=prompt,
            system_instruction=system_instruction or "You are a helpful AI assistant.",
            history=history or [],
            temperature=temperature
        )
        
        return {
            'text': response.get('text', ''),
            'input_tokens': response.get('usage', {}).get('prompt_tokens', 0),
            'output_tokens': response.get('usage', {}).get('completion_tokens', 0)
        }
    
    def _call_openai(self, model, prompt, system_instruction, history, temperature):
        """Call OpenAI API."""
        try:
            import openai
        except ImportError:
            raise AIServiceError("OpenAI package not installed. Run: pip install openai")
        
        provider = model.provider
        client = openai.OpenAI(api_key=provider.decrypted_api_key)
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        
        if history:
            for h in history:
                role = "assistant" if h['role'] == 'model' else h['role']
                messages.append({"role": role, "content": h['content']})
        
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model.model_id,
            messages=messages,
            temperature=temperature
        )
        
        return {
            'text': response.choices[0].message.content,
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens
        }
    
    def _call_anthropic(self, model, prompt, system_instruction, history, temperature):
        """Call Anthropic API."""
        try:
            import anthropic
        except ImportError:
            raise AIServiceError("Anthropic package not installed. Run: pip install anthropic")
        
        provider = model.provider
        client = anthropic.Anthropic(api_key=provider.decrypted_api_key)
        
        messages = []
        if history:
            for h in history:
                role = "assistant" if h['role'] == 'model' else h['role']
                messages.append({"role": role, "content": h['content']})
        
        messages.append({"role": "user", "content": prompt})
        
        response = client.messages.create(
            model=model.model_id,
            max_tokens=model.max_tokens,
            system=system_instruction or "You are a helpful AI assistant.",
            messages=messages
        )
        
        return {
            'text': response.content[0].text,
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens
        }
