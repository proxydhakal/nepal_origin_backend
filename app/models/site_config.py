from typing import Optional
from sqlalchemy import Text, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class SiteConfig(Base):
    """Singleton table for site configuration. Only one row (id=1) is used."""
    __tablename__ = "siteconfig"
    __table_args__ = {"extend_existing": True}

    site_title: Mapped[str] = mapped_column(String(255), default="Nepal Origin")
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Contact info
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Store location / map (admin-managed)
    map_embed_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    map_latitude: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    map_longitude: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Media URLs (paths under /uploads/site/ or /static/brand/)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Social media links as JSON:
    # { "facebook": "url", "facebook_icon": "/uploads/...", "instagram": "url", ... }
    social_links: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
