import time
import logging

api_logger = logging.getLogger('api.requests')


class APILogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = time.time() - start
        user_id = getattr(request.user, 'id', 'anon') if hasattr(request, 'user') else 'pre-auth'

        api_logger.info(
            '%s %s %s %s %.3fs',
            request.method,
            request.path,
            user_id,
            response.status_code,
            duration,
        )
        return response
