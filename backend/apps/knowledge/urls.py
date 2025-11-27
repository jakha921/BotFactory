"""
URLs for knowledge app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.knowledge.views import DocumentViewSet, TextSnippetViewSet

app_name = 'knowledge'

router = DefaultRouter()
router.register(r'bots/(?P<bot_id>[^/.]+)/documents', DocumentViewSet, basename='document')
router.register(r'snippets', TextSnippetViewSet, basename='snippet')

urlpatterns = [
    path('', include(router.urls)),
]

