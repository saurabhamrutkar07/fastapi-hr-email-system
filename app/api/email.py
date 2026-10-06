"""
Email API Controller (app/api/email.py)

This module contains all HTTP endpoints related to email operations.

Available endpoints:
    1. POST /email/send-cold
       Sends cold application emails to multiple HR contacts.

    2. POST /email/send-to-hr
       Sends a cold application email to one specific HR contact.

    3. GET /email/transactions/{request_id}
       Retrieves the transaction details for a specific request ID.

    4. GET /email/transactions
       Retrieves a paginated list of email transactions.

Security:
    All endpoints in this router require authentication through
    the `key-secret` header.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List
# Request/Response Pydantic schemas.
# These classes validate incoming request data and structure outgoing responses.
from app.core.encryption import decrypt_value
from app.schemas.email import JobApplicationEmailRequest, SingleHREmailRequest, EmailTransactionResponse
from app.services.cold_email_service import send_email_to_individual, get_user_smtp_config,get_recruiters_for_sending,send_cold_emails_background,get_user_default_template, get_user_active_resume
from app.database.repositories import get_transaction_by_request_id, list_email_transactions
from app.core.security import get_current_user
from app.models.models import User
from common.Logger import Logger

# ---------------------------------------------------------------------------
# Logger Initialization
# ---------------------------------------------------------------------------

# Get the application logger.
#
# `Logger.get_logger()` returns the configured logger instance.
# We create it once at module level and reuse it throughout this controller.

logger = Logger.get_logger() 

# ---------------------------------------------------------------------------
# Router Configuration
# ---------------------------------------------------------------------------

# Create an APIRouter instance.
#
# `dependencies` defined here apply to EVERY endpoint in this router.
#
# Therefore, every request to:
#
#     /email/send-cold
#     /email/send-to-hr
#     /email/transactions/{request_id}
#     /email/transactions
#
# must pass the `verify_key_secret` security check first.


router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

# ---------------------------------------------------------------------------
# Send Cold Emails
# ---------------------------------------------------------------------------


@router.post("/send-cold",status_code=status.HTTP_202_ACCEPTED)
async def send_cold_email(payload: JobApplicationEmailRequest,background_tasks: BackgroundTasks, current_user:User = Depends(get_current_user)):
     """
        Ques cold application emails to be sent in the background.
        validated SMTP/te,plate/resume synchronously (fails fast with a
        clears error if not configured); the actual sending happens after
        this response is returned.
     """
     # Log successful completion of the operation.
     logger.info("Received request to send cold emails (background).")

     smtp_credential = await get_user_smtp_config(current_user.id)
     smpt_password = decrypt_value(smtp_credential.encrypted_password)
     email_template = await get_user_default_template(current_user.id)
     resume_bytes = await get_user_active_resume(current_user.id)

     recruiters = await get_recruiters_for_sending()
     request_ids = [str(uuid.uuid4()) for _ in recruiters]


     background_tasks.add_task(
         send_cold_emails_background,
         payload=payload,
         user_id=current_user.id,
         recruiters=recruiters,
         request_ids=request_ids,
         smtp_credential=smtp_credential,
         smtp_password=smpt_password,
         email_template=email_template,
         resume_bytes=resume_bytes,
     )
     
     logger.info("Cold email batch queued for background sending")
     return {
         "status": "accepted",
         "total": len(recruiters),
         "request_ids": request_ids,
         "message": "Emails are being sent in the background. Check /email/transactions for results.", 
     }

     
     
        

# ---------------------------------------------------------------------------
# Send Email To Individual HR
# ---------------------------------------------------------------------------

@router.post("/send-to-hr")
async def send_email_to_hr(payload: SingleHREmailRequest,curren_user : User = Depends(get_current_user)):
     """
        Send a personalized cold email to one specific HR contact.

        Flow:
            Client
            ↓
            FastAPI Endpoint
            ↓
            Request validation
            ↓
            send_email_to_individual()
            ↓
            Email sending
            ↓
            Transaction creation
            ↓
            Response
        """
     logger.info("Received request to send email to individual HR.")
     try:

        # Delegate the actual email-sending operation to the service layer.
        result = await send_email_to_individual(payload,user_id=curren_user.id)

        logger.info(
            "Email to individual HR completed successfully."
        )

        return result

     except Exception as exc:
         # Log the complete exception traceback for debugging.
        logger.exception(
            f"Failed to send email to individual HR: {exc}"
        )

        # Allow FastAPI/global exception handling to process the exception.
        raise

     

# ---------------------------------------------------------------------------
# Get Email Transaction By Request ID
# ---------------------------------------------------------------------------


@router.get("/transactions/{request_id}", response_model=EmailTransactionResponse)
async def get_email_transaction(request_id: str, curret_user: User = Depends(get_current_user)):
    """
    Retrieve transaction details for a specific request ID.

    The request ID uniquely identifies an email transaction.

    Flow:
        Client
          ↓
        GET /email/transactions/{request_id}
          ↓
        Repository
          ↓
        PostgreSQL
          ↓
        Transaction returned
          ↓
        Response validation using EmailTransactionResponse
          ↓
        Client
    """
    logger.info(
        f"Fetching email transaction for request_id: {request_id}"
    )

    # Ask the repository layer to find the transaction.
    #
    # The controller does not directly execute SQL.
    transaction = await get_transaction_by_request_id(request_id)

    # If the repository cannot find a transaction with this request ID,
    # return HTTP 404 to the client.
    if not transaction or (curret_user.role != "admin" and transaction.user_id != curret_user.id):

        logger.warning(
            f"Transaction not found for request_id: {request_id}"
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Transaction with request_id "
                f"'{request_id}' not found."
            ),
        )

    logger.info(
        f"Transaction found successfully for request_id: {request_id}"
    )

    return transaction


# ---------------------------------------------------------------------------
# Get Email Transaction History
# ---------------------------------------------------------------------------


@router.get("/transactions", response_model=List[EmailTransactionResponse])
async def get_email_transactions_list(limit: int = 50, offset: int = 0,current_user: User = Depends(get_current_user)):
    """
    Retrieve recent email transactions with pagination.

    Parameters:
        limit:
            Maximum number of transactions to return.

        offset:
            Number of records to skip before returning results.

    Example:

        /email/transactions?limit=50&offset=0

    Flow:
        Client
          ↓
        FastAPI Endpoint
          ↓
        Repository
          ↓
        Database
          ↓
        List of transactions
          ↓
        Response
    """
    logger.info(
        f"Fetching email transactions. "
        f"limit={limit}, offset={offset}"
    )

    filter_user_id = None if current_user.role == "admin" else current_user.id

    # Delegate database operation to the repository layer.
    transactions = await list_email_transactions(
        limit=limit,
        offset=offset,
        user_id = filter_user_id,
    )

    logger.info(
        f"Successfully retrieved {len(transactions)} email transactions."
    )

    return transactions



