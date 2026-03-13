"""
Email sender – sends the rendered HTML digest via SMTP (default: Gmail).

Gmail setup:
  1. Enable 2-Step Verification on your Google account.
  2. Create an App Password at https://myaccount.google.com/apppasswords.
  3. Set EMAIL_SENDER and EMAIL_PASSWORD to your Gmail address and App Password.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_digest(
    subject: str,
    html_body: str,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
    sender_email: str | None = None,
    sender_password: str | None = None,
    recipient_email: str | None = None,
) -> bool:
    """
    Send the HTML digest email.

    Credentials are read from environment variables if not provided:
      EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT

    Returns True on success, False on failure.
    """
    sender = sender_email or os.environ.get("EMAIL_SENDER", "")
    password = sender_password or os.environ.get("EMAIL_PASSWORD", "")
    recipient_raw = recipient_email or os.environ.get("EMAIL_RECIPIENT", "")

    if not sender or not password or not recipient_raw:
        logger.error(
            "Email credentials not configured. "
            "Set EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT."
        )
        return False

    # Support multiple recipients (comma-separated)
    recipients = [r.strip() for r in recipient_raw.split(",") if r.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AI 前沿日报 <{sender}>"
    msg["To"] = ", ".join(recipients)

    # Fallback plain-text part
    plain_text = (
        "您的邮件客户端不支持 HTML 邮件，请使用支持 HTML 的客户端查看本日报。\n"
        "This email requires an HTML-capable mail client."
    )
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        logger.info("Digest sent to: %s", ", ".join(recipients))
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "SMTP authentication failed. "
            "For Gmail, use an App Password (not your account password)."
        )
        return False
    except Exception as exc:
        logger.error("Failed to send email: %s", exc)
        return False
