"""
===============================================================================
SMTP Mailer Core Utility (mailer.py)
===============================================================================
This module encapsulates low-level SMTP network communication using Python's 
built-in `smtplib` and `email.message.EmailMessage` modules.
It constructs multipart MIME emails, attaches files (e.g. PDF resumes), and 
dispatches messages over a TLS-encrypted SMTP connection.
===============================================================================
"""

import smtplib
from email.message import EmailMessage
import mimetypes
import os
from app.core.config import SMTP_SERVER, SMTP_PORT, EMAIL_ADDRESS, EMAIL_PASSWORD


def send_email(
    to_email: str,
    subject: str,
    body: str,
    attachments: list[str] | None = None,
    byte_attachments: list[dict] | None = None,
    smtp_server: str | None = None,
    smtp_port : int | None = None,
    email_address : str | None = None,
    email_password : str | None = None
):
    """
    Constructs and dispatches an email message over SMTP with TLS encryption.

    `attachmetnts` -- file paths on local disk (old style).
    `byte_attachments` --[{"filename": str,"content": bytes}] for data
    alredy in memory (e.g. a resume fetched from s3) -- no disk access.

    If smtp_server/smtp_port/email_address/email_password are not given, 
    falls back to the platform's global confug values -- used by system
    emails (e.g. OTPs) that must always come from the platform account, 
    not a specific user's own SMTP credentials.
    """
    smtp_server = smtp_server or SMTP_SERVER
    smtp_port = smtp_port or SMTP_PORT 
    email_address = email_address or EMAIL_ADDRESS
    email_password = email_password or EMAIL_PASSWORD

    # 1. Initialize modern EmailMessage container
    msg = EmailMessage()
    msg["From"] = email_address
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    # 2. Process file attachments if provided
    if attachments:
        for path in attachments:
            # Check file existence before reading
            if not os.path.exists(path):
                raise FileNotFoundError(f"Attachment not found at path: {path}")

            # Guess MIME content type (e.g., 'application/pdf')
            mime_type, _ = mimetypes.guess_type(path)
            maintype, subtype = (
                mime_type.split("/") if mime_type else ("application", "octet-stream")
            )

            # Read binary file content and add attachment payload
            with open(path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=os.path.basename(path)
                )

    if byte_attachments:
        for att in byte_attachments:
            mime_type,_ = mimetypes.guess_type(att["filename"])
            maintype,subtype = (
                mime_type.split("/") if mime_type else ("application", "octet-stream")
            )

            msg.add_attachment(
                att["content"],
                maintype=maintype,
                subtype=subtype,
                filename=att["filename"]
            )

    # 3. Establish SMTP connection, upgrade to TLS, authenticate, and send message
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Secure connection using Transport Layer Security (TLS)
        server.login(email_address, email_password)  # Authenticate with credentials
        server.send_message(msg)  # Transmit message payload

