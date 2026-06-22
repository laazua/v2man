import base64
import hashlib

from django.conf import settings
from django.db import models
from cryptography.fernet import Fernet, InvalidToken


class EncryptedCharField(models.CharField):
    description = "加密存储的字符字段（透明加解密）"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 512)
        super().__init__(*args, **kwargs)

    @staticmethod
    def _fernet():
        key = base64.urlsafe_b64encode(
            hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        )
        return Fernet(key)

    @staticmethod
    def _is_encrypted(value):
        if not value:
            return False
        try:
            EncryptedCharField._fernet().decrypt(value.encode())
            return True
        except InvalidToken:
            return False

    def get_prep_value(self, value):
        if value is None or value == '':
            return value
        if self._is_encrypted(value):
            return value
        return self._fernet().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        if self._is_encrypted(value):
            return self._fernet().decrypt(value.encode()).decode()
        return value

    def to_python(self, value):
        if value is None:
            return value
        if self._is_encrypted(value):
            return self._fernet().decrypt(value.encode()).decode()
        return value
