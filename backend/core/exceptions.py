"""
Custom exceptions and exception handlers for Bot Factory API.
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)


class CustomAPIException(APIException):
    """
    Base custom exception class for API errors.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A server error occurred.'
    default_code = 'error'
    
    def __init__(self, detail=None, code=None, status_code=None):
        if status_code:
            self.status_code = status_code
        if detail:
            self.detail = detail
        if code:
            self.default_code = code


class NotFoundError(CustomAPIException):
    """Exception for resource not found errors."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found.'
    default_code = 'not_found'


class ValidationError(CustomAPIException):
    """Exception for validation errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Validation error.'
    default_code = 'validation_error'


class PermissionError(CustomAPIException):
    """Exception for permission errors."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Permission denied.'
    default_code = 'permission_denied'


class AuthenticationError(CustomAPIException):
    """Exception for authentication errors."""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentication required.'
    default_code = 'authentication_required'


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error response format.
    
    Response format:
    {
        "error": {
            "message": "Error message",
            "code": "ERROR_CODE",
            "status": 400,
            "details": {
                "field_name": ["Error message for field"]
            }
        }
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If no response, handle Django exceptions
    if response is None:
        if isinstance(exc, Http404):
            response_data = {
                'error': {
                    'message': 'Resource not found.',
                    'code': 'not_found',
                    'status': status.HTTP_404_NOT_FOUND,
                }
            }
            response = Response(response_data, status=status.HTTP_404_NOT_FOUND)
        elif isinstance(exc, PermissionDenied):
            response_data = {
                'error': {
                    'message': 'Permission denied.',
                    'code': 'permission_denied',
                    'status': status.HTTP_403_FORBIDDEN,
                }
            }
            response = Response(response_data, status=status.HTTP_403_FORBIDDEN)
        else:
            # Log unexpected exceptions
            logger.error(f'Unhandled exception: {exc}', exc_info=True)
            response_data = {
                'error': {
                    'message': 'An unexpected error occurred.',
                    'code': 'server_error',
                    'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                }
            }
            response = Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Customize the response format
    if response is not None:
        custom_response_data = {
            'error': {
                'message': str(exc.detail) if hasattr(exc, 'detail') else 'An error occurred.',
                'code': getattr(exc, 'default_code', 'error'),
                'status': response.status_code,
            }
        }
        
        # Add field-level errors if they exist
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            # Check if it's a validation error with field details
            if any(isinstance(v, (list, dict)) for v in exc.detail.values()):
                custom_response_data['error']['details'] = exc.detail
        
        response.data = custom_response_data
        response.status_code = response.status_code
    
    return response

