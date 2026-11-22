#!/usr/bin/env python3
"""
Interactive script to create or update a superuser with admin permissions.

Usage:
    python scripts/create_superuser.py
    python -m scripts.create_superuser
"""

from __future__ import annotations

import asyncio
import getpass
import logging
import re
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.user import User
# Import related models so SQLAlchemy can resolve relationships
from app.models.cart import Cart  # noqa: F401
from app.models.wishlist import Wishlist  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.product import Category, Product, ProductVariant, ProductImage  # noqa: F401
from app.models.user_group import UserGroup
from app.models.permission import Permission

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _prompt_credentials() -> tuple[str, str, str]:
    """Ask for email, name, and password on the terminal."""
    print()
    email = input("Admin email: ").strip().lower()
    if not email or not EMAIL_RE.match(email):
        raise SystemExit("Invalid email address.")

    full_name = input("Full name (optional): ").strip() or email.split("@")[0].replace(".", " ").title()

    password = getpass.getpass("Password (min 8 characters): ")
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters.")

    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match.")

    return email, password, full_name


async def _ensure_admin_group(db) -> UserGroup:
    logger.info("Checking for admin group...")
    result = await db.execute(
        select(UserGroup)
        .filter(UserGroup.name == "Administrators")
        .options(selectinload(UserGroup.permissions))
    )
    admin_group = result.scalars().first()

    permissions_result = await db.execute(select(Permission))
    all_permissions = list(permissions_result.scalars().all())

    if not admin_group:
        logger.info("Creating 'Administrators' group...")
        admin_group = UserGroup(
            name="Administrators",
            description="Full administrative access to all features",
        )
        if all_permissions:
            admin_group.permissions = all_permissions
        db.add(admin_group)
        await db.flush()
        logger.info("Created 'Administrators' group with %s permissions", len(all_permissions))
        return admin_group

    existing_ids = {p.id for p in admin_group.permissions}
    missing = [p for p in all_permissions if p.id not in existing_ids]
    if missing:
        admin_group.permissions.extend(missing)
        await db.flush()
        logger.info("Updated 'Administrators' group with %s additional permissions", len(missing))
    return admin_group


async def create_superuser(email: str, password: str, full_name: str) -> None:
    """Create or update a superuser account with admin permissions."""
    async with SessionLocal() as db:
        try:
            logger.info("Checking if user '%s' exists...", email)
            result = await db.execute(
                select(User).filter(User.email == email).options(selectinload(User.groups))
            )
            user = result.scalars().first()
            admin_group = await _ensure_admin_group(db)

            if user:
                logger.info("User '%s' already exists. Updating to superuser...", email)
                user.hashed_password = get_password_hash(password)
                user.is_superuser = True
                user.is_active = True
                user.is_verified = True
                user.role = "admin"
                user.full_name = full_name or user.full_name
                if admin_group not in user.groups:
                    user.groups.append(admin_group)
                    logger.info("Assigned user to 'Administrators' group")
                db.add(user)
                action = "updated"
            else:
                logger.info("Creating new superuser '%s'...", email)
                user = User(
                    email=email,
                    hashed_password=get_password_hash(password),
                    full_name=full_name,
                    is_active=True,
                    is_superuser=True,
                    is_verified=True,
                    role="admin",
                )
                user.groups = [admin_group]
                db.add(user)
                action = "created"

            await db.commit()
            await db.refresh(user, ["groups"])

            logger.info("Superuser '%s' %s successfully!", email, action)
            logger.info("   - Email: %s", user.email)
            logger.info("   - Name: %s", user.full_name)
            logger.info("   - Role: %s", user.role)
            logger.info("   - Is Superuser: %s", user.is_superuser)
            logger.info("   - Groups: %s", [g.name for g in user.groups])
            logger.info("")
            logger.info("Login with the email and password you entered.")
            logger.info("Admin panel access: enabled")
        except SystemExit:
            raise
        except Exception as e:
            logger.error("Error creating superuser: %s", e, exc_info=True)
            await db.rollback()
            sys.exit(1)

    await engine.dispose()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Create / update Superuser (interactive)")
    logger.info("=" * 60)
    try:
        email, password, full_name = _prompt_credentials()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        sys.exit(1)
    asyncio.run(create_superuser(email, password, full_name))
