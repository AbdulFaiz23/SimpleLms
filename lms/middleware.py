import json
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

class RateLimitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/api/docs') or request.path.startswith('/static/'):
            return None

        # Determine identifier: user ID if authenticated, else IP address
        if hasattr(request, 'auth') and request.auth:
            identifier = f"user_{request.auth.id}"
        elif request.user.is_authenticated:
            identifier = f"user_{request.user.id}"
        else:
            identifier = request.META.get('REMOTE_ADDR', 'unknown_ip')

        import time
        # Get current minute window
        minute_window = int(time.time() // 60)
        cache_key = f"ratelimit:{identifier}:{minute_window}"

        # Increment counter in Redis
        try:
            try:
                requests = cache.incr(cache_key)
            except ValueError:
                cache.set(cache_key, 1, timeout=60)
                requests = 1

            if requests > 60:
                return JsonResponse({"detail": "Rate limit exceeded, try again later"}, status=429)
        except Exception as e:
            # If Redis fails, we should not block the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"RateLimitMiddleware error: {e}")
            pass
        
        return None
