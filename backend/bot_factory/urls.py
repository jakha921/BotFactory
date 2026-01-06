"""
Bot Factory URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.accounts.views import subscription_usage_view
from django.conf import settings
from django.conf.urls.static import static
from unfold.decorators import display
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.bots.public_views import PublicChatView
from apps.core.health_views import HealthCheckView, ReadinessCheckView

# Customize admin site
admin.site.site_header = "Bot Factory Administration"
admin.site.site_title = "Bot Factory Admin"
admin.site.index_title = "Welcome to Bot Factory Administration"


urlpatterns = [
    # Admin site (django-unfold)
    path('admin/', admin.site.urls),
    
    # API Documentation (OpenAPI/Swagger)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Health check endpoints
    path('api/health/', HealthCheckView.as_view(), name='health-check'),
    path('api/health/ready/', ReadinessCheckView.as_view(), name='readiness-check'),
    
    # Webhook endpoint for Telegram updates (must be before API routes)
    # POST /webhook/<token>/
    path('webhook/<str:token>/', include('apps.telegram.webhook_urls')),
    
    # Public API (API key authentication)
    path('api/v1/public/chat/', PublicChatView.as_view(), name='public-chat'),
    
    # API v1 endpoints
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/subscription/', subscription_usage_view, name='subscription'),  # Subscription endpoint
    path('api/v1/bots/', include('apps.bots.urls')),
    path('api/v1/', include('apps.knowledge.urls')),
    path('api/v1/', include('apps.chat.urls')),
    path('api/v1/', include('apps.telegram.urls')),
    path('api/v1/', include('apps.analytics.urls')),
    path('api/v1/ai/', include('apps.ai_settings.urls')),  # AI settings and limits
    path('api/v1/', include('apps.commands.urls')),  # Bot commands
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
