from sqlalchemy.future import select
from app.dao.base import BaseDAO
from app.models.living_building import LivingBuilding
from app.db.session import get_db


class LivingBuildingDAO(BaseDAO):
    model = LivingBuilding
    
    @classmethod
    async def get_existing_ids(cls, city_db_house_ids):
        """Retrieve existing IDs to prevent duplicates in bulk insert."""
        async for session in get_db():
            results = await session.execute(
                select(cls.model.city_db_house_id, cls.model.id)
            )
            return {result[0]: result[1] for result in results}
    