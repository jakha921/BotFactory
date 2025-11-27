"""
Serializers for chat app.
"""
from rest_framework import serializers
from apps.chat.models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage model."""
    isThinking = serializers.BooleanField(source='is_thinking', required=False)
    isFlagged = serializers.BooleanField(source='is_flagged', required=False)
    
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'role',
            'content',
            'timestamp',
            'isThinking',
            'isFlagged',
            'attachments',
        ]
        read_only_fields = ['id', 'timestamp']
    
    def to_representation(self, instance):
        """Customize representation to match frontend types."""
        data = super().to_representation(instance)
        return {
            'id': str(data['id']),
            'role': data['role'],
            'content': data['content'],
            'timestamp': instance.timestamp,  # Return Date object
            'isThinking': data.get('isThinking', False),
            'isFlagged': data.get('isFlagged', False),
            'attachments': data.get('attachments', []),
        }


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for ChatSession model."""
    userId = serializers.UUIDField(source='user.id', read_only=True)
    userName = serializers.SerializerMethodField()
    userAvatar = serializers.URLField(source='user.avatar_url', read_only=True)
    lastMessage = serializers.CharField(source='last_message', read_only=True)
    timestamp = serializers.DateTimeField(source='updated_at', read_only=True)
    isFlagged = serializers.BooleanField(source='is_flagged', read_only=True)
    botId = serializers.UUIDField(source='bot.id', read_only=True)
    unreadCount = serializers.IntegerField(read_only=True, default=0)
    
    class Meta:
        model = ChatSession
        fields = [
            'id',
            'userId',
            'userName',
            'userAvatar',
            'lastMessage',
            'timestamp',
            'sentiment',
            'isFlagged',
            'botId',
            'unreadCount',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_userName(self, obj):
        """Get user's full name."""
        if obj.user:
            name = f"{obj.user.first_name} {obj.user.last_name or ''}".strip()
            return name
        return "Unknown User"
    
    def to_representation(self, instance):
        """Customize representation to match frontend types."""
        data = super().to_representation(instance)
        return {
            'id': str(data['id']),
            'userId': str(data.get('userId', '')),
            'userName': data.get('userName', 'Unknown User'),
            'userAvatar': data.get('userAvatar', ''),
            'lastMessage': data.get('lastMessage', ''),
            'timestamp': instance.updated_at.isoformat() if instance.updated_at else None,
            'sentiment': data.get('sentiment', 'neutral'),
            'isFlagged': data.get('isFlagged', False),
            'botId': str(data['botId']),
            'unreadCount': data.get('unreadCount', 0),
        }

