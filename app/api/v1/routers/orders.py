from typing import Any, List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, get_current_admin_user
from app.api.v1.routers.site_config import get_or_create_site_config
from app.core.config import settings
from app.core.database import get_db
from app.core.email import (
    send_order_confirmed_email,
    send_order_status_email,
    send_order_completed_email,
    send_order_admin_notify_email,
    send_order_reply_email,
)
from app.models.user import User
from app.schemas.order import (
    Order,
    OrderAdmin,
    OrderCreate,
    OrderUpdate,
    GuestOrderCreate,
    OrderReplyCreate,
    OrderReplyOut,
)
from app.services.order_service import order_service

router = APIRouter()
logger = logging.getLogger(__name__)


def _admin_notify_email(site_contact_email: Optional[str]) -> Optional[str]:
    return (settings.DEFAULT_ADMIN_EMAIL or "").strip() or (site_contact_email or "").strip() or None


def _customer_from_order(order) -> tuple[str, str]:
    name = order.customer_name or (getattr(order.user, "full_name", None) if order.user else None) or "Customer"
    email = order.customer_email or (getattr(order.user, "email", None) if order.user else None) or ""
    return name, email


def _order_to_admin(order) -> OrderAdmin:
    data = Order.model_validate(order).model_dump()
    if not data.get("customer_name") or not data.get("customer_email"):
        user = getattr(order, "user", None)
        if user:
            data["customer_name"] = data.get("customer_name") or getattr(user, "full_name", None)
            data["customer_email"] = data.get("customer_email") or getattr(user, "email", None)
    return OrderAdmin(**data)


@router.post("/inquiry", response_model=Order, status_code=201)
async def create_inquiry_order(
    order_in: GuestOrderCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Public herbal product inquiry/order. No login and no payment gateway.
    Notifies DEFAULT_ADMIN_EMAIL and sends confirmation to the customer.
    """
    try:
        order = await order_service.create_guest_order(db, order_in=order_in)
    except ValueError as e:
        logger.warning("Inquiry order rejected: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Critical: guest inquiry order failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to submit your order right now. Please try again shortly.",
        )

    try:
        site_config = await get_or_create_site_config(db)
        logo_url = getattr(site_config, "logo_url", None)
        site_title = getattr(site_config, "site_title", None) or "Nepal Origin"
        total_str = f"Rs. {float(order.total_amount):,.2f}"
        order_number = order.order_number or str(order.id).zfill(8)
        name, email = _customer_from_order(order)

        admin_email = _admin_notify_email(getattr(site_config, "contact_email", None))

        if email:
            await send_order_confirmed_email(
                email_to=email,
                recipient_name=name,
                order_number=order_number,
                total_amount=total_str,
                status=order.status,
                logo_url=logo_url,
                site_title=site_title,
                admin_cc=admin_email,
            )

        if admin_email:
            await send_order_admin_notify_email(
                admin_email=admin_email,
                order_number=order_number,
                customer_name=name,
                customer_email=email,
                customer_phone=order.customer_phone,
                customer_country=order.customer_country,
                customer_address=(order.shipping_address or {}).get("street"),
                total_amount=total_str,
                order_items=order.items,
                notes=order.customer_notes,
                logo_url=logo_url,
                site_title=site_title,
            )
    except Exception as e:
        logger.exception(
            "Critical: failed to send inquiry order emails for order %s: %s",
            getattr(order, "id", None),
            e,
        )

    return order


@router.get("/admin/all", response_model=List[OrderAdmin])
async def read_all_orders(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    date_from: str = None,
    date_to: str = None,
    search: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    orders = await order_service.get_all_orders(
        db, skip=skip, limit=limit, status=status, date_from=date_from, date_to=date_to, search=search
    )
    return [_order_to_admin(o) for o in orders]


@router.get("/admin/{order_id}", response_model=OrderAdmin)
async def read_order_admin(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    order = await order_service.get_order_admin(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_to_admin(order)


@router.post("/admin/{order_id}/replies", response_model=OrderReplyOut, status_code=201)
async def reply_to_order(
    order_id: int,
    body: OrderReplyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """Admin reply about an order — saved and emailed to the customer."""
    reply = await order_service.add_admin_reply(
        db,
        order_id=order_id,
        message=body.message,
        admin_user_id=current_user.id,
    )
    if not reply:
        raise HTTPException(status_code=404, detail="Order not found")

    order = await order_service.get_order_admin(db, order_id=order_id)
    name, email = _customer_from_order(order) if order else ("Customer", "")
    if email:
        try:
            site_config = await get_or_create_site_config(db)
            await send_order_reply_email(
                email_to=email,
                recipient_name=name,
                order_number=(order.order_number if order else str(order_id)),
                message=body.message,
                logo_url=getattr(site_config, "logo_url", None),
                site_title=getattr(site_config, "site_title", None) or "Nepal Origin",
            )
        except Exception as e:
            logger.exception("Failed to email order reply: %s", e)

    return reply


@router.delete("/admin/{order_id}")
async def delete_order_admin(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    deleted = await order_service.delete_order(db, order_id=order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"msg": "Order deleted successfully"}


@router.patch("/{order_id}/status", response_model=Order)
async def update_order_status(
    order_id: int,
    status_update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    order = await order_service.update_status(db, order_id=order_id, status=status_update.status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_full = await order_service.get_order_admin(db, order_id=order_id)
    if order_full:
        name, email = _customer_from_order(order_full)
        if email:
            try:
                site_config = await get_or_create_site_config(db)
                logo_url = getattr(site_config, "logo_url", None)
                site_title = getattr(site_config, "site_title", None) or "Nepal Origin"
                order_number = order_full.order_number or str(order_full.id).zfill(8)
                await send_order_status_email(
                    email_to=email,
                    recipient_name=name,
                    order_number=order_number,
                    new_status=status_update.status,
                    logo_url=logo_url,
                    site_title=site_title,
                )
                if status_update.status.lower() in ("completed", "delivered", "confirmed"):
                    total_str = f"Rs. {float(order_full.total_amount):,.2f}"
                    await send_order_completed_email(
                        email_to=email,
                        recipient_name=name,
                        order_number=order_number,
                        total_amount=total_str,
                        order_items=order_full.items,
                        logo_url=logo_url,
                        site_title=site_title,
                    )
            except Exception as e:
                logger.exception("Failed to send order status email: %s", e)
    return order_full if order_full else order


@router.post("/", response_model=Order)
async def create_order(
    order_in: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Legacy cart checkout (authenticated). Prefer /orders/inquiry for herbal inquiry flow."""
    try:
        order = await order_service.create_order(db, user_id=current_user.id, order_in=order_in)
        try:
            site_config = await get_or_create_site_config(db)
            logo_url = getattr(site_config, "logo_url", None)
            site_title = getattr(site_config, "site_title", None) or "Nepal Origin"
            total_str = f"Rs. {float(order.total_amount):,.2f}"
            order_number = order.order_number or str(order.id).zfill(8)
            await send_order_confirmed_email(
                email_to=current_user.email,
                recipient_name=current_user.full_name,
                order_number=order_number,
                total_amount=total_str,
                status=order.status,
                logo_url=logo_url,
                site_title=site_title,
            )
            admin_email = _admin_notify_email(getattr(site_config, "contact_email", None))
            if admin_email:
                await send_order_admin_notify_email(
                    admin_email=admin_email,
                    order_number=order_number,
                    customer_name=current_user.full_name or "Customer",
                    customer_email=current_user.email,
                    customer_phone=None,
                    customer_country=None,
                    customer_address=None,
                    total_amount=total_str,
                    order_items=order.items,
                    notes=None,
                    logo_url=logo_url,
                    site_title=site_title,
                )
        except Exception as e:
            logger.exception("Failed to send order confirmation email: %s", e)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Order creation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")


@router.get("/", response_model=List[Order])
async def read_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await order_service.get_orders(db, user_id=current_user.id)


@router.get("/{order_id}", response_model=Order)
async def read_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    order = await order_service.get_order(db, order_id=order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
