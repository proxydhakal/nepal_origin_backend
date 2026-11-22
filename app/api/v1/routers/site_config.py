"""Site configuration router - public GET and admin PATCH endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.dependencies.auth import get_current_admin_user
from app.core.database import get_db
from app.core.storage import save_site_asset
from app.models.site_config import SiteConfig
from app.models.user import User
from app.schemas.site_config import SiteConfigResponse, SiteConfigUpdate

router = APIRouter()

DEFAULT_LOGO_URL = "/static/brand/logo.png"
DEFAULT_FAVICON_URL = "/static/brand/favicon.png"


async def get_or_create_site_config(db: AsyncSession) -> SiteConfig:
    """Get the singleton site config, creating it if it doesn't exist."""
    result = await db.execute(select(SiteConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        config = SiteConfig(
            site_title="Nepal Origin",
            meta_description="Modern ecommerce platform",
            logo_url=DEFAULT_LOGO_URL,
            favicon_url=DEFAULT_FAVICON_URL,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config

    # Seed default brand assets when none are configured yet
    updated = False
    if not config.logo_url:
        config.logo_url = DEFAULT_LOGO_URL
        updated = True
    if not config.favicon_url:
        config.favicon_url = DEFAULT_FAVICON_URL
        updated = True
    if updated:
        await db.commit()
        await db.refresh(config)
    return config


@router.get("/site-config", response_model=SiteConfigResponse)
async def get_site_config(
    db: AsyncSession = Depends(get_db),
):
    """
    Get public site configuration. No auth required.
    Used by frontend for title, meta, logo, favicon, contact, social links.
    """
    config = await get_or_create_site_config(db)
    return config


@router.patch("/site-config", response_model=SiteConfigResponse)
async def update_site_config(
    data: SiteConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Update site configuration (admin only).
    """
    config = await get_or_create_site_config(db)
    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(config, field, value)
    await db.commit()
    await db.refresh(config)
    return config


@router.post("/site-config/upload-logo", response_model=SiteConfigResponse)
async def upload_logo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Upload site logo (admin only). Replaces existing logo."""
    relative_path = await save_site_asset(file, "logo")
    config = await get_or_create_site_config(db)
    config.logo_url = relative_path.replace("\\", "/")
    await db.commit()
    await db.refresh(config)
    return config


@router.post("/site-config/upload-favicon", response_model=SiteConfigResponse)
async def upload_favicon(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Upload site favicon (admin only). Replaces existing favicon."""
    relative_path = await save_site_asset(file, "favicon")
    config = await get_or_create_site_config(db)
    config.favicon_url = relative_path.replace("\\", "/")
    await db.commit()
    await db.refresh(config)
    return config


SOCIAL_PLATFORMS = {
    "facebook",
    "twitter",
    "instagram",
    "linkedin",
    "youtube",
    "tiktok",
    "pinterest",
}


@router.post("/site-config/upload-social-icon", response_model=SiteConfigResponse)
async def upload_social_icon(
    platform: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Upload a custom social media icon (admin only). Stored in social_links.{platform}_icon."""
    key = (platform or "").strip().lower()
    if key not in SOCIAL_PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"platform must be one of: {', '.join(sorted(SOCIAL_PLATFORMS))}",
        )
    relative_path = await save_site_asset(file, f"social_{key}")
    config = await get_or_create_site_config(db)
    links = dict(config.social_links or {})
    links[f"{key}_icon"] = "/" + relative_path.replace("\\", "/")
    config.social_links = links
    await db.commit()
    await db.refresh(config)
    return config
