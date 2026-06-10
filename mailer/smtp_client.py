import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import logging

from config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    subject: str
    body: str
    to: list[str]
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    attachment_path: Optional[str] = None


class SMTPClient:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()

    def send(
        self,
        subject: str,
        body: str,
        to: list[str],
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        attachment_path: Optional[str] = None,
    ) -> None:
        msg = MIMEMultipart()
        msg["From"] = self.settings.email_from
        msg["Subject"] = subject
        msg["To"] = ", ".join(to)

        if cc:
            msg["Cc"] = ", ".join(cc)
            all_recipients = to + cc
        else:
            all_recipients = to

        if bcc:
            all_recipients.extend(bcc)

        msg.attach(MIMEText(body, "plain"))

        if attachment_path:
            path = Path(attachment_path)
            if path.exists():
                with open(path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{path.name}"',
                )
                msg.attach(part)
            else:
                logger.warning("Attachment not found: %s", path)

        context = ssl.create_default_context()

        logger.info(
            "Sending email via %s:%d to %s",
            self.settings.smtp_host,
            self.settings.smtp_port,
            all_recipients,
        )

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
            if self.settings.smtp_use_tls:
                server.starttls(context=context)
            if self.settings.smtp_user:
                server.login(self.settings.smtp_user, self.settings.smtp_password)
            server.sendmail(
                self.settings.email_from,
                all_recipients,
                msg.as_string(),
            )

        logger.info("Email sent successfully to %s", all_recipients)
