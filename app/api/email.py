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

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
# Request/Response Pydantic schemas.
# These classes validate incoming request data and structure outgoing responses.
from app.schemas.email import JobApplicationEmailRequest, SingleHREmailRequest, EmailTransactionResponse
from app.services.cold_email_service import send_cold_emails, send_email_to_individual
from app.database.repositories import get_transaction_by_request_id, list_email_transactions
from app.core.security import verify_key_secret
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
    dependencies=[Depends(verify_key_secret)]
)

# ---------------------------------------------------------------------------
# Send Cold Emails
# ---------------------------------------------------------------------------


@router.post("/send-cold")
async def send_cold_email(payload: JobApplicationEmailRequest):
     """
        Send cold application emails to multiple HR contacts.

        Flow:
            Client
            ↓
            FastAPI Endpoint
            ↓
            Request validation using JobApplicationEmailRequest
            ↓
            send_cold_emails() service
            ↓
            Email sending + transaction creation
            ↓
            Response returned to client
     """
     # Log successful completion of the operation.
     logger.info("Received request to send cold emails.")

     # Return the service result to the client.
     try:
          result = await send_cold_emails(payload) 
          logger.info("Cold email sending operation completed successfully.")
          # Return the service result to the client.
          return result
     except Exception as exc:
        # Log the exception along with its traceback.
        #
        # `logger.exception()` should be used inside an except block because
        # it automatically includes the exception traceback.
        logger.exception(
            f"Failed to send cold emails: {exc}"
        )

        # Re-raise the exception so FastAPI can handle it appropriately.
        raise
        

# ---------------------------------------------------------------------------
# Send Email To Individual HR
# ---------------------------------------------------------------------------

@router.post("/send-to-hr")
async def send_email_to_hr(payload: SingleHREmailRequest):
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
        result = await send_email_to_individual(payload)

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
async def get_email_transaction(request_id: str):
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
    if not transaction:

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
async def get_email_transactions_list(limit: int = 50, offset: int = 0):
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

    # Delegate database operation to the repository layer.
    transactions = await list_email_transactions(
        limit=limit,
        offset=offset,
    )

    logger.info(
        f"Successfully retrieved {len(transactions)} email transactions."
    )

    return transactions



