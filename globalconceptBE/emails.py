"""
GrazConcept transactional email service.

All outbound emails go through here.  Django's email backend is configured
in settings.py (Mailgun SMTP when MAILGUN_API_KEY is set, console otherwise).

Public API
----------
send_password_reset_email(user, reset_url)
send_welcome_email(user)
send_admin_application_notification(application_type, applicant_name,
                                    applicant_email, application_id,
                                    extra_fields=None)
"""

import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Brand constants ───────────────────────────────────────────────────────────

BRAND_NAME   = "GrazConcept"
BRAND_COLOR  = "#8B2B8C"          # primary purple
BRAND_LIGHT  = "#f5e6f5"
BRAND_URL    = getattr(settings, "FRONTEND_URL", "https://app.grazconcept.com.ng")
SUPPORT_EMAIL = "support@grazconcept.com.ng"
LOGO_URL     = getattr(settings, "BRAND_LOGO_URL", "")   # optional CDN logo

# ── Shared HTML scaffolding ───────────────────────────────────────────────────

def _wrap(body_html: str, preview_text: str = "") -> str:
    """Wrap a body block in the standard GrazConcept email shell."""
    preview = f'<div style="display:none;font-size:1px;color:#fff;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">{preview_text}</div>' if preview_text else ""
    logo_block = (
        f'<img src="{LOGO_URL}" alt="{BRAND_NAME}" height="40" style="display:block;margin:0 auto 4px;">'
        if LOGO_URL else
        f'<span style="font-size:22px;font-weight:800;color:{BRAND_COLOR};">{BRAND_NAME}</span>'
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{BRAND_NAME}</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f8;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
{preview}
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f8;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

      <!-- Header -->
      <tr>
        <td style="background:{BRAND_COLOR};padding:32px 40px;text-align:center;">
          {logo_block}
          <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,0.8);letter-spacing:1px;text-transform:uppercase;">Travel & FinTech Solutions</p>
        </td>
      </tr>

      <!-- Body -->
      <tr>
        <td style="padding:40px 40px 32px;">
          {body_html}
        </td>
      </tr>

      <!-- Footer -->
      <tr>
        <td style="background:#f8f4f8;padding:24px 40px;text-align:center;border-top:1px solid #ede8ed;">
          <p style="margin:0 0 8px;font-size:12px;color:#888;">
            &copy; 2025 {BRAND_NAME}. All rights reserved.
          </p>
          <p style="margin:0;font-size:12px;color:#aaa;">
            Questions? Email us at
            <a href="mailto:{SUPPORT_EMAIL}" style="color:{BRAND_COLOR};text-decoration:none;">{SUPPORT_EMAIL}</a>
          </p>
          <p style="margin:8px 0 0;font-size:11px;color:#ccc;">
            You received this email because an action was taken on your {BRAND_NAME} account.
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""


def _send(subject: str, to: list[str], text_body: str, html_body: str):
    """
    Send an email via the configured backend (Brevo SMTP by default).
    Logs the full traceback on failure and re-raises so callers can decide
    whether to surface the error or swallow it.
    """
    from_addr = settings.DEFAULT_FROM_EMAIL
    logger.info(
        "Sending email: subject=%r  to=%r  from=%r  host=%s:%s",
        subject, to, from_addr,
        getattr(settings, 'EMAIL_HOST', '?'),
        getattr(settings, 'EMAIL_PORT', '?'),
    )
    msg = EmailMultiAlternatives(subject, text_body, from_addr, to)
    msg.attach_alternative(html_body, "text/html")
    try:
        msg.send(fail_silently=False)
        logger.info("Email sent OK: subject=%r to=%r", subject, to)
    except Exception as exc:
        logger.exception(          # full traceback in server logs
            "Email send FAILED: subject=%r to=%r — %s: %s",
            subject, to, type(exc).__name__, exc,
        )
        raise   # re-raise so callers can handle or report


# ── Password reset ────────────────────────────────────────────────────────────

def send_password_reset_email(user, reset_url: str):
    """Send a branded password-reset link to the user."""
    name = user.first_name or user.email.split("@")[0]
    subject = f"Reset your {BRAND_NAME} password"
    preview = "We received a request to reset your password."

    body_html = f"""
<h2 style="margin:0 0 8px;font-size:24px;font-weight:800;color:#1a1a2e;">Password Reset</h2>
<p style="margin:0 0 20px;font-size:15px;color:#555;">Hi {name},</p>

<p style="margin:0 0 20px;font-size:15px;color:#555;line-height:1.6;">
  We received a request to reset the password for your {BRAND_NAME} account.
  Click the button below to choose a new password.
</p>

<div style="text-align:center;margin:32px 0;">
  <a href="{reset_url}"
     style="display:inline-block;background:{BRAND_COLOR};color:#fff;font-weight:700;
            font-size:15px;text-decoration:none;padding:14px 36px;border-radius:10px;
            letter-spacing:0.3px;">
    Reset Password
  </a>
</div>

<p style="margin:0 0 8px;font-size:13px;color:#888;line-height:1.6;">
  Or paste this link into your browser:
</p>
<p style="margin:0 0 24px;font-size:12px;color:#aaa;word-break:break-all;">
  <a href="{reset_url}" style="color:{BRAND_COLOR};text-decoration:none;">{reset_url}</a>
</p>

<div style="background:#fff8e7;border:1px solid #fde68a;border-radius:10px;padding:14px 18px;margin-bottom:24px;">
  <p style="margin:0;font-size:13px;color:#92400e;line-height:1.6;">
    ⚠ This link expires in <strong>1 hour</strong>.
    If you didn't request a password reset, you can safely ignore this email.
  </p>
</div>

<p style="margin:0;font-size:14px;color:#555;">
  — The {BRAND_NAME} Team
</p>"""

    text_body = (
        f"Hi {name},\n\n"
        f"We received a request to reset your {BRAND_NAME} password.\n\n"
        f"Reset link (expires in 1 hour):\n{reset_url}\n\n"
        f"If you didn't request this, ignore this email.\n\n"
        f"— The {BRAND_NAME} Team"
    )

    _send(subject, [user.email], text_body, _wrap(body_html, preview))


# ── Welcome email ─────────────────────────────────────────────────────────────

def send_welcome_email(user):
    """Send a welcome email to a newly registered user."""
    name = user.first_name or user.email.split("@")[0]
    subject = f"Welcome to {BRAND_NAME}!"
    preview = f"Your account is ready — start exploring."
    dashboard_url = f"{BRAND_URL}/dashboard"

    body_html = f"""
<h2 style="margin:0 0 8px;font-size:24px;font-weight:800;color:#1a1a2e;">Welcome aboard! 🎉</h2>
<p style="margin:0 0 20px;font-size:15px;color:#555;">Hi {name},</p>

<p style="margin:0 0 16px;font-size:15px;color:#555;line-height:1.6;">
  Your {BRAND_NAME} account is ready. We're excited to help you with visa applications,
  travel bookings, bill payments, and more — all in one place.
</p>

<div style="background:{BRAND_LIGHT};border-radius:12px;padding:20px 24px;margin-bottom:24px;">
  <p style="margin:0 0 10px;font-size:14px;font-weight:700;color:{BRAND_COLOR};">
    🚀 Get started quickly:
  </p>
  <ul style="margin:0;padding-left:20px;font-size:14px;color:#555;line-height:1.9;">
    <li>Complete your profile</li>
    <li>Apply for a study, work, or pilgrimage visa</li>
    <li>Top up your wallet &amp; pay utility bills</li>
    <li>Track all your applications in one dashboard</li>
  </ul>
</div>

<div style="text-align:center;margin:32px 0;">
  <a href="{dashboard_url}"
     style="display:inline-block;background:{BRAND_COLOR};color:#fff;font-weight:700;
            font-size:15px;text-decoration:none;padding:14px 36px;border-radius:10px;">
    Go to Dashboard
  </a>
</div>

<p style="margin:0;font-size:14px;color:#555;">
  — The {BRAND_NAME} Team
</p>"""

    text_body = (
        f"Hi {name},\n\n"
        f"Welcome to {BRAND_NAME}! Your account is ready.\n\n"
        f"Dashboard: {dashboard_url}\n\n"
        f"— The {BRAND_NAME} Team"
    )

    _send(subject, [user.email], text_body, _wrap(body_html, preview))


# ── Admin: new application notification ──────────────────────────────────────

def send_admin_application_notification(
    application_type: str,
    applicant_name: str,
    applicant_email: str,
    application_id,
    extra_fields: dict | None = None,
):
    """
    Notify the admin team whenever a new application is submitted.

    Parameters
    ----------
    application_type : str
        Human-readable type, e.g. "Study Visa", "Work Visa", "Pilgrimage", "Vacation"
    applicant_name   : str
    applicant_email  : str
    application_id   : int | str
    extra_fields     : dict of {label: value} to show in the detail table (optional)
    """
    admin_email = getattr(settings, "ADMIN_NOTIFICATION_EMAIL", "admin@grazconcept.com.ng")
    admin_url   = f"{BRAND_URL}/admin/applications"
    subject     = f"[{BRAND_NAME}] New {application_type} Application — #{application_id}"
    preview     = f"New application from {applicant_name} ({applicant_email})"

    # Build extra rows
    extra_rows = ""
    if extra_fields:
        for label, value in extra_fields.items():
            extra_rows += f"""
<tr>
  <td style="padding:8px 12px;font-size:13px;color:#666;background:#fafafa;border-bottom:1px solid #eee;font-weight:600;width:40%;">{label}</td>
  <td style="padding:8px 12px;font-size:13px;color:#333;border-bottom:1px solid #eee;">{value}</td>
</tr>"""

    body_html = f"""
<div style="display:inline-block;background:{BRAND_LIGHT};color:{BRAND_COLOR};font-size:12px;
            font-weight:700;padding:4px 12px;border-radius:20px;margin-bottom:16px;
            text-transform:uppercase;letter-spacing:0.5px;">
  New Application
</div>

<h2 style="margin:0 0 6px;font-size:22px;font-weight:800;color:#1a1a2e;">
  {application_type} Application
</h2>
<p style="margin:0 0 24px;font-size:14px;color:#888;">Application #&nbsp;{application_id}</p>

<table width="100%" cellpadding="0" cellspacing="0" style="border-radius:10px;overflow:hidden;border:1px solid #e8e8e8;margin-bottom:24px;">
  <tr>
    <td style="padding:8px 12px;font-size:13px;color:#666;background:#fafafa;border-bottom:1px solid #eee;font-weight:600;width:40%;">Applicant</td>
    <td style="padding:8px 12px;font-size:13px;color:#333;border-bottom:1px solid #eee;">{applicant_name}</td>
  </tr>
  <tr>
    <td style="padding:8px 12px;font-size:13px;color:#666;background:#fafafa;border-bottom:1px solid #eee;font-weight:600;">Email</td>
    <td style="padding:8px 12px;font-size:13px;color:#333;border-bottom:1px solid #eee;">
      <a href="mailto:{applicant_email}" style="color:{BRAND_COLOR};text-decoration:none;">{applicant_email}</a>
    </td>
  </tr>
  <tr>
    <td style="padding:8px 12px;font-size:13px;color:#666;background:#fafafa;border-bottom:1px solid #eee;font-weight:600;">Application Type</td>
    <td style="padding:8px 12px;font-size:13px;color:#333;border-bottom:1px solid #eee;">{application_type}</td>
  </tr>
  {extra_rows}
</table>

<div style="text-align:center;margin:28px 0;">
  <a href="{admin_url}"
     style="display:inline-block;background:{BRAND_COLOR};color:#fff;font-weight:700;
            font-size:14px;text-decoration:none;padding:12px 32px;border-radius:10px;">
    View in Admin Panel
  </a>
</div>

<p style="margin:16px 0 0;font-size:12px;color:#aaa;text-align:center;">
  This is an automated notification from {BRAND_NAME}.
</p>"""

    text_body = (
        f"New {application_type} Application — #{application_id}\n\n"
        f"Applicant : {applicant_name}\n"
        f"Email     : {applicant_email}\n"
    )
    if extra_fields:
        for label, value in extra_fields.items():
            text_body += f"{label:<20}: {value}\n"
    text_body += f"\nView in admin: {admin_url}\n"

    _send(subject, [admin_email], text_body, _wrap(body_html, preview))
