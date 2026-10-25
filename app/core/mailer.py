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

def _login(server:smtplib.SMTP, email_address: str, email_password: str) -> None:
    """
    server.login() that reports a rejected password as such. Gmail answers 
    a wrong password with "535... not accepted" and then hangs up, so
    smtplib's  retry with its next login method fails with 
    SMTPServerDisconnected insted of SMTPAuthenticationError.  
    """
    try:
        server.login(email_address,email_password)
    except smtplib.SMTPServerDisconnected as exc:
        raise smtplib.SMTPAuthenticationError(
            535, b"Username and password not accepted"
        ) from exc 

def check_smtp_login(
        smtp_server : str,
        smtp_port : int,
        email_address : str, 
        email_password : str 
) -> None:
    """
    Connects  and logs in without sending anything, to find out early 
    whether the mail server accepts these details. Raises the smtplib
    error (e.g. SMTPAuthenticationError for a wrong App password).
    """
    with smtplib.SMTP(smtp_server, smtp_port,timeout=15) as server:
        server.starttls()
        _login(server,email_address, email_password)

def send_email(
    to_email: str,
    subject: str,
    body: str,
    attachments: list[str] | None = None,
    byte_attachments: list[dict] | None = None,
    smtp_server: str | None = None,
    smtp_port : int | None = None,
    email_address : str | None = None,
    email_password : str | None = None,
    message_id : str | None = None
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
    # Our own id for this email, so a reply (In-Reply-To: <this id>) can be matched to it
    if message_id:
        msg["Message-ID"] = message_id
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
        _login(server,email_address, email_password)  # Authenticate with credentials
        server.send_message(msg)  # Transmit message payload

