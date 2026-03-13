"""
Email sender – uses the Resend API to send the HTML digest.

Setup:
  1. Sign up at https://resend.com (free tier: 3 000 emails/month).
  2. Verify your sending domain (or use Resend's onboarding address for testing).
  3. Create an API key and add it as the RESEND_API_KEY GitHub secret.
  4. Set EMAIL_SENDER to an address on your verified domain, e.g. digest@yourdomain.com.
     (For quick testing without a domain, use: onboarding@resend.dev → recipient must be
      your own Resend-verified email address.)
  5. Set EMAIL_RECIPIENT to the destination address (comma-separated for multiple).
"""

import logging
import os

import resend

logger = logging.getLogger(__name__)


def send_digest(
    subject: str,
    html_body: str,
    sender_email: str | None = None,
    recipient_email: str | None = None,
    api_key: str | None = None,
) -> bool:
    """
    Send the HTML digest email via Resend.

    Credentials are read from environment variables if not provided:
      RESEND_API_KEY, EMAIL_SENDER, EMAIL_RECIPIENT

    Returns True on success, False on failure.
    """
    resolved_key = api_key or os.environ.get("RESEND_API_KEY", "")
    sender = sender_email or os.environ.get("EMAIL_SENDER", "")
    recipient_raw = recipient_email or os.environ.get("EMAIL_RECIPIENT", "")

    if not resolved_key or not sender or not recipient_raw:
        logger.error(
            "Email credentials not configured. "
            "Set RESEND_API_KEY, EMAIL_SENDER, EMAIL_RECIPIENT."
        )
        return False

    recipients = [r.strip() for r in recipient_raw.split(",") if r.strip()]

    resend.api_key = resolved_key

    try:
        params: resend.Emails.SendParams = {
            "from": f"AI 前沿日报 <{sender}>",
            "to": recipients,
            "subject": subject,
            "html": html_body,
        }
        email = resend.Emails.send(params)
        logger.info("Digest sent via Resend, id=%s to: %s", email["id"], ", ".join(recipients))
        return True
    except Exception as exc:
        logger.error("Resend API error: %s", exc)
        return False
