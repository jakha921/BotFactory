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

# Customize admin site
admin.site.site_header = "Bot Factory Administration"
admin.site.site_title = "Bot Factory Admin"
admin.site.index_title = "Welcome to Bot Factory Administration"


urlpatterns = [
    # Admin site (django-unfold)
    path('admin/', admin.site.urls),
    
    # Webhook endpoint for Telegram updates (must be before API routes)
    # POST /webhook/<token>/
    path('webhook/<str:token>/', include('apps.telegram.webhook_urls')),
    
    # API v1 endpoints
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/subscription/', subscription_usage_view, name='subscription'),  # Subscription endpoint
    path('api/v1/bots/', include('apps.bots.urls')),
    path('api/v1/', include('apps.knowledge.urls')),
    path('api/v1/', include('apps.chat.urls')),
    path('api/v1/', include('apps.telegram.urls')),
    path('api/v1/', include('apps.analytics.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
