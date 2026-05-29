"""Enable the PostGIS extension.

Tables are generated from the ORM models via ``alembic revision
--autogenerate`` once a database is available (manual section 18.8).

Revision ID: 0001
Revises:
Create Date: 2026-05-29
"""
from __future__ import annotations

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS postgis")
