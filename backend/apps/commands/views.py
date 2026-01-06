"""
Views for commands app.
"""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from core.mixins import OwnerFilterMixin
from apps.commands.models import Command
from apps.commands.serializers import CommandSerializer


class CommandViewSet(OwnerFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing bot commands.

    list: GET /api/v1/commands/ - List all commands for user's bots
    create: POST /api/v1/commands/ - Create a new command
    retrieve: GET /api/v1/commands/{id}/ - Get command details
    update: PUT /api/v1/commands/{id}/ - Full update
    partial_update: PATCH /api/v1/commands/{id}/ - Partial update
    destroy: DELETE /api/v1/commands/{id}/ - Delete command
    """
    serializer_class = CommandSerializer
    queryset = Command.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['bot', 'response_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['priority', 'name', 'created_at']
    ordering = ['-priority', 'name']
