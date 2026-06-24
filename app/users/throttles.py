"""Custom throttle classes for rate-limiting API endpoints."""

from rest_framework.throttling import SimpleRateThrottle


class LoginThrottle(SimpleRateThrottle):
    """Rate-limit login attempts for unauthenticated users."""

    scope = "login"

    def get_cache_key(self, request, view):
        """Generate cache key using client IP for anonymous users only."""
        if request.user.is_authenticated:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class PasswordResetThrottle(SimpleRateThrottle):
    """Rate-limit password reset requests."""

    scope = "password_reset"

    def get_cache_key(self, request, view):
        """Generate cache key using client IP."""
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class ActivateThrottle(SimpleRateThrottle):
    """Rate-limit activation attempts to prevent brute-force."""

    scope = "activate"

    def get_cache_key(self, request, view):
        """Generate cache key using client IP."""
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class VerificationCodeThrottle(SimpleRateThrottle):
    """Rate-limit verification code sending requests."""

    scope = "verification_code"

    def get_cache_key(self, request, view):
        email = request.data.get("email", "")
        return self.cache_format % {
            "scope": self.scope,
            "ident": email or self.get_ident(request),
        }
