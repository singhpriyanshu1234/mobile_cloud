"""Gateway concern: per-request logging with ID + timing.

Logs method, path, status code, duration. Never logs bodies,
passwords, or tokens (only metadata).
"""
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("gateway.access")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "rid=%s %s %s -> 500 %.1fms",
                request_id, request.method, request.url.path, elapsed_ms,
            )
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "rid=%s %s %s -> %s %.1fms",
            request_id, request.method, request.url.path,
            response.status_code, elapsed_ms,
        )
        return response
