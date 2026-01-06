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


class TenantFilterMixin:
    """
    Mixin that filters queryset by tenant (request.tenant).

    Provides tenant isolation at the data level.
    Assumes the model has a `tenant` field or can be filtered through related models.
    """

    def get_queryset(self):
        """
        Filter queryset to only include objects for the current tenant.
        """
        queryset = super().get_queryset()

        # Check if model has direct tenant field
        if hasattr(queryset.model, 'tenant'):
            if self.request.tenant:
                return queryset.filter(tenant=self.request.tenant)
            # If no tenant, return empty queryset for security
            return queryset.none()

        # Check if model has owner field with tenant relationship
        if hasattr(queryset.model, 'owner'):
            if self.request.user.is_authenticated:
                return queryset.filter(owner__tenant=self.request.user.tenant)
            return queryset.none()

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


class TenantViewSetMixin(TenantFilterMixin):
    """
    Mixin that provides tenant filtering and automatic tenant assignment.
    Use this for ViewSets that need tenant isolation.
    """
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        """
        Automatically set the tenant when creating.
        """
        if hasattr(serializer.Meta.model, 'tenant') and self.request.tenant:
            serializer.save(tenant=self.request.tenant)
        elif hasattr(serializer.Meta.model, 'owner'):
            serializer.save(owner=self.request.user)
        else:
            serializer.save()

