"""
Security middleware: HTTPS redirect, Host allowlist, Origin/CSRF checks, security headers.
"""
from __future__ import annotations

from typing import Callable, Iterable
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from app.core.config import settings

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def _parse_host(value: str) -> str:
    return value.split(":")[0].strip().lower()


def _allowed_hosts() -> list[str]:
    raw = (settings.ALLOWED_HOSTS or "").strip()
    if not raw or raw == "*":
        return []
    return [_parse_host(h) for h in raw.split(",") if h.strip()]


def _cors_origins() -> set[str]:
    return {o.rstrip("/") for o in settings.cors_origins_list if o and o != "*"}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Never interfere with CORS preflight
        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        # Strict checks only when production AND DEBUG=false (live deploy)
        harden = settings.is_production and not settings.DEBUG

        # Force HTTPS behind TLS terminator (X-Forwarded-Proto) or direct TLS
        if settings.FORCE_HTTPS and harden:
            proto = request.headers.get("x-forwarded-proto", request.url.scheme).lower()
            if proto != "https":
                url = request.url.replace(scheme="https")
                return RedirectResponse(str(url), status_code=308)

        # Trusted hosts (local 127.0.0.1 / localhost always allowed)
        hosts = _allowed_hosts()
        if hosts and harden:
            host = _parse_host(request.headers.get("host", ""))
            if host and host not in hosts and host not in {"localhost", "127.0.0.1"}:
                return JSONResponse({"detail": "Invalid host header"}, status_code=400)

        # CSRF / cross-origin: Origin/Referer match for cookie-authenticated mutating requests
        if (
            settings.CSRF_PROTECT
            and harden
            and request.method.upper() not in SAFE_METHODS
            and request.cookies
        ):
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            allowed = _cors_origins()
            ok = False
            if origin:
                ok = origin.rstrip("/") in allowed
            elif referer:
                try:
                    ref_origin = f"{urlparse(referer).scheme}://{urlparse(referer).netloc}"
                    ok = ref_origin.rstrip("/") in allowed
                except Exception:
                    ok = False
            if not ok:
                has_auth_cookie = bool(
                    request.cookies.get(settings.COOKIE_ACCESS_TOKEN_NAME)
                    or request.cookies.get(settings.COOKIE_REFRESH_TOKEN_NAME)
                )
                if has_auth_cookie:
                    return JSONResponse(
                        {"detail": "CSRF validation failed: invalid Origin"},
                        status_code=403,
                    )

        response = await call_next(request)

        if not settings.SECURITY_HEADERS_ENABLED:
            return response

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), payment=()",
        )
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("X-XSS-Protection", "0")  # modern browsers use CSP

        if settings.FORCE_HTTPS or (settings.is_production and settings.COOKIE_SECURE):
            response.headers.setdefault(
                "Strict-Transport-Security",
                f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains",
            )

        # Basic CSP — allow self + configured frontend/API + Google Fonts used by storefront
        if settings.CONTENT_SECURITY_POLICY:
            response.headers.setdefault("Content-Security-Policy", settings.CONTENT_SECURITY_POLICY)

        return response


def iter_rate_limit_keys(request: Request) -> Iterable[str]:
    client = request.client.host if request.client else "unknown"
    yield f"ip:{client}"
