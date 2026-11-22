"""
Application settings with environment-aware config.
- ENVIRONMENT=development -> PostgreSQL, DEBUG default True, relaxed CORS
- ENVIRONMENT=production -> MySQL, DEBUG default False, strict CORS/cookies/HTTPS
"""
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    # ---------- Environment ----------
    ENVIRONMENT: str = "development"  # "development" | "production"
    DEBUG: bool = True  # Set to False in production (.env: DEBUG=false)

    PROJECT_NAME: str = "Nepal Origin API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Admin notification inbox (orders, contact form). Falls back to site contact_email if empty.
    DEFAULT_ADMIN_EMAIL: str = ""

    # ---------- Cookie (production: secure, HTTPS) ----------
    COOKIE_ACCESS_TOKEN_NAME: str = "access_token"
    COOKIE_REFRESH_TOKEN_NAME: str = "refresh_token"
    COOKIE_SECURE: bool = False  # Set True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"
    COOKIE_HTTPONLY: bool = True
    COOKIE_PATH: str = "/"

    # ---------- PostgreSQL (development) ----------
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: Optional[str] = None

    # ---------- MySQL (production) ----------
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_SERVER: Optional[str] = None
    MYSQL_PORT: int = 3306
    MYSQL_DB: Optional[str] = None
    MYSQL_SSL: bool = False  # Enable TLS to MySQL when remote
    MYSQL_SSL_CA: Optional[str] = None  # Path to CA cert (optional)

    # Redis: set REDIS_URL directly, or use REDIS_HOST + REDIS_PORT + REDIS_PASSWORD
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # ---------- Email ----------
    EMAIL_HOST: str = "localhost"
    EMAIL_PORT: int = 587
    EMAIL_HOST_USER: str = ""
    EMAIL_HOST_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@example.com"

    FRONTEND_URL: str = "http://localhost:5173"
    API_URL: str = "http://localhost:8000"

    # ---------- Stripe ----------
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ---------- Uploads & static ----------
    UPLOAD_DIR: str = "uploads"

    # ---------- CORS (comma-separated origins; production: exact frontend URL(s) only) ----------
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://localhost:8090,http://127.0.0.1:5173,"
        "http://localhost:3000,http://localhost:8080"
    )

    # ---------- Security ----------
    # Comma-separated hostnames for Host header validation (production). Empty = skip.
    ALLOWED_HOSTS: str = ""
    FORCE_HTTPS: bool = False
    SECURITY_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000
    CSRF_PROTECT: bool = True
    # Empty = use a sensible default CSP for the API responses
    CONTENT_SECURITY_POLICY: str = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    # Login / auth brute-force protection
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 10
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 300
    # Sanitize CKEditor HTML on save (XSS / HTML injection)
    SANITIZE_HTML: bool = True

    # ---------- Logging ----------
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("COOKIE_SAMESITE", mode="before")
    @classmethod
    def normalize_samesite(cls, v: str) -> str:
        if isinstance(v, str):
            val = v.strip().lower()
            if val not in {"lax", "strict", "none"}:
                return "lax"
            return val
        return v

    @model_validator(mode="after")
    def build_redis_url(self) -> "Settings":
        """If REDIS_URL is not set, build it from REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB."""
        if self.REDIS_URL:
            return self
        auth = ""
        if self.REDIS_PASSWORD:
            auth = f":{quote_plus(self.REDIS_PASSWORD)}@"
        object.__setattr__(
            self,
            "REDIS_URL",
            f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}",
        )
        return self

    @model_validator(mode="after")
    def production_safe_defaults(self) -> "Settings":
        """Warn via property usage: in production prefer secure cookies / no debug."""
        if self.is_production and self.CORS_ORIGINS.strip() == "*":
            raise ValueError("CORS_ORIGINS=* is not allowed with credentials in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def DATABASE_URL(self) -> str:
        if self.is_production:
            if not all([self.MYSQL_USER, self.MYSQL_PASSWORD, self.MYSQL_SERVER, self.MYSQL_DB]):
                raise ValueError(
                    "When ENVIRONMENT=production set MYSQL_USER, MYSQL_PASSWORD, MYSQL_SERVER, MYSQL_DB in .env"
                )
            return URL.create(
                "mysql+aiomysql",
                username=self.MYSQL_USER,
                password=self.MYSQL_PASSWORD,
                host=self.MYSQL_SERVER,
                port=self.MYSQL_PORT,
                database=self.MYSQL_DB,
            ).render_as_string(hide_password=False)
        # Development: PostgreSQL
        if not all([self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_SERVER, self.POSTGRES_DB]):
            raise ValueError(
                "When ENVIRONMENT=development set POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_DB in .env"
            )
        return URL.create(
            "postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    @property
    def sqlalchemy_connect_args(self) -> Dict[str, Any]:
        """Extra connect args (e.g. MySQL SSL for aiomysql)."""
        if not self.is_production or not self.MYSQL_SSL:
            return {}
        if self.MYSQL_SSL_CA:
            import ssl as ssl_mod

            ctx = ssl_mod.create_default_context(cafile=self.MYSQL_SSL_CA)
            return {"ssl": ctx}
        return {"ssl": True}

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            # Never return bare * when credentials are required — empty forces explicit config
            if self.is_production:
                return []
            return ["*"]
        return [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        if not self.ALLOWED_HOSTS or self.ALLOWED_HOSTS.strip() == "*":
            return []
        return [h.strip().lower() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
