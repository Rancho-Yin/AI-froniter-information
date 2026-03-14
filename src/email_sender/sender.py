"""
Email sender – uses 163邮箱 SMTP to send the HTML digest.

163邮箱 SMTP setup:
  1. 登录 mail.163.com → 设置 → POP3/SMTP/IMAP
  2. 开启 SMTP 服务
  3. 在「授权密码管理」中生成授权码（非登录密码）
  4. 将以下环境变量设置为 GitHub Secrets:
       SMTP_USER        – 163邮箱地址，如 yourname@163.com
       SMTP_PASSWORD    – 163邮箱授权码（16位）
       EMAIL_SENDER     – 同 SMTP_USER
       EMAIL_RECIPIENT  – 收件人，多个用逗号分隔，如 a@x.com,b@y.com
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
    smtp_server: str = "smtpdm.volcengine.com",
    smtp_port: int = 465,
    sender_email: str | None = None,
    recipient_email: str | None = None,
) -> bool:
    """
    Send the HTML digest email via 火山引擎邮件推送 SMTP.

    Credentials are read from environment variables:
      VOLCENGINE_SMTP_USER, VOLCENGINE_SMTP_PASSWORD, EMAIL_SENDER, EMAIL_RECIPIENT

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

    # 163邮箱 SMTP 对多收件人有反垃圾限制，逐一发送确保每位都能收到
    failed = []
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
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
            "SMTP authentication failed. Check SMTP_USER and SMTP_PASSWORD."
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
