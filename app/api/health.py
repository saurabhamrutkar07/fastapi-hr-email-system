"""
===============================================================================
Health check (app/api/health.py)
===============================================================================
GET /health -- no login needed. 200 when the app and the database answer,
503 when the database doesn't (within 3 seconds). Used by the EC2 setup and
uptime checks to tell "server is up" from "server is up but broken".
===============================================================================
"""
import asyncio

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database.database import engine
from common.Logger import Logger

logger = Logger.get_logger()

router = APIRouter()


async def ping_database() -> None:
    async with engine.connect() as conn: 
        await conn.execute(text("SELECT 1"))


@router.get("/health")
async def health():
    try:
        await asyncio.wait_for(ping_database(), timeout=3)
    except Exception as exc:
        # Details go to the log only, never to the caller 
        logger.error(f"Health check: database not reachable: {exc!r}")
        return JSONResponse(status_code=503, content={"status": "error", "database":"unreachable"})
    return {"status": "ok", "database":"ok"}