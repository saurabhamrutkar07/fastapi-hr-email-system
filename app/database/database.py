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

def env_int(name:str, default:int)-> int:
    """ A whole number from .env, or the default when it isn't set.""" 
    return int(os.getenv(name,default))

# Create Asynchronous SQLAlchemy Engine with a connection pool.
#
# Each request borrows one connection for its database work and gives it 
# back when its session closes, so these numbers are about requests
# running at the same moment, not about how many users exist.
# Every worker process has its own pool: workers x (pool size + overflow)
# must stay well under Postgres's max_connections (100 by default). 
engine = create_async_engine(
    DATABASE_URL,
    # print every sql statement; handy locally, too noisy in production 
    echo=os.getenv("DB_ECHO","false").lower() == "true",
    # Connections kept open and ready
    pool_size=env_int("DB_POOL_SIZE",5),
    # Extra connections allowed during a burst, closed again afterwards 
    max_overflow=env_int("DB_MAX_OVERFLOW",5),
    # Seconds a request waits for a free connection before failing
    pool_timeout = env_int("DB_POOL_TIMEOUT",10),
    # Replace connections older than this, before servers drop idle ones
    pool_recycle=env_int("DB_POOL_RECYCLE",1800),
    # Check a connection still works before handing it out
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
