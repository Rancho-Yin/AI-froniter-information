"""
Email sender – uses Gmail SMTP to send the HTML digest.

Gmail SMTP setup:
  1. Go to your Google Account → Security → 2-Step Verification (must be ON)
  2. Search "App passwords" → create one for "Mail" → copy the 16-char password
  3. Set the following GitHub Secrets:
       SMTP_USER        – your Gmail address, e.g. yourname@gmail.com
       SMTP_PASSWORD    – the 16-char App Password (NOT your Gmail login password)
       EMAIL_SENDER     – same as SMTP_USER
       EMAIL_RECIPIENT  – comma-separated recipients, e.g. a@gmail.com,b@qq.com
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
    recipient_email: str | None = None,
) -> bool:
    """
    Send the HTML digest email via Gmail SMTP (STARTTLS).

    Credentials are read from environment variables:
      SMTP_USER, SMTP_PASSWORD, EMAIL_SENDER, EMAIL_RECIPIENT

    Returns True on success, False on failure.
    """
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    sender = sender_email or os.environ.get("EMAIL_SENDER", "")
    recipient_raw = recipient_email or os.environ.get("EMAIL_RECIPIENT", "")

    if not smtp_user or not smtp_password or not sender or not recipient_raw:
        logger.error(
            "Email credentials not configured. "
            "Set SMTP_USER, SMTP_PASSWORD, EMAIL_SENDER, EMAIL_RECIPIENT."
        )
        return False

    recipients = [r.strip() for r in recipient_raw.split(",") if r.strip()]

    plain_text = (
        "您的邮件客户端不支持 HTML 邮件，请使用支持 HTML 的客户端查看本日报。\n"
        "This email requires an HTML-capable mail client."
    )

    failed = []
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_password)
            for recipient in recipients:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"AI 前沿日报 <{sender}>"
                msg["To"] = recipient
                msg.attach(MIMEText(plain_text, "plain", "utf-8"))
                msg.attach(MIMEText(html_body, "html", "utf-8"))
                try:
                    server.sendmail(sender, [recipient], msg.as_string())
                    logger.info("Sent to: %s", recipient)
                except Exception as exc:
                    logger.error("Failed to send to %s: %s", recipient, exc)
                    failed.append(recipient)
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "SMTP authentication failed. "
            "Make sure SMTP_PASSWORD is a Gmail App Password, not your login password. "
            "Generate one at: Google Account → Security → 2-Step Verification → App passwords"
        )
        return False
    except Exception as exc:
        logger.error("SMTP connection error: %s", exc)
        return False

    if failed:
        logger.warning("Failed recipients: %s", ", ".join(failed))
    success_count = len(recipients) - len(failed)
    logger.info("Digest sent to %d/%d recipients.", success_count, len(recipients))
    return success_count > 0
