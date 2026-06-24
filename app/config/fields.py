"""
Custom Django model fields for v2man project.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


class EncryptedCharField(models.CharField):
    """CharField that transparently encrypts and decrypts values."""

    description = "加密存储的字符字段（透明加解密）"

    def __init__(self, *args, max_length: int = 512, **kwargs) -> None:
        """Initialize with a default max_length of 512."""
        kwargs.setdefault("max_length", max_length)
        super().__init__(*args, **kwargs)

    @staticmethod
    def _fernet() -> Fernet:
        """Return a Fernet instance keyed from Django SECRET_KEY."""
        key = base64.urlsafe_b64encode(
            hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        )
        return Fernet(key)

    @staticmethod
    def _is_encrypted(value: str) -> bool:
        """Check if a value is already encrypted."""
        if not value:
            return False
        try:
            EncryptedCharField._fernet().decrypt(value.encode())
            return True
        except InvalidToken:
            return False

    def get_prep_value(self, value: str | None) -> str | None:
        """Encrypt value before saving to the database."""
        if value is None or value == "":
            return value
        if self._is_encrypted(value):
            return value
        return self._fernet().encrypt(value.encode()).decode()

    def from_db_value(
        self, value: str | None, expression, connection
    ) -> str | None:  # type: ignore[override]
        """Decrypt value when loading from the database."""
        if value is None:
            return value
        if self._is_encrypted(value):
            return self._fernet().decrypt(value.encode()).decode()
        return value

    def to_python(self, value: str | None) -> str | None:
        """Decrypt value during deserialization."""
        if value is None:
            return value
        if self._is_encrypted(value):
            return self._fernet().decrypt(value.encode()).decode()
        return value
