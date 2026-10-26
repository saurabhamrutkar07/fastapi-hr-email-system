"""match the old hr_contacts table to its model

Databases made before migrations got hr_contacts from an older model:
title and company were required and email had no unique index. New
databases already match, so every statement here is safe to run twice.

Revision ID: 017042c87821
Revises: 806e6884b2f7
Create Date: 2026-10-27 00:21:59.404478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '017042c87821'
down_revision: Union[str, Sequence[str], None] = '806e6884b2f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE hr_contacts ALTER COLUMN title DROP NOT NULL")
    op.execute("ALTER TABLE hr_contacts ALTER COLUMN company DROP NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_hr_contacts_email ON hr_contacts (email)")


def downgrade() -> None:
    """Downgrade schema. Nothing to undo: the old shape was a mistake."""
    pass
