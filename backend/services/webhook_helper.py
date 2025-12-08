"""
Helper utilities for webhook operations.
"""
import json
import logging
from typing import Optional, Dict, Any
from django.http import HttpRequest

logger = logging.getLogger(__name__)


async def read_request_body(request: HttpRequest) -> bytes:
    """
    Read request body from Django async view.
    
    Supports both async and sync request reading methods.
    
    Args:
        request: Django HTTP request
        
    Returns:
        Request body as bytes
    """
    body_bytes = b''
    
    # Try async read methods (Django 5.0+)
    if hasattr(request, 'aread'):
        try:
            body_bytes = await request.aread()
        except Exception as e:
            logger.debug(f"aread() failed: {e}, trying fallback methods")
    
    # Fallback to sync methods
    if not body_bytes:
        if hasattr(request, 'body'):
            body_bytes = request.body if isinstance(request.body, bytes) else b''
        elif hasattr(request, 'read'):
            try:
                body_bytes = request.read()
            except Exception as e:
                logger.debug(f"read() failed: {e}")
    
    return body_bytes


async def parse_webhook_update(request: HttpRequest) -> Optional[Dict[str, Any]]:
    """
    Parse Telegram webhook update from request body.
    
    Args:
        request: Django HTTP request
        
    Returns:
        Parsed update data as dict, or None if parsing failed
    """
    try:
        body_bytes = await read_request_body(request)
        
        if not body_bytes:
            logger.error("Empty request body")
            return None
        
        update_data = json.loads(body_bytes.decode('utf-8'))
        return update_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook body: {e}")
        return None
    except UnicodeDecodeError as e:
        logger.error(f"Failed to decode request body: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing webhook body: {e}", exc_info=True)
        return None

