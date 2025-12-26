"""
Serializers for telegram app.
"""
from rest_framework import serializers

from apps.telegram.models import TelegramUser


class TelegramUserSerializer(serializers.ModelSerializer):
    """Serializer for TelegramUser model."""
    firstName = serializers.CharField(source='first_name', read_only=True)
    lastName = serializers.CharField(source='last_name', read_only=True)
    avatarUrl = serializers.URLField(source='avatar_url', read_only=True)
    firstSeen = serializers.DateTimeField(source='first_seen', read_only=True)
    lastActive = serializers.DateTimeField(source='last_active', read_only=True)
    messageCount = serializers.IntegerField(source='message_count', read_only=True)
    botId = serializers.UUIDField(source='bot.id', read_only=True)
    # Expose telegram_id as camelCase telegramId for frontend
    telegramId = serializers.CharField(source='telegram_id', read_only=True)
    
    class Meta:
        model = TelegramUser
        fields = [
            'id',
            'telegramId',
            'username',
            'firstName',
            'lastName',
            'avatarUrl',
            'firstSeen',
            'lastActive',
            'messageCount',
            'botId',
            'notes',
            'status',
        ]
        read_only_fields = ['id', 'first_seen', 'last_active', 'message_count']
    
    def to_representation(self, instance):
        """Customize representation to match frontend types."""
        data = super().to_representation(instance)
        return {
            'id': str(data['id']),
            'telegramId': str(data['telegramId']),
            'username': data.get('username', ''),
            'firstName': data.get('firstName', ''),
            'lastName': data.get('lastName', ''),
            'avatarUrl': data.get('avatarUrl', ''),
            'firstSeen': instance.first_seen.isoformat() if instance.first_seen else None,
            'lastActive': instance.last_active.isoformat() if instance.last_active else None,
            'messageCount': data.get('messageCount', 0),
            'botId': str(data['botId']),
            'notes': data.get('notes', ''),
            'status': data.get('status', 'active'),
        }


class UpdateUserStatusSerializer(serializers.Serializer):
    """Serializer for updating user status."""
    status = serializers.ChoiceField(choices=['active', 'blocked'])
    
    class Meta:
        fields = ['status']

