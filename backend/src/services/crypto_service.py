"""Symmetric encryption for secrets stored in MongoDB (user API keys)."""

from cryptography.fernet import Fernet, InvalidToken

from src.config import settings

_fernet = Fernet(settings.ENCRYPTION_KEY.encode())


class DecryptionError(Exception):
    pass


def encrypt(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _fernet.decrypt(token.encode()).decode()
    except InvalidToken as error:
        raise DecryptionError("A stored key could not be decrypted. Save it again in Settings.") from error
