"""
Views for knowledge app.
DocumentViewSet and DocumentChunkViewSet for knowledge base management.
"""
import threading
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.knowledge.models import Document, DocumentChunk
from apps.bots.models import Bot
from apps.knowledge.serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    DocumentChunkSerializer,
)
from core.permissions import IsOwnerOrReadOnly
from .services import process_document


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

        # Process the document in a separate thread
        thread = threading.Thread(target=process_document, args=(document,))
        thread.start()
        
        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )
    
    def list(self, request, bot_id=None):
        """List documents for a bot."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DocumentChunkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document chunks.
    
    list: GET /api/v1/documents/{document_id}/chunks/ - List chunks for a document
    """
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = DocumentChunkSerializer
    
    def get_queryset(self):
        """Filter chunks by document and ensure user owns the bot."""
        document_id = self.kwargs.get('document_id')
        if document_id:
            document = get_object_or_404(Document, id=document_id, bot__owner=self.request.user)
            return DocumentChunk.objects.filter(document=document)
        return DocumentChunk.objects.none()
    
    def list(self, request, document_id=None):
        """List chunks for a document."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
