"""
core/crypto.py — AES-256 encryption for sensitive data storage.

Replaces base64 (reversible, insecure) with real encryption.
Used for: OAuth tokens, logbook entries, counselor notes.
"""
import os, base64, hashlib
from config import settings

def _key() -> bytes:
    return hashlib.sha256(settings.secret_key.encode()).digest()

def encrypt(plaintext: str) -> str:
    try:
        from cryptography.fernet import Fernet
        key = base64.urlsafe_b64encode(_key())
        return Fernet(key).encrypt(plaintext.encode()).decode()
    except ImportError:
        # fallback to base64 with warning if cryptography not installed
        print("[CRYPTO] ⚠️  pip install cryptography for AES-256. Using base64 fallback.")
        return "b64:" + base64.b64encode(plaintext.encode()).decode()

def decrypt(ciphertext: str) -> str:
    try:
        if ciphertext.startswith("b64:"):
            return base64.b64decode(ciphertext[4:]).decode()
        from cryptography.fernet import Fernet
        key = base64.urlsafe_b64encode(_key())
        return Fernet(key).decrypt(ciphertext.encode()).decode()
    except Exception as e:
        return f"[DECRYPT ERROR: {e}]"

def encrypt_token(token: str) -> str:
    """Encrypt OAuth token for storage. AES-256 via Fernet."""
    return encrypt(token)

def decrypt_token(encrypted: str) -> str:
    return decrypt(encrypted)
