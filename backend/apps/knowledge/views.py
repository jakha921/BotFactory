"""
Views for knowledge app.
DocumentViewSet and TextSnippetViewSet for knowledge base management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.knowledge.models import Document, TextSnippet
from apps.bots.models import Bot
from apps.knowledge.serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    TextSnippetSerializer,
    TextSnippetCreateSerializer,
)
from core.permissions import IsOwnerOrReadOnly


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing documents.
    
    list: GET /api/v1/bots/{bot_id}/documents/ - List documents for a bot
    create: POST /api/v1/bots/{bot_id}/documents/ - Upload a document
    destroy: DELETE /api/v1/documents/{id}/ - Delete a document
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer
    
    def get_queryset(self):
        """Filter documents by bot and ensure user owns the bot."""
        bot_id = self.kwargs.get('bot_id')
        if bot_id:
            bot = get_object_or_404(Bot, id=bot_id, owner=self.request.user)
            return Document.objects.filter(bot=bot)
        return Document.objects.none()
    
    def get_serializer_class(self):
        """Use different serializer for create (file upload)."""
        if self.action == 'create':
            return DocumentUploadSerializer
        return DocumentSerializer
    
    def create(self, request, bot_id=None):
        """Upload a document for a bot."""
        bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
        
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save(bot=bot)
        
        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )
    
    def list(self, request, bot_id=None):
        """List documents for a bot."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TextSnippetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing text snippets.
    
    list: GET /api/v1/bots/{bot_id}/snippets/ - List snippets for a bot
    create: POST /api/v1/snippets/ - Create a snippet
    destroy: DELETE /api/v1/snippets/{id}/ - Delete a snippet
    """
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = TextSnippetSerializer
    
    def get_queryset(self):
        """Filter snippets by bot and ensure user owns the bot."""
        bot_id = self.request.query_params.get('bot_id') or self.kwargs.get('bot_id')
        if bot_id:
            bot = get_object_or_404(Bot, id=bot_id, owner=self.request.user)
            return TextSnippet.objects.filter(bot=bot)
        return TextSnippet.objects.none()
    
    def get_serializer_class(self):
        """Use different serializer for create."""
        if self.action == 'create':
            return TextSnippetCreateSerializer
        return TextSnippetSerializer
    
    def perform_create(self, serializer):
        """Ensure bot belongs to user."""
        bot_id = serializer.validated_data.get('bot').id
        bot = get_object_or_404(Bot, id=bot_id, owner=self.request.user)
        serializer.save(bot=bot)
    
    def list(self, request, bot_id=None):
        """List snippets for a bot."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
