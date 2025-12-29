"""
Views for accounts app.
Authentication views for Bot Factory API.
"""
import logging
from functools import wraps

from rest_framework import status, generics, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.conf import settings

from apps.accounts.serializers import (
    UserSerializer,
    UserRegisterSerializer,
    UserUpdateSerializer,
    UserAPIKeySerializer,
    UserAPIKeyCreateSerializer,
    NotificationPreferencesSerializer,
)
from rest_framework.exceptions import AuthenticationFailed, ValidationError as DRFValidationError, Throttled
from apps.bots.models import Bot
from apps.knowledge.models import Document
from apps.accounts.models import UserAPIKey

logger = logging.getLogger(__name__)
User = get_user_model()


# Rate limiting decorator for auth endpoints
def rate_limit(key_prefix: str, limit: int = 5, period: int = 60):
    """
    Simple rate limiting decorator using Django cache.
    
    Args:
        key_prefix: Prefix for cache key (e.g., 'login', 'register')
        limit: Maximum number of requests allowed
        period: Time period in seconds
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR', 'unknown')
            
            # Create cache key
            cache_key = f"ratelimit:{key_prefix}:{ip}"
            
            # Get current count
            current_count = cache.get(cache_key, 0)
            
            if current_count >= limit:
                logger.warning(f"Rate limit exceeded for {key_prefix} from IP: {ip}")
                raise Throttled(detail={
                    'message': f'Too many requests. Please try again in {period} seconds.',
                    'code': 'rate_limit_exceeded',
                    'retry_after': period
                })
            
            # Increment count
            cache.set(cache_key, current_count + 1, period)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    Rate limited to 3 registrations per hour per IP.
    
    POST /api/v1/auth/register/
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegisterSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new user and return JWT tokens."""
        # Rate limiting for registration
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        cache_key = f"ratelimit:register:{ip}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= 3:  # 3 registrations per hour
            logger.warning(f"Registration rate limit exceeded from IP: {ip}")
            raise Throttled(detail={
                'message': 'Too many registration attempts. Please try again later.',
                'code': 'rate_limit_exceeded',
                'retry_after': 3600
            })
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Increment registration count
        cache.set(cache_key, current_count + 1, 3600)  # 1 hour
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
@rate_limit('login', limit=5, period=60)  # 5 attempts per minute
def login_view(request):
    """
    User login endpoint.
    Rate limited to 5 attempts per minute per IP.
    
    POST /api/v1/auth/login/
    Body: { "email": "user@example.com", "password": "password123" }
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        raise DRFValidationError({
            'email': 'Email and password are required.',
            'password': 'Email and password are required.'
        })
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise AuthenticationFailed({
            'message': 'Invalid email or password.',
            'code': 'invalid_credentials'
        })
    
    if not check_password(password, user.password):
        raise AuthenticationFailed({
            'message': 'Invalid email or password.',
            'code': 'invalid_credentials'
        })
    
    if not user.is_active:
        raise AuthenticationFailed({
            'message': 'User account is disabled.',
            'code': 'account_disabled'
        })
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'user': UserSerializer(user).data,
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    User logout endpoint.
    
    POST /api/v1/auth/logout/
    Body: { "refresh": "refresh_token_string" }
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception as e:
        # Token might already be blacklisted or invalid
        # Still return success to prevent token leakage
        pass
    
    return Response({
        'message': 'Successfully logged out.'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_me_view(request):
    """
    Get current user endpoint.
    
    GET /api/v1/auth/me/
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_update_view(request):
    """
    Update current user endpoint.
    
    PUT/PATCH /api/v1/auth/me/update/
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f'User update request from {request.user.email}. Data: {request.data}')
    logger.info(f'Current user telegram_id before update: {request.user.telegram_id}')
    
    serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    
    logger.info(f'Validated data: {serializer.validated_data}')
    
    updated_user = serializer.save()
    
    # Refresh from database to get latest values
    updated_user.refresh_from_db()
    
    logger.info(f'User telegram_id after update: {updated_user.telegram_id}')
    
    return Response(UserSerializer(updated_user).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_usage_view(request):
    """
    Get subscription usage endpoint.
    
    GET /api/v1/subscription/
    Returns subscription plan and usage statistics.
    """
    user = request.user
    
    # Get usage statistics
    bots_count = Bot.objects.filter(owner=user).count()
    documents_count = Document.objects.filter(bot__owner=user).count()
    # API calls count would need to be tracked separately
    api_calls_count = 0  # placeholder
    
    # Define plan limits
    plan_limits = {
        'Free': {
            'bots': 1,
            'documents': 10,
            'apiCalls': 100
        },
        'Pro': {
            'bots': 5,
            'documents': 500,
            'apiCalls': 10000
        },
        'Enterprise': {
            'bots': float('inf'),  # unlimited
            'documents': 10000,
            'apiCalls': 100000
        }
    }
    
    limits = plan_limits.get(user.plan, plan_limits['Free'])
    
    response_data = {
        'plan': user.plan,
        'renewalDate': None,  # Would need subscription tracking
        'bots': {
            'used': bots_count,
            'limit': limits['bots'] if limits['bots'] != float('inf') else None
        },
        'documents': {
            'used': documents_count,
            'limit': limits['documents']
        },
        'apiCalls': {
            'used': api_calls_count,
            'limit': limits['apiCalls']
        }
    }
    
    return Response(response_data, status=status.HTTP_200_OK)


class UserAPIKeyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user API keys.
    
    list: GET /api/v1/auth/api-keys/ - List all user API keys
    create: POST /api/v1/auth/api-keys/ - Create a new API key
    destroy: DELETE /api/v1/auth/api-keys/{id}/ - Delete an API key
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's API keys."""
        return UserAPIKey.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Use different serializers for create vs list."""
        if self.action == 'create':
            return UserAPIKeyCreateSerializer
        return UserAPIKeySerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new encrypted API key."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_key = serializer.save()
        
        # Return the full representation using UserAPIKeySerializer
        return Response(
            UserAPIKeySerializer(api_key).data,
            status=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete an API key."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """Send password reset email."""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.core.mail import send_mail
    from django.conf import settings
    from apps.accounts.serializers import PasswordResetRequestSerializer
    
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    user = User.objects.get(email=email)
    
    # Generate token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Create reset link
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    reset_url = f"{frontend_url}/reset-password?uid={uid}&token={token}"
    
    # Send email
    try:
        send_mail(
            subject='Reset Your Bot Factory Password',
            message=f'Click the link to reset your password: {reset_url}\n\nThis link expires in 1 hour.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to send email: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({
        'message': 'Password reset email sent. Please check your inbox.'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """Reset password with token."""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from apps.accounts.serializers import PasswordResetConfirmSerializer
    
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        raise ValidationError({'uid': 'Invalid user ID'})
    
    # Verify token
    if not default_token_generator.check_token(user, serializer.validated_data['token']):
        raise ValidationError({'token': 'Invalid or expired token'})
    
    # Set new password
    user.set_password(serializer.validated_data['new_password'])
    user.save()
    
    return Response({'message': 'Password reset successful. You can now log in.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """Change user password."""
    from apps.accounts.serializers import PasswordChangeSerializer
    
    serializer = PasswordChangeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Verify current password
    if not request.user.check_password(serializer.validated_data['current_password']):
        raise DRFValidationError({'current_password': 'Incorrect password'})
    
    # Set new password
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save()
    
    return Response({'message': 'Password changed successfully'})


class NotificationPreferencesViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user notification preferences."""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationPreferencesSerializer
    http_method_names = ['get', 'put', 'patch']
    
    def get_object(self):
        """Get or create notification preferences for current user."""
        from apps.accounts.models import UserNotificationPreferences
        prefs, created = UserNotificationPreferences.objects.get_or_create(
            user=self.request.user
        )
        return prefs
    
    def list(self, request):
        """Return user's notification preferences."""
        prefs = self.get_object()
        serializer = self.get_serializer(prefs)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update user's notification preferences."""
        prefs = self.get_object()
        serializer = self.get_serializer(prefs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
