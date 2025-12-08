"""
Custom middleware for development.
"""
import re
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


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

