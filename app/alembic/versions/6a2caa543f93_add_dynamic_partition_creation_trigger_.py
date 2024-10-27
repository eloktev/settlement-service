"""Add dynamic partition creation trigger for living_building_population

Revision ID: 6a2caa543f93
Revises: 159aba84da2d
Create Date: 2024-10-26 14:32:23.604648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a2caa543f93'
down_revision: Union[str, None] = '159aba84da2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create trigger function
    op.execute("""
    CREATE OR REPLACE FUNCTION create_living_building_population_partition()
    RETURNS TRIGGER AS $$
    DECLARE
        partition_name TEXT;
        start_year INT;
        end_year INT;
    BEGIN
        -- Define partition name and year range
        partition_name := 'living_building_population_' || NEW.year || '_' || NEW.forecast_type;
        start_year := NEW.year;
        end_year := NEW.year + 1;

        -- Check if partition exists; if not, create it
        IF NOT EXISTS (
            SELECT 1
            FROM pg_tables
            WHERE schemaname = 'public' AND tablename = partition_name
        ) THEN
            EXECUTE format(
                'CREATE TABLE IF NOT EXISTS %I PARTITION OF living_building_population
                 FOR VALUES FROM (%L, %L) TO (%L, %L)',
                partition_name, start_year, NEW.forecast_type, end_year, NEW.forecast_type
            );
        END IF;

        RETURN NULL;  -- Proceed with the insert
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create trigger that calls the function before each insert
    op.execute("""
    CREATE TRIGGER before_insert_living_building_population
    BEFORE INSERT ON living_building_population
    FOR EACH ROW EXECUTE FUNCTION create_living_building_population_partition();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS before_insert_living_building_population ON living_building_population")
    op.execute("DROP FUNCTION IF EXISTS create_living_building_population_partition")
