"""Custom authentication backends for v2man."""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class UsernameOrEmailBackend(ModelBackend):
    """Authenticate by username or email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.filter(email=username).first()

        if user and user.check_password(password):
            return user
        return None
