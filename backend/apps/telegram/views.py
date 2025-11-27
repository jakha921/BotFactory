"""
Views for telegram app.
TelegramUserViewSet for managing Telegram users.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.telegram.models import TelegramUser
from apps.bots.models import Bot
from apps.telegram.serializers import (
    TelegramUserSerializer,
    UpdateUserStatusSerializer,
)
from core.permissions import IsOwnerOrReadOnly


class TelegramUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing Telegram users.
    
    list: GET /api/v1/bots/{bot_id}/users/ - List Telegram users for a bot
    retrieve: GET /api/v1/users/{id}/ - Get user details
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TelegramUserSerializer
    
    def get_queryset(self):
        """Filter users by bot and ensure user owns the bot."""
        bot_id = self.kwargs.get('bot_id')
        if bot_id:
            bot = get_object_or_404(Bot, id=bot_id, owner=self.request.user)
            return TelegramUser.objects.filter(bot=bot).select_related('bot')
        return TelegramUser.objects.none()
    
    def list(self, request, bot_id=None):
        """List Telegram users for a bot."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='status')
    def update_status(self, request, pk=None):
        """
        Update user status endpoint.
        
        POST /api/v1/users/{id}/status/
        Body: { "status": "active" | "blocked" }
        """
        user = self.get_object()
        # Ensure user's bot belongs to current user
        if user.bot.owner != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UpdateUserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user.status = serializer.validated_data['status']
        user.save()
        
        return Response({
            'message': 'Status updated successfully',
            'user': TelegramUserSerializer(user).data
        }, status=status.HTTP_200_OK)
