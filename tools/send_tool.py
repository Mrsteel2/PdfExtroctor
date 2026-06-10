from typing import Optional

from tools.registry import tool
from mailer.smtp_client import SMTPClient
from config import get_settings


@tool(
    name="send_report",
    description="Send a report via email using SMTP configuration.",
    subject={"type": "string", "description": "Email subject"},
    body={"type": "string", "description": "Email body text"},
    attachment_path={"type": "string", "description": "Optional file path to attach"},
    to={"type": "string", "description": "Recipient email (overrides config)"},
)
def send_report(
    subject: str,
    body: str,
    attachment_path: Optional[str] = None,
    to: Optional[str] = None,
) -> dict:
    settings = get_settings()
    recipients = [to] if to else [settings.email_to]
    cc = None
    if settings.email_cc and not to:
        cc = [settings.email_cc]

    client = SMTPClient()
    client.send(
        subject=subject,
        body=body,
        to=recipients,
        cc=cc,
        attachment_path=attachment_path,
    )
    return {
        "status": "sent",
        "to": recipients,
        "cc": cc,
        "subject": subject,
    }
