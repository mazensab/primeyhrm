# ============================================================
# 📂 api/public/contact.py
# Primey HR Cloud
# Public Contact API
# ============================================================
# API عام لاستقبال رسائل صفحة التواصل من اللاندنق بيج
# ثم إرسالها إلى إيميل النظام المحدد.
# ============================================================

from __future__ import annotations

import json
import logging
from typing import Dict

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

# ============================================================
# 🔒 Contact Destination
# ============================================================

CONTACT_RECEIVER_EMAIL = "info@primeyride.com"

# ============================================================
# 🖼️ Primey Logo
# ============================================================

LOGO_URL = (
    "https://drive.google.com/uc?export=view&id=1a0Y1SK3n-Hn9QDZa7Ge24r3--B8zXbTd"
)

# ============================================================
# ✅ Allowed Subjects
# ============================================================

ALLOWED_SUBJECTS = {
    "Sales Inquiry",
    "Demo Request",
    "Technical Support",
    "Billing & Subscription",
    "Partnership",
    "General Inquiry",
}

# ============================================================
# ✅ Helpers
# ============================================================

def _bad_request(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse(
        {
            "success": False,
            "message": message,
        },
        status=status,
    )


def _validate_payload(payload: Dict) -> tuple[bool, str]:
    first_name = str(payload.get("first_name", "")).strip()
    last_name = str(payload.get("last_name", "")).strip()
    email = str(payload.get("email", "")).strip()
    subject = str(payload.get("subject", "")).strip()
    message = str(payload.get("message", "")).strip()

    if not first_name or len(first_name) > 50:
        return False, "Invalid first name."

    if not last_name or len(last_name) > 50:
        return False, "Invalid last name."

    if not email or "@" not in email or len(email) > 254:
        return False, "Invalid email address."

    if subject not in ALLOWED_SUBJECTS:
        return False, "Invalid subject selected."

    if not message or len(message) < 2 or len(message) > 2000:
        return False, "Invalid message length."

    return True, ""


def _build_contact_email_html(
    *,
    full_name: str,
    email: str,
    subject: str,
    message: str,
) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en" dir="ltr">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Primey Contact Message</title>
      </head>
      <body style="margin:0; padding:0; background-color:#f3f4f6; font-family:Arial, Helvetica, sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f3f4f6; margin:0; padding:24px 0;">
          <tr>
            <td align="center">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:700px; background:#ffffff; border-radius:18px; overflow:hidden; border:1px solid #e5e7eb;">
                
                <!-- Header -->
                <tr>
                  <td style="background:#000000; padding:28px 24px; text-align:center;">
                    <img
                      src="{LOGO_URL}"
                      alt="Primey"
                      style="max-width:170px; height:auto; display:block; margin:0 auto 14px auto;"
                    />
                    <div style="color:#ffffff; font-size:22px; font-weight:700; line-height:1.4;">
                      New Contact Message
                    </div>
                    <div style="color:#d1d5db; font-size:13px; margin-top:6px;">
                      A new inquiry has been submitted from the public website.
                    </div>
                  </td>
                </tr>

                <!-- Body -->
                <tr>
                  <td style="padding:28px 24px;">
                    <div style="font-size:14px; color:#111827; margin-bottom:18px; line-height:1.8;">
                      Hello Primey Team,
                      <br />
                      You have received a new contact request from the landing page.
                    </div>

                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse; width:100%; font-size:14px; margin-bottom:20px;">
                      <tr>
                        <td style="padding:12px 14px; border:1px solid #e5e7eb; background:#f9fafb; width:180px; font-weight:700; color:#111827;">
                          Subject
                        </td>
                        <td style="padding:12px 14px; border:1px solid #e5e7eb; color:#111827;">
                          {escape(subject)}
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:12px 14px; border:1px solid #e5e7eb; background:#f9fafb; font-weight:700; color:#111827;">
                          Full Name
                        </td>
                        <td style="padding:12px 14px; border:1px solid #e5e7eb; color:#111827;">
                          {escape(full_name)}
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:12px 14px; border:1px solid #e5e7eb; background:#f9fafb; font-weight:700; color:#111827;">
                          Email Address
                        </td>
                        <td style="padding:12px 14px; border:1px solid #e5e7eb; color:#111827;">
                          <a href="mailto:{escape(email)}" style="color:#111827; text-decoration:none;">
                            {escape(email)}
                          </a>
                        </td>
                      </tr>
                    </table>

                    <div style="margin-top:4px; margin-bottom:10px; font-size:14px; font-weight:700; color:#111827;">
                      Message
                    </div>

                    <div style="border:1px solid #e5e7eb; background:#f9fafb; border-radius:12px; padding:16px; color:#111827; font-size:14px; line-height:1.9; white-space:pre-wrap;">
                      {escape(message)}
                    </div>

                    <div style="margin-top:22px; font-size:12px; color:#6b7280; line-height:1.8;">
                      This email was generated automatically from the Primey public contact form.
                    </div>
                  </td>
                </tr>

                <!-- Footer -->
                <tr>
                  <td style="padding:18px 24px; border-top:1px solid #e5e7eb; background:#ffffff; text-align:center; font-size:12px; color:#6b7280;">
                    © Primey — Public Contact Notification
                  </td>
                </tr>

              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


# ============================================================
# 📩 Public Contact Submit
# ============================================================

@csrf_exempt
@require_POST
def public_contact_submit(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return _bad_request("Invalid JSON payload.")

    is_valid, error_message = _validate_payload(payload)
    if not is_valid:
        return _bad_request(error_message)

    first_name = str(payload.get("first_name", "")).strip()
    last_name = str(payload.get("last_name", "")).strip()
    email = str(payload.get("email", "")).strip()
    subject = str(payload.get("subject", "")).strip()
    message = str(payload.get("message", "")).strip()

    full_name = f"{first_name} {last_name}".strip()

    email_subject = f"[Primey Contact] {subject} — {full_name}"

    text_body = (
        "New contact message received from Primey landing page.\n\n"
        f"Subject: {subject}\n"
        f"Full Name: {full_name}\n"
        f"Email: {email}\n\n"
        "Message:\n"
        f"{message}\n"
    )

    html_body = _build_contact_email_html(
        full_name=full_name,
        email=email,
        subject=subject,
        message=message,
    )

    try:
        msg = EmailMultiAlternatives(
            subject=email_subject,
            body=text_body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[CONTACT_RECEIVER_EMAIL],
            reply_to=[email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        return JsonResponse(
            {
                "success": True,
                "message": "Your message has been sent successfully.",
            },
            status=200,
        )

    except Exception as exc:
        logger.exception("Public contact email sending failed: %s", exc)
        return JsonResponse(
            {
                "success": False,
                "message": "Failed to send message. Please try again later.",
            },
            status=500,
        )