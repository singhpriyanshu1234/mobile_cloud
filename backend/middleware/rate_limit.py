"""Gateway concern: simple in-memory sliding-window rate limiter.

- General API: 100 req/min per IP (config RATE_LIMIT_PER_MINUTE).
- Login endpoint: 10 req/min per IP (config LOGIN_RATE_LIMIT_PER_MINUTE).

NOT suitable for multi-instance production: each process has its own
memory. Production would use Redis with atomic counters / token bucket.
"""
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.utils import config

_buckets: dict[str, list[float]] = defaultdict(list)
_WINDOW = 60.0


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _allowed(key: str, limit: int, now: float) -> bool:
    hits = _buckets[key]
    cutoff = now - _WINDOW
    # Prune old entries in place.
    _buckets[key] = [t for t in hits if t > cutoff]
    if len(_buckets[key]) >= limit:
        return False
    _buckets[key].append(now)
    return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only rate-limit API traffic; let the frontend HTML through freely.
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        now = time.monotonic()
        ip = _client_ip(request)
        if request.url.path == "/api/auth/login":
            key, limit = f"login:{ip}", config.LOGIN_RATE_LIMIT_PER_MINUTE
        else:
            key, limit = f"api:{ip}", config.RATE_LIMIT_PER_MINUTE
        if not _allowed(key, limit, now):
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {"code": "RATE_LIMITED", "message": "Too many requests. Slow down and retry."},
                },
            )
        return await call_next(request)
