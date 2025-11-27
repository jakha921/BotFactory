"""
Views for bots app.
BotViewSet for CRUD operations on bots.
"""
import logging
import requests
from django.utils import timezone
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
)
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
        """Filter bots by current user."""
        return Bot.objects.filter(owner=self.request.user)
    
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
                    
                    # Send notification to admin if they have telegram_id
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
                    
                    if has_telegram_id:
                        try:
                            notification_message = (
                                f"Bot Connection Test Successful!\n\n"
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
                            else:
                                # Get error description from Telegram API response
                                notification_error = send_data.get('description', f'Telegram API returned status {send_response.status_code}')
                                # Common errors:
                                if 'chat not found' in notification_error.lower():
                                    notification_error = 'User must start a conversation with the bot first. Send /start to the bot in Telegram.'
                                elif 'bot blocked' in notification_error.lower() or 'blocked' in notification_error.lower():
                                    notification_error = 'Bot is blocked by user. Unblock the bot in Telegram.'
                                
                                logger.warning(
                                    f'Failed to send Telegram notification to user {request.user.id} (telegram_id: {request.user.telegram_id}). '
                                    f'Error: {notification_error}. Response: {send_data}'
                                )
                        except requests.exceptions.ConnectionError as e:
                            # Connection refused or network unreachable
                            notification_error = f'Cannot connect to Telegram API. Please check your internet connection or firewall settings. Error: {str(e)}'
                            logger.error(f'Connection error sending Telegram notification: {str(e)}', exc_info=True)
                        except requests.exceptions.Timeout as e:
                            notification_error = f'Telegram API request timed out. Please try again later.'
                            logger.error(f'Timeout error sending Telegram notification: {str(e)}', exc_info=True)
                        except requests.exceptions.RequestException as e:
                            notification_error = f'Network error: {str(e)}'
                            logger.error(f'Network error sending Telegram notification: {str(e)}', exc_info=True)
                        except Exception as e:
                            notification_error = f'Unexpected error: {str(e)}'
                            logger.error(f'Error sending Telegram notification: {str(e)}', exc_info=True)
                    
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
