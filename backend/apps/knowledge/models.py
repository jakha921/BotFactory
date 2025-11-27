"""
Knowledge models for Bot Factory.
Document and TextSnippet models for knowledge base.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
# from django.contrib.postgres.fields import ArrayField  # PostgreSQL specific


def document_upload_path(instance, filename):
    """Generate upload path for documents."""
    return f'documents/{instance.bot_id}/{filename}'


class Document(models.Model):
    """
    Document model for storing uploaded files (PDF, TXT, DOCX, MD).
    
    Fields according to frontend/types.ts:
    - id: UUID primary key
    - bot: FK to Bot
    - name: Document name
    - file: FileField
    - type: Document type (pdf/txt/docx/md)
    - size: File size in bytes
    - status: Processing status (indexing/ready/error)
    - upload_date: Upload timestamp
    """
    
    TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('txt', 'Text'),
        ('docx', 'Word Document'),
        ('md', 'Markdown'),
    ]
    
    STATUS_CHOICES = [
        ('indexing', 'Indexing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey(
        'bots.Bot',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=document_upload_path)
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES
    )
    size = models.BigIntegerField()  # Size in bytes
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='indexing'
    )
    upload_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-upload_date']
        indexes = [
            models.Index(fields=['bot', 'status']),
            models.Index(fields=['upload_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.bot.name})"
    
    def __repr__(self):
        return f"<Document: {self.name} (id={self.id})>"
    
    def save(self, *args, **kwargs):
        """Save document and set size."""
        if not self.size and self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)


class TextSnippet(models.Model):
    """
    TextSnippet model for storing text snippets with tags.
    
    Fields according to frontend/types.ts:
    - id: UUID primary key
    - bot: FK to Bot
    - title: Snippet title
    - content: Snippet content
    - tags: Array of tags (PostgreSQL ArrayField)
    - updated_at: Last update timestamp
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey(
        'bots.Bot',
        on_delete=models.CASCADE,
        related_name='snippets'
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    # tags = ArrayField(...)  # PostgreSQL specific, using JSONField for compatibility
    tags = models.JSONField(default=list, blank=True)  # Compatible with SQLite and PostgreSQL
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Text Snippet'
        verbose_name_plural = 'Text Snippets'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['bot']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.bot.name})"
    
    def __repr__(self):
        return f"<TextSnippet: {self.title} (id={self.id})>"
