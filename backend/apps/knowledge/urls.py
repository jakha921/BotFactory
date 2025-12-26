"""
URLs for knowledge app.
"""
from django.urls import path, include
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter

from apps.knowledge.views import DocumentViewSet, DocumentChunkViewSet, TextSnippetViewSet
from apps.bots.views import BotViewSet

app_name = 'knowledge'

router = SimpleRouter()
router.register(r'bots', BotViewSet, basename='bot')
router.register(r'snippets', TextSnippetViewSet, basename='snippet')

bots_router = NestedSimpleRouter(router, r'bots', lookup='bot')
bots_router.register(r'documents', DocumentViewSet, basename='bot-documents')

documents_router = NestedSimpleRouter(bots_router, r'documents', lookup='document')
documents_router.register(r'chunks', DocumentChunkViewSet, basename='document-chunks')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(bots_router.urls)),
    path('', include(documents_router.urls)),
]
