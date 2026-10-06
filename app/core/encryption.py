"""
========================================================================================
Symmetric Encryption Utility (encryption.py)
========================================================================================

Provides reversible encryption for secrets that must be recoverd in 
plaintext later (e.g. per-user SMTP passwords) -- unlike password hashing 
(security.py), which is one-way and never needs the orignal value backl.
"""

from cryptography.fernet import Fernet


from app.core.config import ENCRYPTION_KEY


_fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt_value(plain_text:str)-> str:
    """
    Encrypts a plaintext string (e.g. an SMTP app password) into a 
    storable, reversible ciphertext string.
    """

    return _fernet.encrypt(plain_text.encode()).decode()

def decrypt_value(encypted_text:str) -> str:
    """
    Decrpyt a ciphertext string produced by encrypt_value() backs to 
    its orignal palintext
    """
    return _fernet.decrypt(encypted_text.encode()).decode()


