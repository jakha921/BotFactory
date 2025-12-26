"""
AI Settings API views.
"""
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AIModel, AIFeature, AIUsageLog
from .services import AIService, AILimitError, AIServiceError


class ImproveInstructionView(views.APIView):
    """POST /api/v1/ai/improve-instruction/ - Improve system instruction with AI."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        instruction = request.data.get('instruction', '')
        bot_id = request.data.get('bot_id')
        
        if not instruction:
            return Response({'error': 'instruction is required'}, status=400)
        
        try:
            ai_service = AIService(request.user)
            
            # Check limit first
            can_use, message = ai_service.check_limit('improve_instruction')
            if not can_use:
                return Response({
                    'error': 'Usage limit reached',
                    'message': message,
                    'limit_reached': True
                }, status=429)
            
            prompt = f"""Rewrite the following system instructions for an AI bot to be more professional, concise, and robust. Keep the core intent and behavior, but improve clarity and effectiveness:

{instruction}

Return ONLY the improved instruction text, nothing else."""
            
            result = ai_service.generate(
                prompt=prompt,
                feature_code='improve_instruction',
                system_instruction='You are an expert prompt engineer specializing in LLM system instructions.',
                temperature=0.7
            )
            
            return Response({
                'text': result.get('text', ''),
                'usage': {
                    'input_tokens': result.get('input_tokens', 0),
                    'output_tokens': result.get('output_tokens', 0)
                }
            })
            
        except AILimitError as e:
            return Response({
                'error': 'Usage limit reached',
                'message': str(e),
                'limit_reached': True
            }, status=429)
        except AIServiceError as e:
            return Response({'error': str(e)}, status=500)
        except Exception as e:
            return Response({'error': f'Failed to improve instruction: {str(e)}'}, status=500)


class GenerateContentView(views.APIView):
    """POST /api/v1/ai/generate-content/ - Generate knowledge base content with AI."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        title = request.data.get('title', '')
        bot_id = request.data.get('bot_id')
        
        if not title:
            return Response({'error': 'title is required'}, status=400)
        
        try:
            ai_service = AIService(request.user)
            
            # Check limit first
            can_use, message = ai_service.check_limit('generate_content')
            if not can_use:
                return Response({
                    'error': 'Usage limit reached',
                    'message': message,
                    'limit_reached': True
                }, status=429)
            
            prompt = f"""Generate comprehensive content about: {title}

Make it:
- Informative and well-structured
- Suitable for a knowledge base
- Practical and actionable
- 200-400 words

Return ONLY the content text, no title or formatting."""
            
            result = ai_service.generate(
                prompt=prompt,
                feature_code='generate_content',
                system_instruction='You are a helpful content generator that creates informative, structured text for knowledge bases.',
                temperature=0.7
            )
            
            return Response({
                'text': result.get('text', ''),
                'usage': {
                    'input_tokens': result.get('input_tokens', 0),
                    'output_tokens': result.get('output_tokens', 0)
                }
            })
            
        except AILimitError as e:
            return Response({
                'error': 'Usage limit reached',
                'message': str(e),
                'limit_reached': True
            }, status=429)
        except AIServiceError as e:
            return Response({'error': str(e)}, status=500)
        except Exception as e:
            return Response({'error': f'Failed to generate content: {str(e)}'}, status=500)


class AIUsageLimitView(views.APIView):
    """GET /api/v1/ai/usage-limits/ - Get current user's AI usage limits."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        features = AIFeature.objects.filter(is_active=True)
        
        limits = []
        for feature in features:
            can_use, message = AIUsageLog.can_use_feature(user, feature.code)
            
            try:
                limit = feature.limits.get(plan=user.plan)
                limits.append({
                    'feature': feature.code,
                    'name': feature.name,
                    'can_use': can_use,
                    'message': message,
                    'max_uses': limit.max_uses if not limit.is_unlimited else None,
                    'period': limit.period,
                    'is_unlimited': limit.is_unlimited
                })
            except:
                limits.append({
                    'feature': feature.code,
                    'name': feature.name,
                    'can_use': False,
                    'message': 'Not available for your plan'
                })
        
        return Response({'limits': limits, 'plan': user.plan})


class AIModelsListView(views.APIView):
    """GET /api/v1/ai/models/ - Get available AI models."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        models = AIModel.objects.filter(is_active=True).select_related('provider')
        
        result = []
        for model in models:
            result.append({
                'id': str(model.id),
                'provider': model.provider.name,
                'provider_display': model.provider.display_name,
                'name': model.name,
                'display_name': model.display_name,
                'model_id': model.model_id,
                'capability': model.capability,
                'supports_thinking': model.supports_thinking,
                'supports_vision': model.supports_vision,
                'is_default': model.is_default
            })
        
        return Response({'models': result})
