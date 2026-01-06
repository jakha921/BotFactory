"""
URL configuration for commands app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.commands.views import CommandViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'commands', CommandViewSet, basename='command')

urlpatterns = router.urls
