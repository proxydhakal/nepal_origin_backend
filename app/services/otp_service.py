"""OTP storage and verification using the database (works without Redis)."""
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification_otp import VerificationOtp


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


PURPOSE_EMAIL_VERIFICATION = "email_verification"
PURPOSE_PASSWORD_RESET = "password_reset"


async def set_otp_db(
    db: AsyncSession,
    email: str,
    otp: str,
    expire_seconds: int = 600,
    purpose: str = PURPOSE_EMAIL_VERIFICATION,
) -> None:
    """Store OTP for email and purpose. Replaces any existing OTP for that email+purpose."""
    key_email = _normalize_email(email)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)
    await db.execute(
        delete(VerificationOtp).where(
            and_(
                VerificationOtp.email == key_email,
                VerificationOtp.purpose == purpose,
            )
        )
    )
    db.add(
        VerificationOtp(
            email=key_email,
            otp=otp,
            expires_at=expires_at,
            purpose=purpose,
        )
    )
    await db.commit()


async def get_and_delete_otp_db(
    db: AsyncSession,
    email: str,
    purpose: str = PURPOSE_EMAIL_VERIFICATION,
) -> Optional[str]:
    """Get OTP for email and purpose, then delete (one-time use). Returns None if invalid or expired."""
    key_email = _normalize_email(email)
    result = await db.execute(
        select(VerificationOtp)
        .where(VerificationOtp.email == key_email)
        .where(VerificationOtp.purpose == purpose)
        .where(VerificationOtp.expires_at > datetime.now(timezone.utc))
        .limit(1)
    )
    row = result.scalars().first()
    if not row:
        return None
    otp = row.otp
    await db.delete(row)
    await db.commit()
    return otp
