"""
===============================================================================
Error monitoring with Sentry (app/core/monitoring.py)
===============================================================================
Turned on only when SENTRY_DSN is set (production). Locally it stays off,
so nothing is sent while developing. Errors are reported with the request
id; request bodies and variable values are never sent (they can hold
passwords, OTPs and tokens).
===============================================================================
"""
import sentry_sdk

from app.core.config import APP_ENV, SENTRY_DSN
from common.Logger import Logger 

logger = Logger.get_logger()


def init_sentry() -> None:
    if not SENTRY_DSN:
        logger.info("Sentry is off (SENTRY_DSN not set)")
        return
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=APP_ENV,
        send_default_pii=False,
        max_request_body_size="never",
        include_local_variables=False,
        traces_sample_rate=0,
    )
    logger.info(f"Sentry is on (environment={APP_ENV})")