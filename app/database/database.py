"""
===============================================================================
Database Connection & Session Initialization (database.py)
===============================================================================
Configures SQLAlchemy's asynchronous engine and session maker for PostgreSQL.
Exposes:
- `engine`: Async database engine connection pool.
- `AsyncSessionLocal`: Factory for creating per-request async database sessions.
- `Base`: Declarative Base class for all ORM models.
- `get_db()`: FastAPI dependency that yields one AsyncSession per request.

Tables are created and changed by Alembic migrations (migrations/ folder):
run `alembic upgrade head` after pulling new code, before starting the app.

Flow for a junior developer:

    Every incoming request that needs the DB
        -> FastAPI calls get_db()
        -> get_db() opens one AsyncSession, yields it to the route
        -> route/service code does `await db.execute(...)`, `await db.commit()`
        -> when the route finishes (success or error), get_db() resumes
           and closes the session.


===============================================================================
"""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import declarative_base

# Load environment variables
load_dotenv()

# Read Database Connection String.
#
# IMPORTANT: this MUST use an async driver (e.g. postgresql+asyncpg://...).
# `create_async_engine` cannot work with a sync driver like psycopg2 --
# every query made through `engine`/`AsyncSessionLocal` below assumes the
# asyncpg driver is doing the actual network I/O.
DATABASE_URL = os.getenv("DATABASE_URL")

# Create Asynchronous SQLAlchemy Engine
# `echo=True` logs SQL statements for debugging
# `pool_pre_ping=True` tests connections before usage to prevent stale connection errors
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True
)

# Async Session Factory.
#
# `expire_on_commit=False` keeps attributes on a committed object readable
# afterwards without triggering a fresh (lazy-load) query -- which matters
# here because lazy-loading relationships is NOT supported on AsyncSession
# the way it is on a normal sync Session (see get_db() note below and
# hr_contact_excel_service.py's find_existing_contact()).
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)

# Base ORM Class for model declarations
Base = declarative_base()





async def get_db():
    """
    FastAPI dependency: yields ONE AsyncSession per request.

    Usage in a route:
        db: AsyncSession = Depends(get_db)

    FastAPI runs the code before `yield` when the request comes in, hands
    `session` to the route, then resumes this generator (running the
    `except`/`finally` below) once the route returns or raises -- so the
    session is always rolled back on error and always closed, even if the
    route forgets to.

    Note for junior devs: because this yields an AsyncSession (not the
    classic sync Session), every ORM call made with it must be awaited
    (`await db.execute(...)`, `await db.commit()`, `async with
    db.begin_nested():`). Plain `db.query(...)` from the old sync API
    does not exist here.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
