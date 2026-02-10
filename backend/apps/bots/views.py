"""
Views for bots app.
BotViewSet for CRUD operations on bots.
"""
import logging
import requests
import secrets
from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.bots.models import Bot
from apps.bots.serializers import (
    BotSerializer,
    BotCreateSerializer,
    BotUpdateSerializer,
    UIConfigSerializer,
    BotAPIKeySerializer,
    BotAPIKeyCreateSerializer,
)
from apps.bots.models import BotAPIKey
from core.permissions import IsOwnerOrReadOnly
from core.mixins import OwnerFilterMixin, OwnerCreateMixin


class BotViewSet(OwnerFilterMixin, OwnerCreateMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing bots.
    
    list: GET /api/v1/bots/ - List all bots for the current user
    create: POST /api/v1/bots/ - Create a new bot
    retrieve: GET /api/v1/bots/{id}/ - Get bot details
    update: PUT /api/v1/bots/{id}/ - Full update
    partial_update: PATCH /api/v1/bots/{id}/ - Partial update
    destroy: DELETE /api/v1/bots/{id}/ - Delete bot
    """
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """
        Filter bots by current user with optimization.

        Uses select_related to avoid N+1 queries when accessing
        owner.email in BotSerializer.
        """
        return Bot.objects.filter(owner=self.request.user).select_related('owner')
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return BotCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BotUpdateSerializer
        return BotSerializer
    
    def perform_create(self, serializer):
        """Automatically set owner when creating."""
        serializer.save(owner=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a bot and return in frontend format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        bot = serializer.instance
        return Response(
            BotSerializer(bot).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Custom action to activate a bot."""
        bot = self.get_object()
        if bot.status == 'draft':
            bot.status = 'active'
            bot.save()
            return Response({
                'status': 'activated',
                'bot': BotSerializer(bot).data
            })
        return Response(
            {'error': 'Bot is not in draft status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get', 'post'], url_path='ui-config')
    def ui_config(self, request, pk=None):
        """
        Get or update UI configuration for a bot.
        
        GET /api/v1/bots/{id}/ui-config/ - Get UI configuration
        POST /api/v1/bots/{id}/ui-config/ - Update UI configuration
        
        POST Body:
        {
            "inline_keyboards": {...},
            "forms": {...},
            "welcome_message": "...",
            "help_message": "...",
            "default_inline_keyboard": [...]
        }
        """
        bot = self.get_object()
        
        if request.method == 'GET':
            # Return current UI configuration
            config = {
                'inline_keyboards': bot.ui_config.get('inline_keyboards', {}) if bot.ui_config else {},
                'forms': bot.ui_config.get('forms', {}) if bot.ui_config else {},
                'welcome_message': bot.welcome_message or '',
                'help_message': bot.help_message or '',
                'default_inline_keyboard': bot.default_inline_keyboard if bot.default_inline_keyboard else [],
            }
            return Response(config)
        
        elif request.method == 'POST':
            # Update UI configuration
            serializer = UIConfigSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            validated_data = serializer.validated_data
            
            # Update bot fields
            if 'welcome_message' in validated_data:
                bot.welcome_message = validated_data['welcome_message']
            if 'help_message' in validated_data:
                bot.help_message = validated_data['help_message']
            if 'default_inline_keyboard' in validated_data:
                bot.default_inline_keyboard = validated_data['default_inline_keyboard']
            
            # Update ui_config
            current_config = bot.ui_config if bot.ui_config else {}
            if 'inline_keyboards' in validated_data:
                if 'inline_keyboards' not in current_config:
                    current_config['inline_keyboards'] = {}
                current_config['inline_keyboards'].update(validated_data['inline_keyboards'] or {})
            if 'forms' in validated_data:
                if 'forms' not in current_config:
                    current_config['forms'] = {}
                current_config['forms'].update(validated_data['forms'] or {})
            
            bot.ui_config = current_config
            bot.save()
            
            return Response({
                'message': 'UI configuration updated successfully',
                'config': {
                    'inline_keyboards': bot.ui_config.get('inline_keyboards', {}) if bot.ui_config else {},
                    'forms': bot.ui_config.get('forms', {}) if bot.ui_config else {},
                    'welcome_message': bot.welcome_message or '',
                    'help_message': bot.help_message or '',
                    'default_inline_keyboard': bot.default_inline_keyboard if bot.default_inline_keyboard else [],
                }
            }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='keyboards/(?P<keyboard_name>[^/.]+)')
    def get_keyboard(self, request, pk=None, keyboard_name=None):
        """
        Get specific keyboard configuration for a bot.
        
        GET /api/v1/bots/{id}/keyboards/{keyboard_name}/ - Get keyboard configuration
        """
        bot = self.get_object()
        
        if not bot.ui_config or 'inline_keyboards' not in bot.ui_config:
            return Response(
                {'error': f'Keyboard "{keyboard_name}" not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        keyboards = bot.ui_config.get('inline_keyboards', {})
        if keyboard_name not in keyboards:
            return Response(
                {'error': f'Keyboard "{keyboard_name}" not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'keyboard_name': keyboard_name,
            'config': keyboards[keyboard_name]
        })
    
    @action(detail=True, methods=['get'], url_path='test-telegram-connection')
    def test_telegram_connection(self, request, pk=None):
        """
        Test Telegram bot token connection.
        
        GET /api/v1/bots/{id}/test-telegram-connection/ - Test Telegram token
        
        Returns:
        {
            "success": true/false,
            "bot_info": {
                "id": ...,
                "username": "...",
                "first_name": "...",
                ...
            } or null,
            "error": "error message" or null
        }
        """
        bot = self.get_object()
        
        if not bot.telegram_token:
            return Response({
                'success': False,
                'bot_info': None,
                'error': 'Telegram token is not set for this bot'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get decrypted token
        telegram_token = bot.decrypted_telegram_token
        if not telegram_token:
            return Response({
                'success': False,
                'bot_info': None,
                'error': 'Telegram token is not set or could not be decrypted'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Test token by calling Telegram Bot API getMe endpoint
        try:
            url = f'https://api.telegram.org/bot{telegram_token}/getMe'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    
                    # Try to send notification to user if they have telegram_id
                    # Note: This will only work if user has started a conversation with the bot
                    notification_sent = False
                    notification_error = None
                    
                    # Refresh user from database to get latest telegram_id
                    request.user.refresh_from_db()
                    has_telegram_id = bool(request.user.telegram_id)
                    
                    logger = logging.getLogger(__name__)
                    logger.info(
                        f'Testing Telegram connection for bot {bot.id}. '
                        f'User {request.user.id} (email: {request.user.email}) has telegram_id: {request.user.telegram_id}'
                    )
                    
                    # Only attempt notification if user has telegram_id
                    # This is optional - test success doesn't depend on notification
                    if has_telegram_id:
                        try:
                            notification_message = (
                                f"✅ Bot Connection Test Successful!\n\n"
                                f"Bot: @{bot_info.get('username', 'N/A')} ({bot_info.get('first_name', 'N/A')})\n"
                                f"Bot ID: {bot_info.get('id')}\n"
                                f"Bot Name: {bot.name}\n"
                                f"Connection verified at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            )
                            
                            send_url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
                            send_response = requests.post(
                                send_url,
                                json={
                                    'chat_id': request.user.telegram_id,
                                    'text': notification_message,
                                },
                                timeout=10
                            )
                            
                            send_data = send_response.json() if send_response.headers.get('content-type', '').startswith('application/json') else {}
                            
                            if send_response.status_code == 200 and send_data.get('ok'):
                                notification_sent = True
                                logger.info(f'Successfully sent notification to user {request.user.id}')
                            else:
                                # Get error description from Telegram API response
                                error_desc = send_data.get('description', f'Telegram API returned status {send_response.status_code}')
                                
                                # Common errors - provide helpful messages
                                if 'chat not found' in error_desc.lower() or 'bot blocked' in error_desc.lower():
                                    notification_error = (
                                        'To receive notifications, you need to start a conversation with this bot first. '
                                        f'Send /start to @{bot_info.get("username", "the bot")} in Telegram.'
                                    )
                                else:
                                    notification_error = f'Could not send notification: {error_desc}'
                                
                                # Log warning but don't fail the test
                                logger.info(
                                    f'Could not send Telegram notification to user {request.user.id} (telegram_id: {request.user.telegram_id}). '
                                    f'Reason: {error_desc}. This is normal if user hasn\'t started a conversation with the bot.'
                                )
                        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
                            # Network errors - log but don't fail test
                            notification_error = 'Network error while sending notification'
                            logger.info(f'Network error sending Telegram notification (non-critical): {str(e)}')
                        except Exception as e:
                            # Other errors - log but don't fail test
                            notification_error = f'Unexpected error: {str(e)}'
                            logger.warning(f'Error sending Telegram notification (non-critical): {str(e)}', exc_info=True)
                    
                    return Response({
                        'success': True,
                        'bot_info': {
                            'id': bot_info.get('id'),
                            'username': bot_info.get('username'),
                            'first_name': bot_info.get('first_name'),
                            'is_bot': bot_info.get('is_bot'),
                            'can_join_groups': bot_info.get('can_join_groups'),
                            'can_read_all_group_messages': bot_info.get('can_read_all_group_messages'),
                            'supports_inline_queries': bot_info.get('supports_inline_queries'),
                        },
                        'notification_sent': notification_sent,
                        'notification_error': notification_error,
                        'has_telegram_id': has_telegram_id,
                        'telegram_id': str(request.user.telegram_id) if request.user.telegram_id else None,
                        'error': None
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'bot_info': None,
                        'error': data.get('description', 'Invalid token or bot not found')
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'bot_info': None,
                    'error': f'Telegram API returned status {response.status_code}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'bot_info': None,
                'error': 'Connection timeout. Please check your internet connection.'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({
                'success': False,
                'bot_info': None,
                'error': 'Failed to connect to Telegram API. Please check your internet connection.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({
                'success': False,
                'bot_info': None,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='bot-status')
    def bot_status(self, request, pk=None):
        """
        Get bot running status.
        
        GET /api/v1/bots/{id}/bot-status/ - Get bot status
        
        Returns:
        {
            "is_running": true/false,
            "last_heartbeat": "2025-01-23T12:00:00Z" or null,
            "error": "error message" or null
        }
        """
        bot = self.get_object()
        
        # For now, check if bot is active and has token
        # In future, can use signals or file-based heartbeat
        is_running = (
            bot.status == 'active' and
            bot.telegram_token and
            bot.telegram_token.strip() != ''
        )
        
        # Use updated_at as proxy for last activity
        # In production, would use a heartbeat mechanism
        last_heartbeat = bot.updated_at if is_running else None
        
        return Response({
            'is_running': is_running,
            'last_heartbeat': last_heartbeat.isoformat() if last_heartbeat else None,
            'error': None
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='restart-bot')
    def restart_bot(self, request, pk=None):
        """
        Restart bot (signal bot process to restart).
        
        POST /api/v1/bots/{id}/restart-bot/ - Restart bot
        
        Returns:
        {
            "success": true/false,
            "message": "Bot restart signal sent" or error message
        }
        """
        bot = self.get_object()
        
        # Use decrypted token for restart check
        telegram_token = bot.decrypted_telegram_token
        if not telegram_token:
            return Response({
                'success': False,
                'message': 'Telegram token is not set for this bot'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if bot.status != 'active':
            return Response({
                'success': False,
                'message': f'Bot status is "{bot.status}", not "active". Cannot restart inactive bot.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Trigger restart by updating bot (BotMonitor will detect change)
        # Touch updated_at to trigger monitor reload
        bot.save(update_fields=['updated_at'])
        
        # In production, could use:
        # - Django signals
        # - Redis pub/sub
        # - File-based signals
        # - HTTP endpoint on bot process
        
        return Response({
            'success': True,
            'message': 'Bot restart signal sent. Bot will be restarted by monitor within 30 seconds.'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get', 'post'], url_path='api-keys')
    def api_keys(self, request, pk=None):
        """
        Get or create API keys for a bot.
        
        GET /api/v1/bots/{id}/api-keys/ - List API keys
        POST /api/v1/bots/{id}/api-keys/ - Create new API key
        """
        bot = self.get_object()
        
        if request.method == 'GET':
            # List API keys
            api_keys = BotAPIKey.objects.filter(bot=bot).order_by('-created_at')
            serializer = BotAPIKeySerializer(api_keys, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Create new API key
            serializer = BotAPIKeyCreateSerializer(
                data=request.data,
                context={'bot': bot}
            )
            serializer.is_valid(raise_exception=True)
            api_key_obj = serializer.save()
            
            # Get plain key from context
            plain_key = serializer.context.get('plain_key')
            
            return Response({
                'id': str(api_key_obj.id),
                'name': api_key_obj.name,
                'key': plain_key,  # Only returned once on creation
                'key_prefix': api_key_obj.key_prefix,
                'created_at': api_key_obj.created_at.isoformat(),
                'expires_at': api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None,
                'warning': 'Save this key securely. It will not be shown again.'
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='api-keys/(?P<api_key_id>[^/.]+)')
    def delete_api_key(self, request, pk=None, api_key_id=None):
        """
        Delete an API key.

        DELETE /api/v1/bots/{id}/api-keys/{api_key_id}/
        """
        bot = self.get_object()

        try:
            api_key = BotAPIKey.objects.get(id=api_key_id, bot=bot)
            api_key.delete()
            return Response({
                'message': 'API key deleted successfully'
            }, status=status.HTTP_200_OK)
        except BotAPIKey.DoesNotExist:
            return Response(
                {'error': 'API key not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='set-webhook')
    def set_webhook(self, request, pk=None):
        """
        Enable webhook mode and register webhook with Telegram.

        POST /api/v1/bots/{id}/set-webhook/

        Body (optional):
        {
            "webhook_url": "https://custom-url.com/webhook"  // Optional, uses default if not provided
        }

        Returns:
        {
            "success": true/false,
            "webhook_url": "...",
            "delivery_mode": "webhook",
            "telegram_response": {...}
        }
        """
        bot = self.get_object()

        if not bot.telegram_token:
            return Response({
                'success': False,
                'error': 'Telegram token is not set for this bot'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get custom webhook URL from request (optional)
        custom_url = request.data.get('webhook_url')
        if custom_url:
            bot.webhook_url = custom_url

        # Build webhook URL
        from django.conf import settings
        if bot.webhook_url:
            webhook_url = bot.webhook_url
        else:
            base_url = getattr(settings, 'WEBHOOK_BASE_URL', 'http://localhost:8000')
            webhook_url = f"{base_url}/api/telegram/webhook/{bot.id}/"

        # Generate webhook secret if not exists
        import secrets
        if not bot.webhook_secret:
            bot.webhook_secret = secrets.token_urlsafe(32)

        # Update delivery mode
        bot.delivery_mode = 'webhook'
        bot.save(update_fields=['webhook_secret', 'delivery_mode', 'webhook_url'])

        # Register webhook with Telegram
        telegram_api_url = f"https://api.telegram.org/bot{bot.decrypted_telegram_token}/setWebhook"

        try:
            response = requests.post(
                telegram_api_url,
                json={
                    'url': webhook_url,
                    'secret_token': bot.webhook_secret,
                    'allowed_updates': ['message', 'callback_query']
                },
                timeout=10
            )
            result = response.json()

            if result.get('ok'):
                logger.info(f"Webhook registered for bot {bot.name}: {webhook_url}")
                return Response({
                    'success': True,
                    'webhook_url': webhook_url,
                    'delivery_mode': bot.delivery_mode,
                    'telegram_response': result
                }, status=status.HTTP_200_OK)
            else:
                # Rollback on failure
                bot.delivery_mode = 'polling'
                bot.save(update_fields=['delivery_mode'])
                return Response({
                    'success': False,
                    'error': f"Failed to register webhook: {result.get('description', 'Unknown error')}",
                    'telegram_response': result
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Rollback on exception
            bot.delivery_mode = 'polling'
            bot.save(update_fields=['delivery_mode'])
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='delete-webhook')
    def delete_webhook(self, request, pk=None):
        """
        Disable webhook mode and switch to polling.

        POST /api/v1/bots/{id}/delete-webhook/

        Returns:
        {
            "success": true/false,
            "delivery_mode": "polling",
            "telegram_response": {...}
        }
        """
        bot = self.get_object()

        if bot.delivery_mode != 'webhook':
            return Response({
                'success': True,
                'message': 'Bot is not in webhook mode',
                'delivery_mode': bot.delivery_mode
            }, status=status.HTTP_200_OK)

        # Delete webhook from Telegram
        telegram_api_url = f"https://api.telegram.org/bot{bot.decrypted_telegram_token}/deleteWebhook"

        try:
            response = requests.post(telegram_api_url, timeout=10)
            result = response.json()

            # Update delivery mode to polling regardless of Telegram response
            # (idempotent operation - safe to call multiple times)
            bot.delivery_mode = 'polling'
            bot.save(update_fields=['delivery_mode'])

            if result.get('ok'):
                logger.info(f"Webhook deleted for bot {bot.name}")
            else:
                logger.warning(f"Telegram returned error when deleting webhook for {bot.name}: {result}")

            return Response({
                'success': True,
                'delivery_mode': bot.delivery_mode,
                'telegram_response': result,
                'message': 'Webhook mode disabled. Bot will use polling mode.'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Still update delivery mode even if Telegram call fails
            bot.delivery_mode = 'polling'
            bot.save(update_fields=['delivery_mode'])

            return Response({
                'success': True,
                'delivery_mode': bot.delivery_mode,
                'warning': f'Could not confirm webhook deletion with Telegram: {str(e)}'
            }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='webhook-info')
    def webhook_info(self, request, pk=None):
        """
        Get webhook information from Telegram.

        GET /api/v1/bots/{id}/webhook-info/

        Returns:
        {
            "delivery_mode": "webhook" | "polling",
            "webhook_url": "...",
            "has_custom_url": true/false,
            "webhook_secret_set": true/false,
            "telegram_webhook_info": {...}  // From getWebhookInfo API
        }
        """
        bot = self.get_object()

        # Get webhook info from Telegram
        telegram_info = None
        telegram_api_url = f"https://api.telegram.org/bot{bot.decrypted_telegram_token}/getWebhookInfo"

        try:
            response = requests.get(telegram_api_url, timeout=10)
            result = response.json()
            if result.get('ok'):
                telegram_info = result.get('result', {})
        except Exception as e:
            logger.warning(f"Failed to get webhook info from Telegram: {str(e)}")

        return Response({
            'delivery_mode': bot.delivery_mode,
            'webhook_url': bot.webhook_url or None,
            'has_custom_url': bool(bot.webhook_url),
            'webhook_secret_set': bool(bot.webhook_secret),
            'telegram_webhook_info': telegram_info
        }, status=status.HTTP_200_OK)
        """
        Delete an API key.
        
        DELETE /api/v1/bots/{id}/api-keys/{api_key_id}/
        """
        bot = self.get_object()
        
        try:
            api_key = BotAPIKey.objects.get(id=api_key_id, bot=bot)
            api_key.delete()
            return Response({
                'message': 'API key deleted successfully'
            }, status=status.HTTP_200_OK)
        except BotAPIKey.DoesNotExist:
            return Response(
                {'error': 'API key not found'},
                status=status.HTTP_404_NOT_FOUND
            )
