"""
Cryptographic stuff needed for Authentication
"""
from base64 import urlsafe_b64encode

from cryptography.fernet import Fernet
from django.conf import settings


class SymmetricCrypt:
    """
    Symmetric Encryption and Decryption using the configured Django Secret
    """

    def __init__(self):
        """
        Initialize Fernet Cipher Suite
        """
        self.cipher_suite = Fernet(urlsafe_b64encode(settings.SECRET_KEY.encode('utf-8')[:32]))

    def encrypt(self, to_be_encrypted: bytes) -> bytes:
        """
        Encrypt with Fernet, using the configured Django Secret
        """
        return self.cipher_suite.encrypt(to_be_encrypted)

    def decrypt(self, to_be_decrypted: bytes) -> bytes:
        """
        Decrypt with Fernet, using the configured Django Secret
        """
        return self.cipher_suite.decrypt(to_be_decrypted)
