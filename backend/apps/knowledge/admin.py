"""
Admin configuration for knowledge app.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.knowledge.models import Document, DocumentChunk, TextSnippet


@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    """Admin interface for Document model."""
    
    list_display = [
        'file',
        'bot',
        'uploaded_at',
    ]
    list_filter = [
        'uploaded_at',
    ]
    search_fields = [
        'file',
        'bot__name',
    ]
    ordering = ['-uploaded_at']
    readonly_fields = ['id', 'uploaded_at']


@admin.register(DocumentChunk)
class DocumentChunkAdmin(ModelAdmin):
    """Admin interface for DocumentChunk model."""
    
    list_display = [
        'document',
        'text',
    ]
    list_filter = [
        'document',
    ]
    search_fields = [
        'text',
    ]
    ordering = ['-document']
    readonly_fields = ['id']


@admin.register(TextSnippet)
class TextSnippetAdmin(ModelAdmin):
    """Admin interface for TextSnippet model."""
    
    list_display = [
        'title',
        'bot',
        'updated_at',
    ]
    list_filter = [
        'bot',
        'updated_at',
    ]
    search_fields = [
        'title',
        'content',
        'bot__name',
    ]
    ordering = ['-updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
