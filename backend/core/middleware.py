"""
Custom middleware for development.
"""
import re
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to resolve tenant from authenticated user or headers.

    Sets request.tenant for tenant-aware filtering throughout the app.
    """

    def process_request(self, request):
        """Resolve tenant and attach to request."""
        # If user is authenticated, get their tenant
        if request.user.is_authenticated and hasattr(request.user, 'tenant'):
            request.tenant = request.user.tenant
            return None

        # For API requests, check for tenant slug in header
        # This allows service-to-service communication with tenant context
        tenant_slug = request.META.get('HTTP_X_TENANT_SLUG')
        if tenant_slug:
            try:
                from apps.accounts.models import Tenant
                request.tenant = Tenant.objects.get(slug=tenant_slug)
            except Tenant.DoesNotExist:
                logger.warning(f"Tenant not found for slug: {tenant_slug}")
                request.tenant = None
        else:
            request.tenant = None

        return None


class NgrokHostMiddleware(MiddlewareMixin):
    """
    Middleware to allow ngrok domains in development.
    
    This middleware bypasses ALLOWED_HOSTS check for ngrok domains
    when DEBUG=True. Only use in development!
    """
    
    def process_request(self, request):
        """Process request and allow ngrok domains."""
        if not settings.DEBUG:
            # Only in development mode
            return None
        
        host = request.get_host().split(':')[0]  # Remove port if present
        
        # Check if it's an ngrok domain
        ngrok_patterns = [
            r'.+\.ngrok\.io$',
            r'.+\.ngrok-free\.app$',
            r'.+\.ngrok\.app$',
        ]
        
        for pattern in ngrok_patterns:
            if re.match(pattern, host):
                logger.debug(f"Allowing ngrok domain: {host}")
                # Set a flag to bypass ALLOWED_HOSTS check
                request._ngrok_bypass = True
                break
        
        return None


class DisallowedHostBypassMiddleware(MiddlewareMixin):
    """
    Middleware to bypass ALLOWED_HOSTS check for ngrok domains.
    
    This middleware adds ngrok domains to ALLOWED_HOSTS dynamically
    BEFORE SecurityMiddleware checks them.
    
    Only works in development (DEBUG=True).
    """
    
    def __init__(self, get_response=None):
        """Initialize middleware (compatible with both old and new style)."""
        if get_response is not None:
            self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Allow ngrok requests by adding host to ALLOWED_HOSTS.
        
        This runs BEFORE SecurityMiddleware (must be first in MIDDLEWARE list),
        so the host will be allowed.
        """
        if not settings.DEBUG:
            return None
        
        try:
            host = request.get_host().split(':')[0]  # Remove port if present
            
            # Check if it's an ngrok domain
            ngrok_patterns = [
                r'.+\.ngrok\.io$',
                r'.+\.ngrok-free\.app$',
                r'.+\.ngrok\.app$',
            ]
            
            for pattern in ngrok_patterns:
                if re.match(pattern, host):
                    # Add to ALLOWED_HOSTS if not already there
                    if host not in settings.ALLOWED_HOSTS:
                        settings.ALLOWED_HOSTS.append(host)
                        logger.info(f"Added ngrok host to ALLOWED_HOSTS: {host}")
                    break
        except Exception as e:
            logger.error(f"Error in DisallowedHostBypassMiddleware: {e}", exc_info=True)
        
        return None


import time

request_logger = logging.getLogger('django.request')


class APIRequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging API requests with timing information.
    Logs request method, path, response status, and duration.
    """
    
    def process_request(self, request):
        """Store request start time."""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log request details after processing."""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Only log API requests
            if request.path.startswith('/api/'):
                request_logger.info(
                    f"API Request: {request.method} {request.path} "
                    f"Status:{response.status_code} "
                    f"Duration:{duration*1000:.2f}ms "
                    f"User:{getattr(request.user, 'email', 'Anonymous')}",
                    extra={
                        'method': request.method,
                        'path': request.path,
                        'status_code': response.status_code,
                        'duration_ms': round(duration * 1000, 2),
                        'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                        'ip': self.get_client_ip(request),
                    }
                )
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
