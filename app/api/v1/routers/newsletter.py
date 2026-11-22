"""Newsletter subscription, unsubscribe, and admin list."""
import logging
import secrets
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import settings
from app.core.database import get_db
from app.core import email as email_utils
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.models.user import User
from app.api.v1.dependencies.auth import get_current_admin_user
from app.api.v1.routers.site_config import get_or_create_site_config

router = APIRouter()
logger = logging.getLogger(__name__)


class NewsletterSubscribe(BaseModel):
    email: EmailStr


class NewsletterSubscriberOut(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


def _new_token() -> str:
    return secrets.token_urlsafe(24)


def _admin_email(site_contact_email: str | None) -> str | None:
    return (settings.DEFAULT_ADMIN_EMAIL or "").strip() or (site_contact_email or "").strip() or None


@router.post("/subscribe", response_model=dict)
async def subscribe_newsletter(
    data: NewsletterSubscribe = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Subscribe to newsletter. Sends confirmation email with unsubscribe link."""
    email = str(data.email).strip().lower()
    if not email or "@" not in email:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body", "email"], "msg": "Please enter a valid email address.", "type": "value_error"}],
        )

    result = await db.execute(select(NewsletterSubscriber).filter(NewsletterSubscriber.email == email))
    existing = result.scalar_one_or_none()

    site_config = await get_or_create_site_config(db)
    site_title = site_config.site_title or "Nepal Origin"
    admin_email = _admin_email(site_config.contact_email)
    is_new = False

    if existing:
        if existing.is_active:
            return {"msg": "You are already subscribed to our newsletter."}
        existing.is_active = True
        if not existing.unsubscribe_token:
            existing.unsubscribe_token = _new_token()
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
        subscriber = existing
    else:
        subscriber = NewsletterSubscriber(
            email=email,
            is_active=True,
            unsubscribe_token=_new_token(),
        )
        db.add(subscriber)
        await db.commit()
        await db.refresh(subscriber)
        is_new = True

    try:
        await email_utils.send_newsletter_welcome_email(
            email_to=email,
            logo_url=site_config.logo_url,
            site_title=site_title,
            contact_email=site_config.contact_email,
            unsubscribe_token=subscriber.unsubscribe_token,
            admin_cc=admin_email,
        )
        if admin_email and is_new:
            await email_utils.send_newsletter_admin_notify_email(
                admin_email=admin_email,
                subscriber_email=email,
                logo_url=site_config.logo_url,
                site_title=site_title,
            )
    except Exception as e:
        logger.exception("Critical: newsletter subscription emails failed for %s: %s", email, e)

    return {"msg": "Thank you for subscribing! Check your email for confirmation."}


@router.get("/unsubscribe", response_model=dict)
async def unsubscribe_newsletter(
    token: str = Query(..., min_length=8),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Public unsubscribe via token from email link."""
    result = await db.execute(
        select(NewsletterSubscriber).filter(NewsletterSubscriber.unsubscribe_token == token)
    )
    subscriber = result.scalar_one_or_none()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid or expired unsubscribe link.")

    if not subscriber.is_active:
        return {"msg": "You are already unsubscribed.", "email": subscriber.email}

    subscriber.is_active = False
    db.add(subscriber)
    await db.commit()

    site_config = await get_or_create_site_config(db)
    admin_email = _admin_email(site_config.contact_email)
    try:
        await email_utils.send_newsletter_unsubscribed_email(
            email_to=subscriber.email,
            logo_url=site_config.logo_url,
            site_title=site_config.site_title or "Nepal Origin",
            admin_cc=admin_email,
        )
    except Exception as e:
        logger.exception("Critical: unsubscribe confirmation email failed: %s", e)

    return {"msg": "You have been unsubscribed successfully.", "email": subscriber.email}


@router.get("/admin/subscribers", response_model=List[NewsletterSubscriberOut])
async def list_subscribers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    stmt = select(NewsletterSubscriber).order_by(NewsletterSubscriber.created_at.desc())
    if active_only:
        stmt = stmt.filter(NewsletterSubscriber.is_active.is_(True))
    if search and search.strip():
        q = f"%{search.strip().lower()}%"
        stmt = stmt.filter(func.lower(NewsletterSubscriber.email).like(q))
    stmt = stmt.offset(skip).limit(min(limit, 500))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/admin/stats", response_model=dict)
async def subscriber_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> dict:
    total = (await db.execute(select(func.count(NewsletterSubscriber.id)))).scalar() or 0
    active = (
        await db.execute(
            select(func.count(NewsletterSubscriber.id)).filter(NewsletterSubscriber.is_active.is_(True))
        )
    ).scalar() or 0
    return {"total": total, "active": active, "inactive": total - active}


@router.delete("/admin/subscribers/{subscriber_id}", response_model=dict)
async def delete_subscriber(
    subscriber_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> dict:
    result = await db.execute(select(NewsletterSubscriber).filter(NewsletterSubscriber.id == subscriber_id))
    subscriber = result.scalar_one_or_none()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    await db.delete(subscriber)
    await db.commit()
    return {"msg": "Subscriber removed"}
