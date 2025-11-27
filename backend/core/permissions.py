"""
Custom permissions for Bot Factory API.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission that allows read-only access to all authenticated users,
    but only allows write access to the owner of the object.
    
    Assumes the model instance has an `owner` attribute.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for the owner
        return obj.owner == request.user


class IsBotOwner(permissions.BasePermission):
    """
    Permission that only allows access to the owner of the bot.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
    
    def has_permission(self, request, view):
        # For list/create actions, check if user is authenticated
        if request.method in ['POST', 'GET']:
            return request.user.is_authenticated
        return True


class IsOwner(permissions.BasePermission):
    """
    Generic permission that checks if the object belongs to the request user.
    Works for objects with an `owner` attribute.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if object has owner attribute
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        # If no owner attribute, deny access
        return False

