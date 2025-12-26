"""
Serializers for knowledge app.
"""
from rest_framework import serializers

from apps.bots.models import Bot
from apps.knowledge.models import Document, DocumentChunk, TextSnippet


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    botId = serializers.UUIDField(source='bot.id', read_only=True)
    uploadDate = serializers.DateTimeField(source='uploaded_at', read_only=True)
    name = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'name',
            'type',
            'size',
            'status',
            'uploadDate',
            'botId',
        ]
        read_only_fields = ['id', 'uploaded_at']
    
    def get_name(self, obj):
        """Extract filename from file path."""
        if obj.file:
            return obj.file.name.split('/')[-1]
        return ''
    
    def get_type(self, obj):
        """Extract file type from filename."""
        if obj.file:
            ext = obj.file.name.lower().split('.')[-1]
            if ext == 'pdf':
                return 'pdf'
            elif ext == 'txt':
                return 'txt'
            elif ext in ['doc', 'docx']:
                return 'docx'
            elif ext == 'md':
                return 'md'
        return 'txt'
    
    def get_size(self, obj):
        """Get file size as formatted string."""
        if obj.file and hasattr(obj.file, 'size'):
            size = obj.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "0 B"
    
    def get_status(self, obj):
        """Determine document status based on chunks."""
        if hasattr(obj, 'chunks') and obj.chunks.exists():
            return 'ready'
        # Check if document was just uploaded (no chunks yet)
        return 'indexing'

class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for document upload."""
    file = serializers.FileField()
    
    class Meta:
        model = Document
        fields = ['file']

    def validate_file(self, value):
        """Validate uploaded file."""
        # Check file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError("File size exceeds 50MB limit.")
        
        # Check file type
        allowed_extensions = ['.pdf', '.txt', '.docx', '.md']
        file_extension = value.name.lower().split('.')[-1]
        if file_extension not in [ext.lstrip('.') for ext in allowed_extensions]:
            raise serializers.ValidationError(
                f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return value

class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for DocumentChunk model."""
    documentId = serializers.UUIDField(source='document.id', read_only=True)
    
    class Meta:
        model = DocumentChunk
        fields = [
            'id',
            'text',
            'documentId',
        ]
        read_only_fields = ['id']


class TextSnippetSerializer(serializers.ModelSerializer):
    """Serializer for TextSnippet model."""

    # Write-only bot field accepts bot UUID and resolves to Bot instance
    bot = serializers.PrimaryKeyRelatedField(
        queryset=Bot.objects.all(),
        write_only=True,
        required=True,
    )
    # Read-only botId field exposed to frontend
    botId = serializers.UUIDField(source="bot.id", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = TextSnippet
        fields = [
            "id",
            "title",
            "content",
            "tags",
            "bot",
            "botId",
            "updatedAt",
        ]
        read_only_fields = ["id", "updated_at"]
