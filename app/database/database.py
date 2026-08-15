"""
===============================================================================
Database Connection & Session Initialization (database.py)
===============================================================================
Configures SQLAlchemy's asynchronous engine and session maker for PostgreSQL/MySQL/SQLite.
Exposes:
- `engine`: Async database engine connection pool.
- `AsyncSessionLocal`: Factory for creating async database sessions.
- `Base`: Declarative Base class for all ORM models.
- `init_db()`: Helper to auto-create missing tables on server startup.
===============================================================================
"""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables
load_dotenv()

# Read Database Connection String (e.g. postgresql+asyncpg://user:pass@host/dbname)
DATABASE_URL = os.getenv("DATABASE_URL")

# Create Asynchronous SQLAlchemy Engine
# `echo=True` logs SQL statements for debugging
# `pool_pre_ping=True` tests connections before usage to prevent stale connection errors
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True
)

# Async Session Factory
# `expire_on_commit=False` prevents attributes from expiring after commit, allowing access after session close
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
# Base ORM Class for model declarations
Base = declarative_base()


def init_db():
    db = SessionLocal()

    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()