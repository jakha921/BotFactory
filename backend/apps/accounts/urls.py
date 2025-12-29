"""
URLs for accounts app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import (
    RegisterView,
    login_view,
    logout_view,
    user_me_view,
    user_update_view,
    subscription_usage_view,
    UserAPIKeyViewSet,
    password_reset_request_view,
    password_reset_confirm_view,
    change_password_view,
    NotificationPreferencesViewSet,
)

app_name = 'accounts'

router = DefaultRouter()
router.register(r'api-keys', UserAPIKeyViewSet, basename='user-api-keys')
router.register(r'notifications', NotificationPreferencesViewSet, basename='notifications')

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', user_me_view, name='me'),
    path('me/update/', user_update_view, name='me_update'),
    # Password Reset
    path('password-reset/', password_reset_request_view, name='password_reset'),
    path('password-reset/confirm/', password_reset_confirm_view, name='password_reset_confirm'),
    # Password Change
    path('change-password/', change_password_view, name='change_password'),
    # API Keys management and Notifications
    path('', include(router.urls)),
]
