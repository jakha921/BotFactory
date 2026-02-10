"""
Views for knowledge app.
DocumentViewSet and DocumentChunkViewSet for knowledge base management.
"""
import threading
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.knowledge.models import Document, DocumentChunk, TextSnippet
from apps.bots.models import Bot
from apps.knowledge.serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    DocumentChunkSerializer,
    TextSnippetSerializer,
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
        # NestedSimpleRouter passes parent lookup as `<lookup>_pk`, i.e. `bot_pk`
        bot_id = self.kwargs.get('bot_pk') or self.kwargs.get('bot_id')
        if bot_id:
            bot = get_object_or_404(Bot, id=bot_id, owner=self.request.user)
            return Document.objects.filter(bot=bot)
        return Document.objects.none()
    
    def get_serializer_class(self):
        """Use different serializer for create (file upload)."""
        if self.action == 'create':
            return DocumentUploadSerializer
        return DocumentSerializer
    
    def create(self, request, *args, **kwargs):
        """Upload a document for a bot."""
        bot_id = kwargs.get('bot_pk') or kwargs.get('bot_id')
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
    
    def list(self, request, *args, **kwargs):
        """List documents for a bot."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DocumentChunkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document chunks.

    list: GET /api/v1/documents/{document_id}/chunks/ - List chunks for a document
    update: PATCH /api/v1/chunks/{id}/ - Update chunk text
    regenerate: POST /api/v1/chunks/{id}/regenerate/ - Regenerate embedding
    """
    permission_classes = [IsAuthenticated]  # DocumentChunk doesn't have owner field

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

    def update(self, request, *args, **kwargs):
        """Update chunk text and regenerate embedding."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        document = get_object_or_404(Document, id=instance.document.id, bot__owner=self.request.user)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # If text changed, regenerate embedding
        if 'text' in serializer.validated_data and serializer.validated_data['text'] != instance.text:
            chunk = serializer.save()
            # Regenerate embedding for the updated chunk
            from .services import generate_embedding_for_chunk
            generate_embedding_for_chunk(chunk)
        else:
            serializer.save()

        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def regenerate(self, request, *args, **kwargs):
        """Regenerate embedding for a chunk."""
        instance = self.get_object()
        document = get_object_or_404(Document, id=instance.document.id, bot__owner=self.request.user)

        from .services import generate_embedding_for_chunk
        try:
            generate_embedding_for_chunk(instance)
            return Response({
                'success': True,
                'message': 'Embedding regenerated successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to regenerate embedding: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class TextSnippetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing text snippets.
    
    list: GET /api/v1/snippets/?bot_id={bot_id} - List snippets for a bot
    create: POST /api/v1/snippets/ - Create a snippet
    update: PATCH /api/v1/snippets/{id}/ - Update a snippet
    destroy: DELETE /api/v1/snippets/{id}/ - Delete a snippet
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TextSnippetSerializer
    
    def get_queryset(self):
        """Filter snippets by bot and ensure user owns the bot."""
        bot_id = self.request.query_params.get('bot_id')
        if bot_id:
            bot = get_object_or_404(Bot, id=bot_id, owner=self.request.user)
            return TextSnippet.objects.filter(bot=bot)
        # If no bot_id, return empty queryset
        return TextSnippet.objects.none()
    
    def perform_create(self, serializer):
        """Create a snippet and ensure user owns the bot."""
        bot = serializer.validated_data.get("bot")
        if not bot:
            raise serializers.ValidationError({'bot': 'This field is required.'})
        
        # Ensure the authenticated user owns the bot referenced by this snippet
        try:
            Bot.objects.get(id=bot.id, owner=self.request.user)
        except Bot.DoesNotExist:
            raise serializers.ValidationError({
                'bot': 'Bot not found or you do not have permission to access it.'
            })
        
        # `bot` instance is already in validated_data, so just save
        serializer.save()
    
    def perform_update(self, serializer):
        """Update a snippet and ensure user owns the bot."""
        instance = self.get_object()
        # Ensure user owns the bot
        get_object_or_404(Bot, id=instance.bot.id, owner=self.request.user)
        
        # If bot is being changed, verify ownership of new bot
        if 'bot' in serializer.validated_data:
            new_bot = serializer.validated_data.get('bot')
            get_object_or_404(Bot, id=new_bot.id, owner=self.request.user)
        
        serializer.save()
