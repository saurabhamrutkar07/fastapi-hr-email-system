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
    attachments: list[str] | None = None
):
    """
    Constructs and dispatches an email message over SMTP with TLS encryption.

    Parameters:
    -----------
    to_email : str
        Recipient email address.
    subject : str
        Email subject line.
    body : str
        Plain text or rendered HTML email body.
    attachments : list[str] | None
        Optional list of absolute file paths to attach (e.g., PDF resumes).

    Raises:
    -------
    FileNotFoundError:
        If an attachment path specified in `attachments` does not exist on disk.
    smtplib.SMTPAuthenticationError:
        If SMTP login fails due to wrong password or expired credentials.
    smtplib.SMTPRecipientsRefused:
        If the recipient email address is invalid or rejected by the remote server.
    """
    # 1. Initialize modern EmailMessage container
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
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

    # 3. Establish SMTP connection, upgrade to TLS, authenticate, and send message
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()  # Secure connection using Transport Layer Security (TLS)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)  # Authenticate with credentials
        server.send_message(msg)  # Transmit message payload

