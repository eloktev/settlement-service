from pydantic import BaseModel, Field
from geoalchemy2.types import WKBElement
from typing_extensions import Annotated


class LivingBuildingBase(BaseModel):
    city_db_house_id: int = Field(..., description="id дома в city_db")
    parent_territory_id: int = Field(..., description="id территории из urban_db")
    center: Annotated[str, WKBElement] = Field(..., description="Центр дома")

class LivingBuildingCreate(LivingBuildingBase):
    pass

class LivingBuilding(LivingBuildingBase):
    id: int

    class Config:
        from_attributes=True
