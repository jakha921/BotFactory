"""
Serializers for knowledge app.
"""
from rest_framework import serializers
from apps.knowledge.models import Document, DocumentChunk


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    botId = serializers.UUIDField(source='bot.id', read_only=True)
    uploadedAt = serializers.DateTimeField(source='uploaded_at', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id',
            'file',
            'uploadedAt',
            'botId',
        ]
        read_only_fields = ['id', 'uploaded_at']

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
