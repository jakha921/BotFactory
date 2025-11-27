"""
URLs for accounts app.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import (
    RegisterView,
    login_view,
    logout_view,
    user_me_view,
    user_update_view,
    subscription_usage_view,
)

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', user_me_view, name='me'),
    path('me/update/', user_update_view, name='me_update'),
]

