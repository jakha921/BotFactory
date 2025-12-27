"""
Serializers for bots app.
"""
from rest_framework import serializers
from apps.bots.models import Bot, BotAPIKey


class BotSerializer(serializers.ModelSerializer):
    """Serializer for Bot model (for reading bot data)."""
    conversations_count = serializers.IntegerField(read_only=True)
    documents_count = serializers.IntegerField(read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    systemInstruction = serializers.CharField(source='system_instruction', required=False, allow_blank=True)
    thinkingBudget = serializers.IntegerField(source='thinking_budget', required=False, allow_null=True)
    telegramToken = serializers.CharField(source='telegram_token', required=False, allow_blank=True)
    uiConfig = serializers.JSONField(source='ui_config', required=False, allow_null=True)
    defaultInlineKeyboard = serializers.JSONField(source='default_inline_keyboard', required=False, allow_null=True)
    welcomeMessage = serializers.CharField(source='welcome_message', required=False, allow_blank=True)
    helpMessage = serializers.CharField(source='help_message', required=False, allow_blank=True)
    
    class Meta:
        model = Bot
        fields = [
            'id',
            'name',
            'description',
            'status',
            'model',
            'provider',
            'temperature',
            'systemInstruction',
            'thinkingBudget',
            'telegramToken',
            'avatar',
            'createdAt',
            'conversations_count',
            'documents_count',
            'owner_email',
            'uiConfig',
            'defaultInlineKeyboard',
            'welcomeMessage',
            'helpMessage',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']
    
    def to_representation(self, instance):
        """Customize representation to match frontend types (camelCase)."""
        # Mask telegram token for security - only show last 8 characters
        masked_token = ''
        if instance.telegram_token:
            decrypted = instance.decrypted_telegram_token
            if decrypted and len(decrypted) > 8:
                masked_token = '****' + decrypted[-8:]
            elif decrypted:
                masked_token = '****'
        
        representation = {
            'id': str(instance.id),
            'name': instance.name,
            'description': instance.description,
            'status': instance.status,
            'model': instance.model,
            'provider': instance.provider,
            'temperature': instance.temperature,
            'systemInstruction': instance.system_instruction,
            'thinkingBudget': instance.thinking_budget,
            # Return masked token for security
            'telegramToken': masked_token,
            'hasTelegramToken': bool(instance.telegram_token),
            'avatar': instance.avatar if instance.avatar else '',
            'createdAt': instance.created_at.isoformat() if instance.created_at else None,
            'updatedAt': instance.updated_at.isoformat() if instance.updated_at else None,
            'conversationsCount': instance.conversations_count,
            'documentsCount': instance.documents_count,
            'uiConfig': instance.ui_config if instance.ui_config else {},
            'defaultInlineKeyboard': instance.default_inline_keyboard if instance.default_inline_keyboard else [],
            'welcomeMessage': instance.welcome_message if instance.welcome_message else '',
            'helpMessage': instance.help_message if instance.help_message else '',
        }
        # Remove None values for optional fields
        if representation['thinkingBudget'] is None:
            representation['thinkingBudget'] = None  # Keep None for optional field
        return representation


class BotCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bots - owner is set automatically."""
    # Accept camelCase from frontend but map to snake_case model fields
    systemInstruction = serializers.CharField(source='system_instruction', required=False, allow_blank=True)
    thinkingBudget = serializers.IntegerField(source='thinking_budget', required=False, allow_null=True)
    telegramToken = serializers.CharField(source='telegram_token', required=False, allow_blank=True)
    
    class Meta:
        model = Bot
        fields = [
            'name',
            'description',
            'status',
            'model',
            'provider',
            'temperature',
            'systemInstruction',
            'thinkingBudget',
            'telegramToken',
            'avatar',
        ]
        extra_kwargs = {
            'name': {'required': True},
            'model': {'required': True},
            'provider': {'required': True},
        }
    
    def validate_temperature(self, value):
        """Validate temperature is between 0 and 2."""
        if not 0 <= value <= 2:
            raise serializers.ValidationError("Temperature must be between 0 and 2")
        return value
    
    def validate_thinkingBudget(self, value):
        """Validate thinking budget is non-negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Thinking budget must be non-negative")
        return value
    
    def validate_telegramToken(self, value):
        """Validate telegram token format if provided."""
        if value and value.strip():
            # Must be plain token in format: 123456789:ABC...
            import re
            if not re.match(r'^\d+:[A-Za-z0-9_-]+$', value):
                raise serializers.ValidationError(
                    "Invalid Telegram bot token format. Expected format: 123456789:ABC..."
                )
        return value


class BotUpdateSerializer(BotSerializer):
    """Serializer for updating bots - some fields may be readonly."""
    
    class Meta(BotSerializer.Meta):
        fields = BotSerializer.Meta.fields
    
    def validate_temperature(self, value):
        """Validate temperature is between 0 and 2."""
        if not 0 <= value <= 2:
            raise serializers.ValidationError("Temperature must be between 0 and 2")
        return value
    
    def validate_thinking_budget(self, value):
        """Validate thinking budget is non-negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Thinking budget must be non-negative")
        return value
    
    def validate_telegram_token(self, value):
        """Validate telegram token format if provided."""
        if value and value.strip():
            # Check if it's already encrypted (starts with Fernet prefix)
            if not value.startswith('gAAAAAB'):
                # Must be plain token in format: 123456789:ABC...
                import re
                if not re.match(r'^\d+:[A-Za-z0-9_-]+$', value):
                    raise serializers.ValidationError(
                        "Invalid Telegram bot token format. Expected format: 123456789:ABC..."
                    )
        return value
    
    def to_internal_value(self, data):
        """Convert camelCase to snake_case."""
        # Handle camelCase field names from frontend
        internal_data = {}
        field_mapping = {
            'systemInstruction': 'system_instruction',
            'thinkingBudget': 'thinking_budget',
            'telegramToken': 'telegram_token',
            'uiConfig': 'ui_config',
            'defaultInlineKeyboard': 'default_inline_keyboard',
            'welcomeMessage': 'welcome_message',
            'helpMessage': 'help_message',
        }
        
        for key, value in data.items():
            internal_key = field_mapping.get(key, key)
            internal_data[internal_key] = value
        
        return super().to_internal_value(internal_data)


class BotAPIKeySerializer(serializers.ModelSerializer):
    """Serializer for BotAPIKey model."""
    key_prefix_display = serializers.CharField(source='key_prefix', read_only=True)
    bot_name = serializers.CharField(source='bot.name', read_only=True)
    
    class Meta:
        model = BotAPIKey
        fields = [
            'id',
            'bot',
            'bot_name',
            'name',
            'key_prefix_display',
            'is_active',
            'last_used_at',
            'created_at',
            'expires_at',
        ]
        read_only_fields = ['id', 'key', 'key_prefix', 'created_at', 'last_used_at']


class BotAPIKeyCreateSerializer(serializers.Serializer):
    """Serializer for creating API keys."""
    name = serializers.CharField(max_length=100, required=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    
    def create(self, validated_data):
        """Create a new API key for the bot."""
        bot = self.context['bot']
        name = validated_data['name']
        expires_at = validated_data.get('expires_at')
        
        api_key_obj, plain_key = BotAPIKey.create_key(bot, name, expires_at)
        
        # Store plain key in context for response
        self.context['plain_key'] = plain_key
        
        return api_key_obj


class UIConfigSerializer(serializers.Serializer):
    """Serializer for UI configuration."""
    inline_keyboards = serializers.DictField(required=False, allow_null=True)
    forms = serializers.DictField(required=False, allow_null=True)
    welcome_message = serializers.CharField(required=False, allow_blank=True)
    help_message = serializers.CharField(required=False, allow_blank=True)
    default_inline_keyboard = serializers.ListField(required=False, allow_null=True)
    
    def validate_inline_keyboards(self, value):
        """Validate inline keyboards structure."""
        if value is None:
            return value
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("inline_keyboards must be a dictionary")
        
        # Validate each keyboard configuration
        for keyboard_name, keyboard_rows in value.items():
            if not isinstance(keyboard_rows, list):
                raise serializers.ValidationError(f"Keyboard '{keyboard_name}' must be a list of rows")
            
            for row in keyboard_rows:
                if not isinstance(row, list):
                    raise serializers.ValidationError(f"Keyboard '{keyboard_name}' rows must be lists")
                
                for button in row:
                    if not isinstance(button, dict):
                        raise serializers.ValidationError(f"Keyboard '{keyboard_name}' buttons must be dictionaries")
                    
                    if 'text' not in button:
                        raise serializers.ValidationError(f"Button in '{keyboard_name}' must have 'text' field")
                    
                    # Button must have either callback_data or url
                    if 'callback_data' not in button and 'url' not in button:
                        raise serializers.ValidationError(f"Button in '{keyboard_name}' must have 'callback_data' or 'url'")
        
        return value
    
    def validate_forms(self, value):
        """Validate forms structure."""
        if value is None:
            return value
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("forms must be a dictionary")
        
        # Validate each form configuration
        for form_name, form_config in value.items():
            if not isinstance(form_config, dict):
                raise serializers.ValidationError(f"Form '{form_name}' must be a dictionary")
            
            if 'steps' not in form_config:
                raise serializers.ValidationError(f"Form '{form_name}' must have 'steps' field")
            
            if not isinstance(form_config['steps'], list):
                raise serializers.ValidationError(f"Form '{form_name}' steps must be a list")
            
            for step in form_config['steps']:
                if not isinstance(step, dict):
                    raise serializers.ValidationError(f"Form '{form_name}' steps must be dictionaries")
                
                required_fields = ['field', 'type', 'prompt']
                for field in required_fields:
                    if field not in step:
                        raise serializers.ValidationError(f"Form '{form_name}' step must have '{field}' field")
        
        return value
