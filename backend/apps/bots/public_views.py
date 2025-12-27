"""
Public API views for external services.
Uses API key authentication instead of JWT.
"""
import logging
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.cache import cache
from django.utils import timezone

from apps.bots.models import Bot
from apps.chat.models import ChatSession, ChatMessage
from apps.telegram.models import TelegramUser
from services.gemini import get_gemini_service
from core.authentication import APIKeyAuthentication
from functools import wraps
from rest_framework.exceptions import Throttled

logger = logging.getLogger(__name__)


def rate_limit_api_key(key_prefix: str, limit: int = 100, period: int = 60):
    """
    Rate limiting decorator for API key-based requests.
    Uses API key ID instead of IP address.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(self, request, *args, **kwargs):
            # Get API key from authentication
            api_key_obj = getattr(request, 'auth', None)
            if not api_key_obj:
                # Fallback to IP if no API key
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR', 'unknown')
                cache_key = f"ratelimit:{key_prefix}:ip:{ip}"
            else:
                # Use API key ID for rate limiting
                cache_key = f"ratelimit:{key_prefix}:key:{api_key_obj.id}"
            
            current_count = cache.get(cache_key, 0)
            
            if current_count >= limit:
                logger.warning(f"Rate limit exceeded for {key_prefix} (key: {getattr(api_key_obj, 'id', 'unknown')})")
                raise Throttled(detail={
                    'message': f'Too many requests. Please try again in {period} seconds.',
                    'code': 'rate_limit_exceeded',
                    'retry_after': period
                })
            
            cache.set(cache_key, current_count + 1, period)
            
            return view_func(self, request, *args, **kwargs)
        return wrapped_view
    return decorator


class PublicChatView(views.APIView):
    """
    Public API endpoint for generating bot responses.
    Uses API key authentication via X-API-Key header.
    
    POST /api/v1/public/chat/
    Headers: X-API-Key: <bot_api_key>
    Body: {
        "message": "User message",
        "session_id": "optional-session-id"
    }
    """
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]  # Require valid API key authentication
    
    @rate_limit_api_key('public_api', limit=100, period=60)  # 100 requests per minute per API key
    def post(self, request):
        """
        Generate bot response using API key authentication.
        """
        message = request.data.get('message')
        session_id = request.data.get('session_id')
        
        if not message or not message.strip():
            return Response(
                {'error': {'message': 'message is required', 'code': 'validation_error'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Bot is available from authentication
        bot = request.user  # APIKeyAuthentication returns bot as user
        
        if not bot or bot.status != 'active':
            return Response(
                {'error': {'message': 'Bot is not active', 'code': 'bot_inactive'}},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get or create session
        chat_session = None
        if session_id:
            try:
                chat_session = ChatSession.objects.get(id=session_id, bot=bot)
            except ChatSession.DoesNotExist:
                # Create new session if provided ID doesn't exist
                chat_session = None
        
        if not chat_session:
            # Create a system user for public API sessions
            system_user, _ = TelegramUser.objects.get_or_create(
                telegram_id=0,  # System user
                bot=bot,
                defaults={
                    'first_name': 'API User',
                    'status': 'active'
                }
            )
            chat_session = ChatSession.objects.create(
                bot=bot,
                user=system_user
            )
        
        # Save user message
        ChatMessage.objects.create(
            session=chat_session,
            role='user',
            content=message
        )
        
        # Get chat history
        history_messages = ChatMessage.objects.filter(
            session=chat_session
        ).order_by('timestamp')[:10]
        
        history = [
            {'role': msg.role, 'content': msg.content}
            for msg in history_messages
        ]
        
        # Generate response
        try:
            gemini_service = get_gemini_service()
            result = gemini_service.generate_response(
                model_name=bot.model or 'gemini-2.5-flash',
                prompt=message,
                system_instruction=bot.system_instruction or 'You are a helpful AI assistant.',
                history=history,
                thinking_budget=bot.thinking_budget,
                temperature=bot.temperature or 0.7
            )
            
            # Save bot response
            ChatMessage.objects.create(
                session=chat_session,
                role='model',
                content=result.get('text', ''),
                attachments={'grounding_chunks': result.get('groundingChunks', [])}
            )
            
            return Response({
                'text': result.get('text', ''),
                'session_id': str(chat_session.id),
                'grounding_chunks': result.get('groundingChunks', [])
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Error generating response in public API: {str(e)}', exc_info=True)
            return Response(
                {'error': {'message': 'Failed to generate response', 'code': 'generation_error'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

