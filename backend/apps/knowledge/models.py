import uuid
from django.db import models
from pgvector.django import VectorField
from apps.bots.models import Bot
from django.utils import timezone

class Document(models.Model):
    """Document model for knowledge base files."""
    
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('indexing', 'Indexing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ]
    
    TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('txt', 'Text'),
        ('docx', 'Word Document'),
        ('md', 'Markdown'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=255, default='', blank=True, help_text="Display name of the document")
    file = models.FileField(upload_to='documents/')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='txt', help_text="File type")
    size = models.BigIntegerField(default=0, help_text="File size in bytes")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading', help_text="Processing status")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['bot', 'status']),
            models.Index(fields=['uploaded_at']),
        ]

    def __str__(self):
        return self.name or self.file.name
    
    def save(self, *args, **kwargs):
        """Auto-populate name and size from file if not set."""
        if self.file:
            if not self.name:
                self.name = self.file.name.split('/')[-1]
            if not self.size and hasattr(self.file, 'size'):
                self.size = self.file.size
            # Auto-detect type from extension
            if not self.type or self.type == 'txt':
                ext = self.file.name.split('.')[-1].lower()
                type_map = {'pdf': 'pdf', 'txt': 'txt', 'docx': 'docx', 'md': 'md'}
                self.type = type_map.get(ext, 'txt')
        super().save(*args, **kwargs)

class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    text = models.TextField()
    embedding = VectorField(dimensions=768)

    def __str__(self):
        return f"Chunk {self.id} for {self.document.file.name}"


class TextSnippet(models.Model):
    """Text snippet for knowledge base."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='snippets')
    title = models.CharField(max_length=255)
    content = models.TextField()
    tags = models.JSONField(default=list, blank=True)
    embedding = VectorField(dimensions=768, null=True, blank=True, help_text="Embedding vector for RAG search")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['bot', 'updated_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.bot.name})"
    
    def save(self, *args, **kwargs):
        """Override save to generate embedding if content changed."""
        # Only generate embedding if content changed and embedding is None
        if self.pk:
            old_instance = TextSnippet.objects.get(pk=self.pk)
            if old_instance.content == self.content and self.embedding is not None:
                # Content unchanged, keep existing embedding
                super().save(*args, **kwargs)
                return
        
        # Generate embedding if content exists
        if self.content and not self.embedding:
            try:
                from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
                embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                # Combine title and content for embedding
                text_to_embed = f"{self.title}\n{self.content}"
                self.embedding = embeddings.embed_query(text_to_embed)
            except Exception as e:
                # Log error but don't fail save
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to generate embedding for TextSnippet {self.id}: {str(e)}")
        
        super().save(*args, **kwargs)
