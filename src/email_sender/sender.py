"""
Email sender – uses 火山引擎邮件推送 SMTP to send the HTML digest.

火山引擎邮件推送 setup:
  1. 登录 console.volcengine.com → 搜索「邮件推送」→ 开通服务
  2. 添加发信域名并完成验证
  3. 添加发信地址（即 EMAIL_SENDER）
  4. 在「SMTP发送」页面获取 SMTP 用户名和密码
  5. 将以下环境变量设置为 GitHub Secrets:
       VOLCENGINE_SMTP_USER     – SMTP 用户名
       VOLCENGINE_SMTP_PASSWORD – SMTP 密码
       EMAIL_SENDER             – 发信地址（在火山引擎中配置的）
       EMAIL_RECIPIENT          – 收件人，多个用逗号分隔
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
    smtp_user = os.environ.get("VOLCENGINE_SMTP_USER", "")
    smtp_password = os.environ.get("VOLCENGINE_SMTP_PASSWORD", "")
    sender = sender_email or os.environ.get("EMAIL_SENDER", "")
    recipient_raw = recipient_email or os.environ.get("EMAIL_RECIPIENT", "")

    if not smtp_user or not smtp_password or not sender or not recipient_raw:
        logger.error(
            "Email credentials not configured. "
            "Set VOLCENGINE_SMTP_USER, VOLCENGINE_SMTP_PASSWORD, EMAIL_SENDER, EMAIL_RECIPIENT."
        )
        return False

    recipients = [r.strip() for r in recipient_raw.split(",") if r.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AI 前沿日报 <{sender}>"
    msg["To"] = ", ".join(recipients)

    plain_text = (
        "您的邮件客户端不支持 HTML 邮件，请使用支持 HTML 的客户端查看本日报。\n"
        "This email requires an HTML-capable mail client."
    )
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(sender, recipients, msg.as_string())
        logger.info("Digest sent to: %s", ", ".join(recipients))
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "SMTP authentication failed. "
            "Check VOLCENGINE_SMTP_USER and VOLCENGINE_SMTP_PASSWORD."
        )
        return False
    except Exception as exc:
        logger.error("Failed to send email: %s", exc)
        return False
