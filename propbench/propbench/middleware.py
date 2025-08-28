from django.contrib.sessions.middleware import SessionMiddleware as DjangoSessionMiddleware
from django.contrib.sessions.middleware import SessionInterrupted
import logging

logger = logging.getLogger(__name__)

class SafeSessionMiddleware(DjangoSessionMiddleware):
    """Session middleware that ignores SessionInterrupted to avoid 500s when a session row is removed concurrently.

    This should only be used as a pragmatic workaround for development where session deletion/race conditions
    can occur. In production, investigate root causes instead of suppressing the exception.
    """
    def process_response(self, request, response):
        try:
            return super().process_response(request, response)
        except SessionInterrupted as exc:
            # Log and swallow the exception so the user isn't blocked by a session race
            logger.warning("Ignored SessionInterrupted during request: %s", exc)
            return response
