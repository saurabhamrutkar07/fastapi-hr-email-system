"""
===============================================================================
Alembic Environment (migrations/env.py)
===============================================================================
Runs database migrations with the app's own settings:
1. The database URL comes from DATABASE_URL in .env, like the app.
2. `Base.metadata` (every model in app/models/models.py) is what
   `alembic revision --autogenerate` compares the database against.
3. Tables that aren't models (old tables from early versions) are left
   alone, so a migration never drops them by accident.

Commands (run from the project folder):
    alembic upgrade head                            # bring the database up to date
    alembic revision --autogenerate -m "message"    # write a migration for model changes
===============================================================================
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.database.database import Base
import app.models.models  # noqa: F401 -- registers every model on Base.metadata

load_dotenv()

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    """Skip tables that exist in the database but not in our models."""
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations() -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


asyncio.run(run_migrations())
