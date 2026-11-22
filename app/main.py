from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.security_middleware import SecurityHeadersMiddleware
from app.api.v1.api import api_router

# Disable OpenAPI docs only for hardened production (DEBUG=false)
_docs_url = None if (settings.is_production and not settings.DEBUG) else "/docs"
_redoc_url = None if (settings.is_production and not settings.DEBUG) else "/redoc"
_openapi_url = None if (settings.is_production and not settings.DEBUG) else f"{settings.API_V1_STR}/openapi.json"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Nepal Origin herbal products API — FastAPI, SQLAlchemy (Async), MySQL (prod).",
    version="1.0.0",
    contact={
        "name": "Nepal Origin",
        "email": settings.DEFAULT_ADMIN_EMAIL or "admin@nepalorigin.com.np",
    },
    debug=settings.DEBUG,
    openapi_url=_openapi_url,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# Security headers (inner). CORS must be outermost so OPTIONS preflight is handled correctly.
app.add_middleware(SecurityHeadersMiddleware)

_cors_origins = settings.cors_origins_list
if settings.is_production and not settings.DEBUG and ("*" in _cors_origins or not _cors_origins):
    raise RuntimeError(
        "Production requires explicit CORS_ORIGINS (e.g. https://nepalorigin.com.np). Wildcard is forbidden."
    )

# Outermost: allow browser preflight from Vite (localhost:5173) without 400s
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins if _cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

app.include_router(api_router, prefix=settings.API_V1_STR)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }
