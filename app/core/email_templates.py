"""HTML email templates with site logo and colors (#0B5C2E green, #F57C00 orange)."""
from datetime import datetime

# Site colors (from website)
PRIMARY_COLOR = "#0B5C2E"
ACCENT_COLOR = "#F57C00"
TEXT_COLOR = "#374151"
LIGHT_BG = "#f3f4f6"
DARK_FOOTER = "#0a3d1f"


def _base_html(
    title: str,
    body_content: str,
    logo_url: str | None,
    site_title: str = "Nepal Origin",
    unsubscribe_url: str | None = None,
    footer_note: str | None = None,
) -> str:
    """Base HTML wrapper with logo header, themed body, copyright footer."""
    year = datetime.now().year
    if logo_url:
        logo_section = (
            f'<img src="{logo_url}" alt="{site_title}" '
            f'style="max-height:52px;max-width:200px;height:auto;display:inline-block;" />'
        )
    else:
        logo_section = (
            f'<span style="font-size:24px;font-weight:800;color:#ffffff;letter-spacing:0.5px;">'
            f"{site_title}</span>"
        )

    unsubscribe_block = ""
    if unsubscribe_url:
        unsubscribe_block = (
            f'<p style="margin:12px 0 0;font-size:12px;color:#9ca3af;">'
            f'You are receiving this because you subscribed to our newsletter. '
            f'<a href="{unsubscribe_url}" style="color:{ACCENT_COLOR};text-decoration:underline;">Unsubscribe</a>'
            f"</p>"
        )
    elif footer_note:
        unsubscribe_block = (
            f'<p style="margin:12px 0 0;font-size:12px;color:#9ca3af;">{footer_note}</p>'
        )

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background-color:#f1f5f9;color:{TEXT_COLOR};">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f1f5f9;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(11,92,46,0.08);">
          <tr>
            <td style="background:linear-gradient(135deg,{PRIMARY_COLOR} 0%,#063d1f 100%);padding:28px 32px;text-align:center;">
              {logo_section}
            </td>
          </tr>
          <tr>
            <td style="height:4px;background:{ACCENT_COLOR};font-size:0;line-height:0;">&nbsp;</td>
          </tr>
          <tr>
            <td style="padding:32px;line-height:1.65;font-size:15px;color:{TEXT_COLOR};">
              {body_content}
            </td>
          </tr>
          <tr>
            <td style="padding:24px 32px;background:{DARK_FOOTER};text-align:center;">
              <p style="margin:0;font-size:12px;color:#d1fae5;">
                &copy; {year} {site_title}. All rights reserved.
              </p>
              <p style="margin:8px 0 0;font-size:11px;color:#86efac;">
                Pure Himalayan herbal products — Purity Always Wins.
              </p>
              {unsubscribe_block}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def verification_email_html(
    recipient_name: str,
    verify_link: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> str:
    """Email verification after signup."""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">Thank you for signing up! Please verify your email address by clicking the button below.</p>
    <div style="margin:24px 0;">
      <a href="{verify_link}" style="display:inline-block;background:{ACCENT_COLOR};color:#1f2937;padding:14px 28px;text-decoration:none;font-weight:bold;border-radius:12px;">Verify Email</a>
    </div>
    <p style="margin:0 0 16px;color:#6b7280;font-size:14px;">If you did not create an account, please ignore this email.</p>
    <p style="margin:0;">This link expires in 24 hours.</p>
    """
    return _base_html("Verify Your Email", body, logo_url, site_title)


def verification_otp_email_html(
    recipient_name: str,
    otp: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    expire_minutes: int = 10,
) -> str:
    """Email verification OTP after signup."""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">Thank you for signing up! Use the OTP below to verify your email address in the app.</p>
    <div style="margin:24px 0;padding:24px;background:{LIGHT_BG};border-left:4px solid {ACCENT_COLOR};border-radius:8px;text-align:center;">
      <p style="margin:0 0 8px;font-size:12px;color:#6b7280;letter-spacing:2px;">YOUR VERIFICATION CODE</p>
      <p style="margin:0;font-size:32px;font-weight:800;letter-spacing:8px;color:{PRIMARY_COLOR};">{otp}</p>
    </div>
    <p style="margin:0 0 16px;color:#6b7280;font-size:14px;">If you did not create an account, please ignore this email.</p>
    <p style="margin:0;">This code expires in {expire_minutes} minutes.</p>
    """
    return _base_html("Verify Your Email", body, logo_url, site_title)


def password_reset_otp_email_html(
    recipient_name: str,
    otp: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    expire_minutes: int = 10,
) -> str:
    """Password reset OTP (app-based)."""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">You requested to reset your password. Use the OTP below in the app to set a new password.</p>
    <div style="margin:24px 0;padding:24px;background:{LIGHT_BG};border-left:4px solid {ACCENT_COLOR};border-radius:8px;text-align:center;">
      <p style="margin:0 0 8px;font-size:12px;color:#6b7280;letter-spacing:2px;">YOUR PASSWORD RESET CODE</p>
      <p style="margin:0;font-size:32px;font-weight:800;letter-spacing:8px;color:{PRIMARY_COLOR};">{otp}</p>
    </div>
    <p style="margin:0 0 16px;color:#6b7280;font-size:14px;">If you did not request this, please ignore this email. Your password will remain unchanged.</p>
    <p style="margin:0;">This code expires in {expire_minutes} minutes.</p>
    """
    return _base_html("Password Reset Code", body, logo_url, site_title)


def password_reset_email_html(
    recipient_name: str,
    reset_link: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> str:
    """Password reset request (link)."""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">You requested a password reset. Click the button below to set a new password.</p>
    <div style="margin:24px 0;">
      <a href="{reset_link}" style="display:inline-block;background:{ACCENT_COLOR};color:#1f2937;padding:14px 28px;text-decoration:none;font-weight:bold;border-radius:12px;">Reset Password</a>
    </div>
    <p style="margin:0 0 16px;color:#6b7280;font-size:14px;">If you did not request this, please ignore this email. Your password will remain unchanged.</p>
    <p style="margin:0;">This link expires in 1 hour.</p>
    """
    return _base_html("Password Reset Request", body, logo_url, site_title)


def newsletter_welcome_email_html(
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    contact_email: str | None = None,
    unsubscribe_url: str | None = None,
) -> str:
    """Newsletter subscription confirmation."""
    contact_line = (
        f'<p style="margin:16px 0 0;">Questions? Contact us at: '
        f'<a href="mailto:{contact_email}" style="color:{PRIMARY_COLOR};text-decoration:underline;">{contact_email}</a></p>'
        if contact_email
        else ""
    )
    body = f"""
    <p style="margin:0 0 16px;font-size:18px;font-weight:700;color:{PRIMARY_COLOR};">You're subscribed!</p>
    <p style="margin:0 0 16px;">Thank you for joining the {site_title} newsletter.</p>
    <p style="margin:0 0 16px;">You will receive exclusive herbal product deals, new arrivals, and updates straight to your inbox.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {ACCENT_COLOR};border-radius:8px;">
      <p style="margin:0 0 8px;font-weight:bold;color:{PRIMARY_COLOR};">What to expect:</p>
      <ul style="margin:0;padding-left:20px;">
        <li>Early access to sales and promotions</li>
        <li>New Himalayan product launches</li>
        <li>Wellness tips and guides</li>
      </ul>
    </div>
    {contact_line}
    """
    return _base_html(
        "Welcome to Our Newsletter",
        body,
        logo_url,
        site_title,
        unsubscribe_url=unsubscribe_url,
    )


def newsletter_admin_notify_email_html(
    email: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> str:
    body = f"""
    <p style="margin:0 0 16px;">A new newsletter subscription was received.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {ACCENT_COLOR};border-radius:8px;">
      <p style="margin:0;"><strong>Email:</strong> <a href="mailto:{email}" style="color:{PRIMARY_COLOR};">{email}</a></p>
    </div>
    """
    return _base_html("New Newsletter Subscriber", body, logo_url, site_title)


def newsletter_unsubscribed_email_html(
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> str:
    body = f"""
    <p style="margin:0 0 16px;">You have been unsubscribed from the {site_title} newsletter.</p>
    <p style="margin:0 0 16px;">You will no longer receive marketing emails from us. Transactional emails (orders, contact replies) may still be sent when needed.</p>
    <p style="margin:0;">If this was a mistake, you can subscribe again anytime from our website footer.</p>
    """
    return _base_html("Unsubscribed", body, logo_url, site_title)


def contact_thankyou_email_html(
    recipient_name: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    contact_email: str | None = None,
) -> str:
    """Thank-you email after contact form submission."""
    contact_line = f'<p style="margin:0;">You can also reach us at: <a href="mailto:{contact_email}" style="color:{PRIMARY_COLOR};text-decoration:underline;">{contact_email}</a></p>' if contact_email else ""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name},</p>
    <p style="margin:0 0 16px;">Thank you for reaching out! We have received your message and will get back to you shortly.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {PRIMARY_COLOR};border-radius:4px;">
      <p style="margin:0;font-weight:bold;">Our team typically responds within 24-48 hours.</p>
    </div>
    {contact_line}
    """
    return _base_html("We Received Your Message", body, logo_url, site_title)


def contact_admin_notify_email_html(
    name: str,
    email: str,
    subject: str,
    message: str,
    submission_type: str = "feedback",
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> str:
    """Admin notification when contact form is submitted."""
    body = f"""
    <p style="margin:0 0 16px;">A new contact form submission has been received.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {PRIMARY_COLOR};border-radius:4px;">
      <p style="margin:0 0 8px;"><strong>Name:</strong> {name}</p>
      <p style="margin:0 0 8px;"><strong>Email:</strong> <a href="mailto:{email}" style="color:{PRIMARY_COLOR};">{email}</a></p>
      <p style="margin:0 0 8px;"><strong>Subject:</strong> {subject}</p>
      <p style="margin:0 0 8px;"><strong>Type:</strong> {submission_type}</p>
      <p style="margin:16px 0 0;"><strong>Message:</strong></p>
      <p style="margin:8px 0 0;white-space:pre-wrap;">{message}</p>
    </div>
    """
    return _base_html("New Contact Form Submission", body, logo_url, site_title)


def order_confirmed_email_html(
    recipient_name: str,
    order_number: str,
    total_amount: str,
    status: str = "pending",
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    orders_url: str | None = None,
) -> str:
    """Order / inquiry confirmation email."""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">Thank you for your product inquiry with {site_title}. We have received your request and our team will contact you shortly to confirm details — no online payment is required at this stage.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {ACCENT_COLOR};border-radius:8px;">
      <p style="margin:0 0 8px;"><strong>Inquiry / Order ID:</strong> #{order_number}</p>
      <p style="margin:0 0 8px;"><strong>Status:</strong> {status}</p>
      <p style="margin:0 0 8px;"><strong>Estimated total:</strong> {total_amount}</p>
    </div>
    <p style="margin:0;">If you have any questions, reply to this email or use our contact form.</p>
    """
    return _base_html(
        "Order Inquiry Received",
        body,
        logo_url,
        site_title,
        footer_note="This is a transactional email related to your inquiry.",
    )


def order_status_update_email_html(
    recipient_name: str,
    order_number: str,
    new_status: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    orders_url: str | None = None,
) -> str:
    """Email when order status is updated (any step). order_number: 8-digit tracking ID."""
    orders_link = f'<p style="margin:16px 0 0;"><a href="{orders_url}" style="color:{PRIMARY_COLOR};font-weight:bold;">View order details</a></p>' if orders_url else ""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">Your order status has been updated.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {PRIMARY_COLOR};border-radius:4px;">
      <p style="margin:0 0 8px;"><strong>Order ID:</strong> #{order_number}</p>
      <p style="margin:0 0 8px;"><strong>New status:</strong> {new_status}</p>
    </div>
    {orders_link}
    """
    return _base_html("Order Status Update", body, logo_url, site_title)


def order_admin_notify_email_html(
    order_number: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str | None,
    customer_country: str | None,
    customer_address: str | None,
    total_amount: str,
    items_html: str,
    notes: str | None = None,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> str:
    notes_block = f'<p style="margin:12px 0 0;"><strong>Notes:</strong> {notes}</p>' if notes else ""
    body = f"""
    <p style="margin:0 0 16px;">A new product inquiry / order was submitted on {site_title}.</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {PRIMARY_COLOR};border-radius:4px;">
      <p style="margin:0 0 8px;"><strong>Order ID:</strong> #{order_number}</p>
      <p style="margin:0 0 8px;"><strong>Customer:</strong> {customer_name}</p>
      <p style="margin:0 0 8px;"><strong>Email:</strong> {customer_email}</p>
      <p style="margin:0 0 8px;"><strong>Phone:</strong> {customer_phone or '—'}</p>
      <p style="margin:0 0 8px;"><strong>Country:</strong> {customer_country or '—'}</p>
      <p style="margin:0 0 8px;"><strong>Address:</strong> {customer_address or '—'}</p>
      <p style="margin:0 0 8px;"><strong>Estimated total:</strong> {total_amount}</p>
      {notes_block}
    </div>
    <p style="margin:16px 0 8px;"><strong>Items:</strong></p>
    <table style="width:100%;border-collapse:collapse;font-size:14px;margin:0 0 16px;">
      <thead>
        <tr style="background:#e5e7eb;">
          <th style="text-align:left;padding:10px;border:1px solid #d1d5db;">Product</th>
          <th style="text-align:center;padding:10px;border:1px solid #d1d5db;">Qty</th>
          <th style="text-align:right;padding:10px;border:1px solid #d1d5db;">Line</th>
        </tr>
      </thead>
      <tbody>
        {items_html}
      </tbody>
    </table>
    <p style="margin:0;color:#6b7280;font-size:13px;">Reply from the admin Orders page to email the customer.</p>
    """
    return _base_html("New Order Inquiry", body, logo_url, site_title)


def order_reply_email_html(
    recipient_name: str,
    order_number: str,
    message: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
) -> str:
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">We have an update regarding your order <strong>#{order_number}</strong>:</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {ACCENT_COLOR};border-radius:4px;white-space:pre-wrap;">
      {message}
    </div>
    <p style="margin:16px 0 0;">If you have questions, reply to this email or contact us through the website.</p>
    """
    return _base_html("Order Update", body, logo_url, site_title)


def order_completed_email_html(
    recipient_name: str,
    order_number: str,
    total_amount: str,
    items_html: str,
    logo_url: str | None = None,
    site_title: str = "Nepal Origin",
    orders_url: str | None = None,
) -> str:
    """Order completed email with list of order items. order_number: 8-digit tracking ID."""
    orders_link = f'<p style="margin:16px 0 0;"><a href="{orders_url}" style="color:{PRIMARY_COLOR};font-weight:bold;">View order details</a></p>' if orders_url else ""
    body = f"""
    <p style="margin:0 0 16px;">Dear {recipient_name or 'Customer'},</p>
    <p style="margin:0 0 16px;">Your order has been completed. Thank you for shopping with us!</p>
    <div style="margin:24px 0;padding:16px;background:{LIGHT_BG};border-left:4px solid {ACCENT_COLOR};border-radius:4px;">
      <p style="margin:0 0 8px;"><strong>Order ID:</strong> #{order_number}</p>
      <p style="margin:0 0 8px;"><strong>Total:</strong> {total_amount}</p>
    </div>
    <p style="margin:16px 0 8px;"><strong>Order items:</strong></p>
    <table style="width:100%;border-collapse:collapse;font-size:14px;margin:0 0 16px;">
      <thead>
        <tr style="background:#e5e7eb;">
          <th style="text-align:left;padding:10px;border:1px solid #d1d5db;">Product</th>
          <th style="text-align:center;padding:10px;border:1px solid #d1d5db;">Qty</th>
          <th style="text-align:right;padding:10px;border:1px solid #d1d5db;">Price</th>
        </tr>
      </thead>
      <tbody>
        {items_html}
      </tbody>
    </table>
    {orders_link}
    """
    return _base_html("Order Completed", body, logo_url, site_title)
