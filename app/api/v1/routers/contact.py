import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core import email as email_utils
from app.api.v1.dependencies.auth import get_current_user_optional
from app.api.v1.routers.site_config import get_or_create_site_config
from app.models.user import User
from app.models.contact_submission import ContactSubmission
from app.schemas.contact import ContactSubmissionCreate, ContactSubmissionOut

router = APIRouter()
logger = logging.getLogger(__name__)


def _admin_notify_email(site_contact_email: str | None) -> str | None:
    return (settings.DEFAULT_ADMIN_EMAIL or "").strip() or (site_contact_email or "").strip() or None


@router.post("/", response_model=ContactSubmissionOut, status_code=201)
async def submit_contact(
    data: ContactSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Submit contact form. Thank-you to user; admin notified via DEFAULT_ADMIN_EMAIL."""
    name = (data.name or "").strip()
    email = (data.email or "").strip().lower()
    subject = (data.subject or "").strip()
    message = (data.message or "").strip()

    field_errors: list[dict] = []
    if len(name) < 2:
        field_errors.append(
            {"loc": ["body", "name"], "msg": "Name must be at least 2 characters.", "type": "string_too_short"}
        )
    if "@" not in email or "." not in email.split("@")[-1]:
        field_errors.append(
            {"loc": ["body", "email"], "msg": "Please provide a valid email address.", "type": "value_error"}
        )
    if len(subject) < 3:
        field_errors.append(
            {"loc": ["body", "subject"], "msg": "Subject must be at least 3 characters.", "type": "string_too_short"}
        )
    if len(message) < 10:
        field_errors.append(
            {"loc": ["body", "message"], "msg": "Message must be at least 10 characters.", "type": "string_too_short"}
        )
    if data.submission_type not in ("feedback", "grievance"):
        field_errors.append(
            {"loc": ["body", "submission_type"], "msg": "Type must be feedback or grievance.", "type": "value_error"}
        )
    if field_errors:
        raise HTTPException(status_code=422, detail=field_errors)

    try:
        submission = ContactSubmission(
            name=name,
            email=email,
            subject=subject,
            message=message,
            submission_type=data.submission_type,
            user_id=current_user.id if current_user else None,
        )
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
    except Exception as e:
        logger.exception("Critical: failed to save contact submission: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to submit your message right now. Please try again shortly.",
        )

    try:
        site_config = await get_or_create_site_config(db)
        logo_url = site_config.logo_url
        site_title = site_config.site_title or "Nepal Origin"
        contact_email = site_config.contact_email
        admin_email = _admin_notify_email(contact_email)

        await email_utils.send_contact_thankyou_email(
            email_to=email,
            name=name,
            logo_url=logo_url,
            site_title=site_title,
            contact_email=contact_email or admin_email,
            admin_cc=admin_email,
        )
        if admin_email:
            await email_utils.send_contact_admin_notify_email(
                admin_email=admin_email,
                name=name,
                email=email,
                subject=subject,
                message=message,
                submission_type=data.submission_type,
                logo_url=logo_url,
                site_title=site_title,
            )
    except Exception as e:
        logger.exception("Critical: contact emails failed for submission %s: %s", submission.id, e)

    return submission
