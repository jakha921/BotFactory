"""
Reusable mixins for ViewSets.
"""
from rest_framework import viewsets
from core.permissions import IsOwnerOrReadOnly


class OwnerFilterMixin:
    """
    Mixin that filters queryset by owner (request.user).
    Assumes the model has an `owner` field.
    """
    
    def get_queryset(self):
        """
        Filter queryset to only include objects owned by the current user.
        """
        queryset = super().get_queryset()
        if hasattr(queryset.model, 'owner'):
            return queryset.filter(owner=self.request.user)
        return queryset


class OwnerCreateMixin:
    """
    Mixin that automatically sets the owner when creating an object.
    Assumes the model has an `owner` field.
    """
    
    def perform_create(self, serializer):
        """
        Automatically set the owner to the current user when creating.
        """
        if hasattr(serializer.Meta.model, 'owner'):
            serializer.save(owner=self.request.user)
        else:
            serializer.save()


class OwnerViewSetMixin(OwnerFilterMixin, OwnerCreateMixin):
    """
    Combined mixin that provides both owner filtering and automatic owner assignment.
    Use this for ViewSets that need both features.
    """
    permission_classes = [IsOwnerOrReadOnly]

