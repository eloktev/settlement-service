from app.dao.base import BaseDAO
from app.models.population import LivingBuildingPopulation
from sqlalchemy import text
from pydantic import BaseModel
from app.db.session import get_db
from app.schemas.population import LivingBuildingPopulationCreate
from sqlalchemy.dialects.postgresql import insert  
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.living_building import LivingBuilding
from app.models.population import LivingBuildingPopulation
from itertools import product
import logging
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from itertools import product
from app.db.session import get_db
from pydantic import BaseModel

class LivingBuildingPopulationDAO(BaseDAO):
    model = LivingBuildingPopulation
    create_schema = LivingBuildingPopulationCreate

    @classmethod
    async def ensure_partition(cls, session, year: int, forecast_type: str):
        """Create a partition if it does not exist for the given year and forecast_type."""
        partition_name = f"living_building_population_{year}_{forecast_type}"
        start_year = year
        end_year = year + 1

        # Construct SQL for partition creation
        create_partition_sql = f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_tables
                    WHERE schemaname = 'public' AND tablename = '{partition_name}'
                ) THEN
                    EXECUTE format(
                        'CREATE TABLE IF NOT EXISTS %I PARTITION OF living_building_population
                         FOR VALUES FROM (%s, %L) TO (%s, %L)',
                        '{partition_name}', {start_year}, '{forecast_type}', {end_year}, '{forecast_type}'
                    );
                END IF;
            END $$;
        """
        try:
            await session.execute(text(create_partition_sql))
            await session.commit()  # Ensure partition exists before inserting
            logging.debug(f"Partition {partition_name} ensured for {year}, {forecast_type}")
        except Exception as e:
            await session.rollback()
            logging.error(f"Error creating partition {partition_name}: {e}")
            raise e

    @classmethod
    async def batch_insert(cls, instances: list[BaseModel], batch_size: int = None):
        if batch_size is None:
            batch_size = cls.BATCH_SIZE

        data = [instance.model_dump() for instance in instances]
        total_inserted = 0

        async for session in get_db():
            try:
                # Ensure partitions
                unique_years = {instance.year for instance in instances}
                unique_forecasts = {instance.forecast_type for instance in instances}
                for year, forecast_type in product(unique_years, unique_forecasts):
                    await cls.ensure_partition(session, year, forecast_type)

                # Perform batch insertion
                for i in range(0, len(data), batch_size):
                    batch_data = data[i:i + batch_size]
                    stmt = insert(cls.model).values(batch_data)
                    stmt = stmt.on_conflict_do_nothing()
                    result = await session.execute(stmt)
                    total_inserted += result.rowcount or len(batch_data)
                    logging.debug(f"Inserted batch of {len(batch_data)} records.")

                await session.commit()
                logging.info(f"Total records inserted: {total_inserted}")
            except Exception as e:
                await session.rollback()
                logging.error(f"Error during batch insert: {e}")
                raise e

    @classmethod
    async def get_population_by_parent_territory_id(cls, session, parent_territory_id: int, limit: int = 100, offset: int = 0):
        """Fetch paginated population records by LivingBuilding.parent_territory_id."""
        query = (
            select(cls.model)
            .join(LivingBuilding, LivingBuilding.id == cls.model.living_building_id)
            .where(LivingBuilding.parent_territory_id == parent_territory_id)
            .options(joinedload(cls.model.living_building))
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        return result.scalars().all() 
    
    @classmethod
    async def get_population_by_city_db_house_id(cls, session, city_db_house_id: int):
        """Fetch population record by living building id from city_db"""
        query = (
            select(cls.model)
            .join(LivingBuilding, LivingBuilding.id == cls.model.living_building_id)
            .where(LivingBuilding.city_db_house_id == city_db_house_id)
            .options(joinedload(cls.model.living_building))
        )
        result = await session.execute(query)
        return result.scalars().first()  
    
