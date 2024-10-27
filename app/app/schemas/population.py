from pydantic import BaseModel, Field
from geoalchemy2.types import WKBElement
from typing_extensions import Annotated
from app.schemas.living_building import LivingBuilding


class LivingBuildingPopulationBase(BaseModel):
    living_building_id: int = Field(..., description="id дома в таблице living_building") 
    year: int
    forecast_type: str
    count: int

class LivingBuildingPopulationCreate(LivingBuildingPopulationBase):
    pass


class LivingBuildingPopulation(LivingBuildingPopulationBase):
    living_building: LivingBuilding = Field(..., description="сведения из таблицы living_building") 

    class Config:
        from_attributes=True
