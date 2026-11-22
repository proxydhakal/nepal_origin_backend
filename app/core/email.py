"""Email sending using HTML templates with logo and site colors."""
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from app.core.email_templates import (
    verification_email_html,
    verification_otp_email_html,
    password_reset_otp_email_html,
    password_reset_email_html,
    newsletter_welcome_email_html,
    newsletter_admin_notify_email_html,
    newsletter_unsubscribed_email_html,
    contact_thankyou_email_html,
    contact_admin_notify_email_html,
    order_confirmed_email_html,
    order_status_update_email_html,
    order_completed_email_html,
    order_admin_notify_email_html,
    order_reply_email_html,
)

# Port 465 uses SSL/TLS, port 587 uses STARTTLS
# For port 465: MAIL_SSL_TLS=True, MAIL_STARTTLS=False
# For port 587: MAIL_STARTTLS=True, MAIL_SSL_TLS=False
use_ssl = settings.EMAIL_PORT == 465

conf = ConnectionConfig(
    MAIL_USERNAME=settings.EMAIL_HOST_USER,
    MAIL_PASSWORD=settings.EMAIL_HOST_PASSWORD,
    MAIL_FROM=settings.FROM_EMAIL,
    MAIL_PORT=settings.EMAIL_PORT,
    MAIL_SERVER=settings.EMAIL_HOST,
    MAIL_STARTTLS=not use_ssl,  # STARTTLS for port 587
    MAIL_SSL_TLS=use_ssl,  # SSL/TLS for port 465
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fastmail = FastMail(conf)


DEFAULT_LOGO_PATH = "static/brand/logo.png"
SUPPORT_EMAIL = "support@nepalorigin.store"


def _logo_url(relative_path: str | None) -> str | None:
    """Build full logo URL for emails. Uses static brand logo when not provided."""
    path = (relative_path or DEFAULT_LOGO_PATH).strip()
    if not path:
        return None
    base = settings.API_URL.rstrip("/")
    path = path.lstrip("/").replace("\\", "/")
    return f"{base}/{path}"


def _cc_emails(admin_email: str | None, recipient: str | None = None) -> list[str]:
    """CC admin on customer emails when configured and not the same as recipient."""
    admin = (admin_email or settings.DEFAULT_ADMIN_EMAIL or "").strip()
    if not admin:
        return []
    if recipient and admin.lower() == recipient.strip().lower():
        return []
    return [admin]


def unsubscribe_link(token: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/newsletter/unsubscribe?token={token}"


async def send_verification_email(
    email_to: str,
    token: str,
    full_name: str | None = None,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> None:
    """Send email verification link after signup."""
    verify_link = f"{settings.FRONTEND_URL.rstrip('/')}/auth/verify-email?token={token}"
    html = verification_email_html(
        recipient_name=full_name or "Customer",
        verify_link=verify_link,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
    )
    message = MessageSchema(
        subject="Verify Your Email",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_verification_otp_email(
    email_to: str,
    otp: str,
    full_name: str | None = None,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    expire_minutes: int = 10,
) -> None:
    """Send OTP for email verification (app-based, no link)."""
    html = verification_otp_email_html(
        recipient_name=full_name or "Customer",
        otp=otp,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        expire_minutes=expire_minutes,
    )
    message = MessageSchema(
        subject="Your Verification Code - Nepal Origin",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_reset_password_email(
    email_to: str,
    token: str,
    full_name: str | None = None,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> None:
    """Send password reset link."""
    reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/auth/reset-password?token={token}"
    html = password_reset_email_html(
        recipient_name=full_name or "Customer",
        reset_link=reset_link,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
    )
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_password_reset_otp_email(
    email_to: str,
    otp: str,
    full_name: str | None = None,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    expire_minutes: int = 10,
) -> None:
    """Send OTP for password reset (app-based)."""
    html = password_reset_otp_email_html(
        recipient_name=full_name or "Customer",
        otp=otp,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        expire_minutes=expire_minutes,
    )
    message = MessageSchema(
        subject="Your Password Reset Code - Nepal Origin",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_newsletter_welcome_email(
    email_to: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    contact_email: str | None = None,
    unsubscribe_token: str | None = None,
    admin_cc: str | None = None,
) -> None:
    """Send newsletter subscription confirmation (admin CC when configured)."""
    html = newsletter_welcome_email_html(
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        contact_email=contact_email or SUPPORT_EMAIL,
        unsubscribe_url=unsubscribe_link(unsubscribe_token) if unsubscribe_token else None,
    )
    message = MessageSchema(
        subject=f"Welcome to {site_title} Newsletter",
        recipients=[email_to],
        cc=_cc_emails(admin_cc or contact_email, email_to),
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_newsletter_admin_notify_email(
    admin_email: str,
    subscriber_email: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> None:
    html = newsletter_admin_notify_email_html(
        email=subscriber_email,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
    )
    message = MessageSchema(
        subject=f"[{site_title}] New newsletter subscriber",
        recipients=[admin_email],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_newsletter_unsubscribed_email(
    email_to: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    admin_cc: str | None = None,
) -> None:
    html = newsletter_unsubscribed_email_html(
        logo_url=_logo_url(logo_url),
        site_title=site_title,
    )
    message = MessageSchema(
        subject=f"Unsubscribed from {site_title} Newsletter",
        recipients=[email_to],
        cc=_cc_emails(admin_cc, email_to),
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_contact_thankyou_email(
    email_to: str,
    name: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    contact_email: str | None = None,
    admin_cc: str | None = None,
) -> None:
    """Send thank-you email after contact form submission (admin CC when configured)."""
    html = contact_thankyou_email_html(
        recipient_name=name,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        contact_email=contact_email or SUPPORT_EMAIL,
    )
    message = MessageSchema(
        subject=f"We Received Your Message - {site_title}",
        recipients=[email_to],
        cc=_cc_emails(admin_cc or contact_email, email_to),
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_contact_admin_notify_email(
    admin_email: str,
    name: str,
    email: str,
    subject: str,
    message: str,
    submission_type: str = "feedback",
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> None:
    """Notify admin when contact form is submitted."""
    html = contact_admin_notify_email_html(
        name=name,
        email=email,
        subject=subject,
        message=message,
        submission_type=submission_type,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
    )
    msg = MessageSchema(
        subject=f"[{site_title}] New Contact Form: {subject[:50]}",
        recipients=[admin_email],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(msg)


def _orders_url() -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/orders"


async def send_order_confirmed_email(
    email_to: str,
    recipient_name: str | None,
    order_number: str,
    total_amount: str,
    status: str = "pending",
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    admin_cc: str | None = None,
) -> None:
    """Send order/inquiry confirmation (admin CC when configured)."""
    html = order_confirmed_email_html(
        recipient_name=recipient_name or "Customer",
        order_number=order_number,
        total_amount=total_amount,
        status=status,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        orders_url=_orders_url(),
    )
    message = MessageSchema(
        subject=f"Order Inquiry #{order_number} - {site_title}",
        recipients=[email_to],
        cc=_cc_emails(admin_cc, email_to),
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_order_status_email(
    email_to: str,
    recipient_name: str | None,
    order_number: str,
    new_status: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> None:
    """Send email when order status is updated. order_number: 8-digit tracking ID."""
    html = order_status_update_email_html(
        recipient_name=recipient_name or "Customer",
        order_number=order_number,
        new_status=new_status,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        orders_url=_orders_url(),
    )
    message = MessageSchema(
        subject=f"Order #{order_number} - Status: {new_status} - {site_title}",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


def _order_items_rows(order_items: list) -> str:
    rows = []
    for item in order_items or []:
        name = "Product"
        if getattr(item, "variant", None) and getattr(item.variant, "product", None):
            name = item.variant.product.name or name
        elif getattr(item, "variant", None):
            name = getattr(item.variant, "sku", name)
        qty = getattr(item, "quantity", 0)
        unit = getattr(item, "quantity_unit", "") or ""
        price = getattr(item, "price_at_purchase", 0)
        try:
            line_total = float(price) * float(qty)
        except (TypeError, ValueError):
            line_total = 0
        qty_label = f"{qty} {unit}".strip()
        rows.append(
            f'<tr><td style="padding:10px;border:1px solid #d1d5db;">{name}</td>'
            f'<td style="text-align:center;padding:10px;border:1px solid #d1d5db;">{qty_label}</td>'
            f'<td style="text-align:right;padding:10px;border:1px solid #d1d5db;">Rs. {line_total:,.2f}</td></tr>'
        )
    return "\n".join(rows) or '<tr><td colspan="3" style="padding:10px;">No items</td></tr>'


async def send_order_admin_notify_email(
    admin_email: str,
    order_number: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str | None,
    customer_country: str | None,
    customer_address: str | None,
    total_amount: str,
    order_items: list,
    notes: str | None = None,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> None:
    html = order_admin_notify_email_html(
        order_number=order_number,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        customer_country=customer_country,
        customer_address=customer_address,
        total_amount=total_amount,
        items_html=_order_items_rows(order_items),
        notes=notes,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
    )
    message = MessageSchema(
        subject=f"[{site_title}] New order inquiry #{order_number}",
        recipients=[admin_email],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)


async def send_order_reply_email(
    email_to: str,
    recipient_name: str | None,
    order_number: str,
    message: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> None:
    html = order_reply_email_html(
        recipient_name=recipient_name or "Customer",
        order_number=order_number,
        message=message,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
    )
    msg = MessageSchema(
        subject=f"Update on order #{order_number} - {site_title}",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(msg)


async def send_order_completed_email(
    email_to: str,
    recipient_name: str | None,
    order_number: str,
    total_amount: str,
    order_items: list,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> None:
    """Send order completed email with list of order items. order_number: 8-digit tracking ID. order_items: list of objects with variant (with product.name), quantity, price_at_purchase."""
    rows = []
    for item in order_items:
        name = "Product"
        if getattr(item, "variant", None) and getattr(item.variant, "product", None):
            name = item.variant.product.name or name
        elif getattr(item, "variant", None):
            name = getattr(item.variant, "sku", name)
        qty = getattr(item, "quantity", 0)
        price = getattr(item, "price_at_purchase", 0)
        try:
            line_total = float(price) * int(qty)
        except (TypeError, ValueError):
            line_total = 0
        rows.append(
            f'<tr><td style="padding:10px;border:1px solid #d1d5db;">{name}</td>'
            f'<td style="text-align:center;padding:10px;border:1px solid #d1d5db;">{qty}</td>'
            f'<td style="text-align:right;padding:10px;border:1px solid #d1d5db;">Rs. {line_total:,.2f}</td></tr>'
        )
    items_html = "\n".join(rows)
    html = order_completed_email_html(
        recipient_name=recipient_name or "Customer",
        order_number=order_number,
        total_amount=total_amount,
        items_html=items_html,
        logo_url=_logo_url(logo_url),
        site_title=site_title,
        orders_url=_orders_url(),
    )
    message = MessageSchema(
        subject=f"Order Completed #{order_number} - {site_title}",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )
    await fastmail.send_message(message)
