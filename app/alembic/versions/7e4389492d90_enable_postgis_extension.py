"""Enable PostGIS extension

Revision ID: 7e4389492d90
Revises: 
Create Date: 2024-10-26 14:25:10.691456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e4389492d90'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade() -> None:
    # Disable PostGIS extension if you want to remove it in downgrades
    op.execute("DROP EXTENSION IF EXISTS postgis")
