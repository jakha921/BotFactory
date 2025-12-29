"""
Serializers for accounts app.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.accounts.models import User, UserAPIKey, UserNotificationPreferences


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (for reading user data)."""
    telegramId = serializers.IntegerField(source='telegram_id', allow_null=True, required=False)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'plan',
            'telegramId',
            'avatar',
            'createdAt',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Customize representation to match frontend types (camelCase)."""
        representation = {
            'id': str(instance.id),
            'email': instance.email,
            'name': instance.name,
            'plan': instance.plan,
            'telegramId': str(instance.telegram_id) if instance.telegram_id else None,
            'avatar': instance.avatar if instance.avatar else '',
            'createdAt': instance.created_at.isoformat() if instance.created_at else None,
        }
        return representation


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True
    )
    
    class Meta:
        model = User
        fields = [
            'email',
            'name',
            'password',
            'password_confirm',
            'plan',
        ]
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs
    
    def create(self, validated_data):
        """Create a new user."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        plan = validated_data.pop('plan', 'Free')
        
        user = User.objects.create_user(
            password=password,
            plan=plan,
            **validated_data
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    telegramId = serializers.IntegerField(source='telegram_id', required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'name',
            'avatar',
            'plan',
            'telegramId',
        ]
    
    def to_internal_value(self, data):
        """Convert camelCase to snake_case and validate."""
        # Handle camelCase field names from frontend
        # We need to keep telegramId as is because it has source='telegram_id' in field definition
        internal_data = {}
        for key, value in data.items():
            if key == 'telegramId':
                # Convert to integer if provided, None if empty
                # Keep as telegramId because field definition has source='telegram_id'
                if value is not None and value != '':
                    try:
                        internal_data['telegramId'] = int(value)
                    except (ValueError, TypeError):
                        internal_data['telegramId'] = None
                else:
                    internal_data['telegramId'] = None
            else:
                internal_data[key] = value
        
        # Call parent to_internal_value which will handle the source mapping
        validated_data = super().to_internal_value(internal_data)
        return validated_data
    
    def update(self, instance, validated_data):
        """Update user instance."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f'UserUpdateSerializer.update called with validated_data: {validated_data}')
        logger.info(f'Instance telegram_id before update: {instance.telegram_id}')
        
        # After to_internal_value and validation, DRF converts telegramId to telegram_id
        # based on the source='telegram_id' mapping in the field definition
        # So validated_data will have 'telegram_id' key, not 'telegramId'
        for attr, value in validated_data.items():
            logger.info(f'Setting {attr} = {value} (type: {type(value)})')
            # Directly set the attribute on the instance
            setattr(instance, attr, value)
        
        instance.save()
        
        # Refresh from database to ensure value is saved
        instance.refresh_from_db()
        
        logger.info(f'Instance telegram_id after save and refresh: {instance.telegram_id}')
        
        return instance


class UserAPIKeySerializer(serializers.ModelSerializer):
    """Serializer for listing user API keys (without exposing the actual key)."""
    
    class Meta:
        model = UserAPIKey
        fields = ['id', 'name', 'provider', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def to_representation(self, instance):
        """Return camelCase representation."""
        return {
            'id': str(instance.id),
            'name': instance.name,
            'provider': instance.provider,
            'key': instance.masked_key,  # Masked version
            'created': instance.created_at.strftime('%Y-%m-%d'),
        }


class UserAPIKeyCreateSerializer(serializers.Serializer):
    """Serializer for creating a new user API key."""
    name = serializers.CharField(max_length=100, required=True)
    provider = serializers.ChoiceField(choices=['openai', 'gemini', 'anthropic'], required=True)
    key = serializers.CharField(required=True, write_only=True)
    
    def validate_key(self, value):
        """Validate that key is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("API key cannot be empty")
        return value.strip()
    
    def create(self, validated_data):
        """Create a new encrypted API key for the user."""
        user = self.context['request'].user
        plain_key = validated_data.pop('key')
        
        api_key = UserAPIKey(
            user=user,
            name=validated_data['name'],
            provider=validated_data['provider']
        )
        api_key.encrypt_key(plain_key)
        api_key.save()
        
        return api_key


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request password reset via email."""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirm password reset with token."""
    token = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Change user password."""
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return attrs


class NotificationPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for user notification preferences."""
    class Meta:
        model = UserNotificationPreferences
        fields = ['email_alerts', 'push_notifications', 'weekly_digest']
