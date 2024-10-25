from sqlalchemy.future import select
from app.dao.base import BaseDAO
from app.models.living_building import LivingBuilding


class LivingBuildingDAO(BaseDAO):
    model = LivingBuilding
    
    