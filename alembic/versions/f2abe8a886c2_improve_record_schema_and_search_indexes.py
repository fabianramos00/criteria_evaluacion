"""improve record schema and search indexes

Revision ID: f2abe8a886c2
Revises: dcf153d2d326
Create Date: 2026-08-21 11:43:33.920624

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f2abe8a886c2"
down_revision: Union[str, Sequence[str], None] = "dcf153d2d326"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "Record",
        "data",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        type_=postgresql.JSONB(),
        postgresql_using="data::jsonb",
    )
    op.alter_column(
        "Record",
        "rating",
        existing_type=sa.Float(),
        type_=sa.Numeric(precision=5, scale=2),
        postgresql_using="rating::numeric(5,2)",
    )
    op.create_index(
        "ix_record_repository_names_gin",
        "Record",
        ["repository_names"],
        unique=False,
        postgresql_using="gin",
    )
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_record_repository_names_trgm "
        'ON "Record" USING gin '
        "(array_to_string(repository_names, ' ') gin_trgm_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_record_repository_names_trgm")
    op.drop_index("ix_record_repository_names_gin", table_name="Record")
    op.alter_column(
        "Record",
        "rating",
        existing_type=sa.Numeric(precision=5, scale=2),
        type_=sa.Float(),
        postgresql_using="rating::double precision",
    )
    op.alter_column(
        "Record",
        "data",
        existing_type=postgresql.JSONB(),
        type_=postgresql.JSON(astext_type=sa.Text()),
        postgresql_using="data::json",
    )
