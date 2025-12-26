"""
Custom authentication classes for Bot Factory API.
"""
from rest_framework import authentication, exceptions
from apps.bots.models import BotAPIKey


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Authentication using X-API-Key header.
    """
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_API_KEY') or request.META.get('X-API-Key')
        
        if not api_key:
            return None
        
        try:
            # Find API key by trying to decrypt stored keys
            # This is not efficient for large datasets, but works for MVP
            # In production, consider using a hash-based lookup
            api_key_obj = None
            for stored_key in BotAPIKey.objects.filter(is_active=True).select_related('bot'):
                try:
                    if stored_key.verify_key(api_key):
                        api_key_obj = stored_key
                        break
                except Exception:
                    continue
            
            if not api_key_obj:
                raise exceptions.AuthenticationFailed('Invalid API key')
            
            if not api_key_obj.is_valid():
                raise exceptions.AuthenticationFailed('API key is inactive or expired')
            
            # Mark as used
            api_key_obj.mark_used()
            
            # Return bot as user (for permission checks)
            # The bot will be available as request.user
            return (api_key_obj.bot, api_key_obj)
            
        except BotAPIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def authenticate_header(self, request):
        return 'X-API-Key'

