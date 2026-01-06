"""
Serializers for commands app.
"""
from rest_framework import serializers
from apps.commands.models import Command


class CommandSerializer(serializers.ModelSerializer):
    """Serializer for Command model."""

    class Meta:
        model = Command
        fields = [
            'id',
            'bot',
            'name',
            'description',
            'response_type',
            'text_response',
            'ai_prompt_override',
            'form_id',
            'menu_config',
            'is_active',
            'priority',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        """Validate based on response type."""
        response_type = data.get('response_type')

        if response_type == 'text' and not data.get('text_response'):
            raise serializers.ValidationError({
                'text_response': 'Required for TEXT response type'
            })

        if response_type == 'form' and not data.get('form_id'):
            raise serializers.ValidationError({
                'form_id': 'Required for FORM response type'
            })

        return data
