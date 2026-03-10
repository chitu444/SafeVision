"""
alerts/email_alert.py
=====================
SMTP email alerts with optional file attachments.
All credentials are read from config.settings so they can be overridden
via environment variables without touching this file.
"""

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config.settings import (
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_RECEIVER,
    EMAIL_SMTP_SERVER,
    EMAIL_SMTP_PORT,
)


def send_alert(
    subject: str,
    body: str,
    attachment_paths: Optional[list] = None,
    *,
    enabled: bool = True,
    sender: str = EMAIL_SENDER,
    password: str = EMAIL_PASSWORD,
    receiver: str = EMAIL_RECEIVER,
    smtp_server: str = EMAIL_SMTP_SERVER,
    smtp_port: int = EMAIL_SMTP_PORT,
) -> tuple[bool, str]:
    """
    Send an email alert.

    Parameters
    ----------
    subject, body:       Standard email fields.
    attachment_paths:    Optional list of local file paths to attach.
    enabled:             Master switch; returns ``(False, "disabled")`` when off.
    sender/password/…:   Override the defaults from ``config.settings`` when needed
                         (e.g. per-session UI inputs).

    Returns
    -------
    ``(True, "Sent")`` on success, ``(False, error_message)`` on failure.
    """
    if not enabled:
        return False, "Email alerts disabled"
    if not sender or not password or not receiver:
        return False, "Missing sender / app-password / receiver"

    try:
        msg = MIMEMultipart()
        msg["From"]    = sender
        msg["To"]      = receiver
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        for path in attachment_paths or []:
            if not path or not os.path.exists(path):
                continue
            with open(path, "rb") as fh:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(fh.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(path)}"',
            )
            msg.attach(part)

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        return True, "Sent"

    except Exception as exc:
        return False, str(exc)
