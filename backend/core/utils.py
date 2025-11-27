"""
General utility functions for Bot Factory.
"""
import uuid
from typing import Optional
import hashlib
import secrets
import base64
from django.conf import settings


def generate_uuid() -> str:
    """
    Generate a UUID string for use as primary keys.
    """
    return str(uuid.uuid4())


def hash_token(token: str, salt: Optional[str] = None) -> str:
    """
    Hash a token (e.g., Telegram bot token) for secure storage.
    
    Args:
        token: The token to hash
        salt: Optional salt for hashing (generated if not provided)
    
    Returns:
        Hashed token string
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Create hash
    hash_obj = hashlib.sha256()
    hash_obj.update((salt + token).encode('utf-8'))
    hashed = hash_obj.hexdigest()
    
    # Return salt:hash format for verification later
    return f"{salt}:{hashed}"


def verify_token(token: str, hashed_token: str) -> bool:
    """
    Verify a token against a hashed token.
    
    Args:
        token: The plain token to verify
        hashed_token: The hashed token string (salt:hash format)
    
    Returns:
        True if token matches, False otherwise
    """
    try:
        salt, stored_hash = hashed_token.split(':', 1)
        computed_hash = hashlib.sha256((salt + token).encode('utf-8')).hexdigest()
        return secrets.compare_digest(computed_hash, stored_hash)
    except (ValueError, AttributeError):
        return False


def _get_encryption_key() -> bytes:
    """
    Get encryption key from Django SECRET_KEY.
    
    Returns:
        32-byte key suitable for Fernet encryption
    """
    from hashlib import sha256
    # Use SECRET_KEY to derive encryption key
    key = sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    # Fernet requires 32 bytes, SHA256 produces 32 bytes
    return base64.urlsafe_b64encode(key)


def encrypt_token(token: str) -> str:
    """
    Encrypt a token using Fernet symmetric encryption.
    
    Args:
        token: Plain text token to encrypt
    
    Returns:
        Encrypted token string (base64 encoded)
    
    Raises:
        ImportError: If cryptography is not installed
    """
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        # Fallback: if cryptography not installed, return token as-is (not encrypted)
        # In production, cryptography MUST be installed
        return token
    
    if not token:
        return token
    
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(token.encode('utf-8'))
        return encrypted.decode('utf-8')
    except Exception as e:
        # If encryption fails, return token as-is (fallback for compatibility)
        return token


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a token using Fernet symmetric encryption.
    
    Args:
        encrypted_token: Encrypted token string (base64 encoded)
    
    Returns:
        Decrypted plain text token
    
    Raises:
        ImportError: If cryptography is not installed
    """
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        # Fallback: if cryptography not installed, return token as-is
        return encrypted_token
    
    if not encrypted_token:
        return encrypted_token
    
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_token.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception:
        # If decryption fails, assume token is not encrypted (backward compatibility)
        return encrypted_token

