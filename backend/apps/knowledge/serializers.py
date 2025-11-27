"""
Serializers for knowledge app.
"""
from rest_framework import serializers
from apps.knowledge.models import Document, TextSnippet


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    type = serializers.CharField(read_only=True)
    size = serializers.CharField()  # Convert to human-readable format in frontend
    uploadDate = serializers.DateTimeField(source='upload_date', read_only=True)
    botId = serializers.UUIDField(source='bot.id', read_only=True)
    
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
        read_only_fields = ['id', 'upload_date', 'status']
    
    def to_representation(self, instance):
        """Customize representation to match frontend types."""
        data = super().to_representation(instance)
        # Convert size to string format (bytes -> KB/MB)
        size_bytes = instance.size
        if size_bytes >= 1024 * 1024:
            size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
        elif size_bytes >= 1024:
            size_str = f"{size_bytes / 1024:.2f} KB"
        else:
            size_str = f"{size_bytes} B"
        
        return {
            'id': str(data['id']),
            'name': data['name'],
            'type': data['type'],
            'size': size_str,
            'status': data['status'],
            'uploadDate': data.get('uploadDate'),
            'botId': str(data['botId']),
        }


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for document upload."""
    file = serializers.FileField()
    
    class Meta:
        model = Document
        fields = ['file', 'name']
    
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
    
    def create(self, validated_data):
        """Create document from uploaded file."""
        file = validated_data.pop('file')
        bot = validated_data.get('bot')
        
        # Determine file type from extension
        file_extension = file.name.lower().split('.')[-1]
        type_mapping = {
            'pdf': 'pdf',
            'txt': 'txt',
            'docx': 'docx',
            'md': 'md',
        }
        doc_type = type_mapping.get(file_extension, 'txt')
        
        # Use provided name or filename
        name = validated_data.get('name', file.name)
        
        document = Document.objects.create(
            bot=bot,
            name=name,
            file=file,
            type=doc_type,
            size=file.size,
            status='indexing'
        )
        
        # TODO: Process document asynchronously (Celery task)
        # For now, mark as ready
        document.status = 'ready'
        document.save()
        
        return document


class TextSnippetSerializer(serializers.ModelSerializer):
    """Serializer for TextSnippet model."""
    botId = serializers.UUIDField(source='bot.id', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    
    class Meta:
        model = TextSnippet
        fields = [
            'id',
            'title',
            'content',
            'tags',
            'botId',
            'updatedAt',
        ]
        read_only_fields = ['id', 'updated_at']
    
    def to_representation(self, instance):
        """Customize representation to match frontend types."""
        data = super().to_representation(instance)
        return {
            'id': str(data['id']),
            'title': data['title'],
            'content': data['content'],
            'tags': data.get('tags', []),
            'botId': str(data['botId']),
            'updatedAt': data.get('updatedAt'),
        }


class TextSnippetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating TextSnippet."""
    
    class Meta:
        model = TextSnippet
        fields = [
            'title',
            'content',
            'tags',
            'bot',
        ]

