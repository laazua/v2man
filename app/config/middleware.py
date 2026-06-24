"""
Middleware for v2man project.
"""

import logging
import time
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

api_logger: logging.Logger = logging.getLogger("api.requests")


class APILogMiddleware:
    """Middleware that logs API request details."""

    def __init__(self, get_response: Callable) -> None:
        """Initialize middleware with the next response handler."""
        self.get_response = get_response

    def __call__(
        self, request: HttpRequest
    ) -> HttpResponse:  # type: ignore[override]
        """Log request method, path, user, status code, and duration."""
        start: float = time.time()
        response = self.get_response(request)
        duration: float = time.time() - start
        user_id = (
            getattr(request.user, "id", "anon")
            if hasattr(request, "user")
            else "pre-auth"
        )

        api_logger.info(
            "%s %s %s %s %.3fs",
            request.method,
            request.path,
            user_id,
            response.status_code,
            duration,
        )
        return response
