"""Add function ensure partition before inserting to partitioned tables

Revision ID: b9ebe4329c8e
Revises: 6a2caa543f93
Create Date: 2024-10-26 14:47:33.823267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9ebe4329c8e'
down_revision: Union[str, None] = '6a2caa543f93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
               CREATE OR REPLACE FUNCTION ensure_partition(year_value INT, forecast_type_value TEXT)
                RETURNS VOID AS $$
                DECLARE
                    partition_name TEXT;
                    start_year INT;
                    end_year INT;
                BEGIN
                    partition_name := 'living_building_population_' || year_value || '_' || forecast_type_value;
                    start_year := year_value;
                    end_year := year_value + 1;

                    -- Check if the partition exists
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_tables
                        WHERE schemaname = 'public' AND tablename = partition_name
                    ) THEN
                        EXECUTE format(
                            'CREATE TABLE IF NOT EXISTS %I PARTITION OF living_building_population
                            FOR VALUES FROM (%L, %L) TO (%L, %L)',
                            partition_name, start_year, forecast_type_value, end_year, forecast_type_value
                        );
                    END IF;
                END;
                $$ LANGUAGE plpgsql;
               """)


def downgrade() -> None:
    # Optionally, drop the dynamic partitioning function if no longer needed
    op.execute("DROP FUNCTION IF EXISTS ensure_partition")
