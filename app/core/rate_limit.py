"""Simple in-memory rate limiter for auth endpoints (per-process)."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status

from app.core.config import settings

_lock = Lock()
_buckets: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(
    request: Request,
    *,
    key_prefix: str,
    max_attempts: int | None = None,
    window_seconds: int | None = None,
) -> None:
    max_attempts = max_attempts if max_attempts is not None else settings.RATE_LIMIT_LOGIN_ATTEMPTS
    window_seconds = (
        window_seconds if window_seconds is not None else settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS
    )
    key = f"{key_prefix}:{_client_ip(request)}"
    now = time.monotonic()
    with _lock:
        q = _buckets[key]
        while q and now - q[0] > window_seconds:
            q.popleft()
        if len(q) >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please try again later.",
            )
        q.append(now)


def clear_rate_limit(request: Request, *, key_prefix: str) -> None:
    key = f"{key_prefix}:{_client_ip(request)}"
    with _lock:
        _buckets.pop(key, None)
