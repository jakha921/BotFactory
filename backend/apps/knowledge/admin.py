"""
Admin configuration for knowledge app.
"""
from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.knowledge.models import Document, TextSnippet


@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    """Admin interface for Document model."""
    
    list_display = [
        'name',
        'bot',
        'type',
        'status',
        'size',
        'upload_date',
    ]
    list_filter = [
        'type',
        'status',
        'upload_date',
    ]
    search_fields = [
        'name',
        'bot__name',
    ]
    ordering = ['-upload_date']
    readonly_fields = ['id', 'upload_date', 'size']


@admin.register(TextSnippet)
class TextSnippetAdmin(ModelAdmin):
    """Admin interface for TextSnippet model."""
    
    list_display = [
        'title',
        'bot',
        'updated_at',
    ]
    list_filter = [
        'updated_at',
    ]
    search_fields = [
        'title',
        'content',
        'bot__name',
    ]
    ordering = ['-updated_at']
    readonly_fields = ['id', 'updated_at']
