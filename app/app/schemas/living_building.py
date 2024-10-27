from pydantic import BaseModel, Field, field_serializer
from geoalchemy2.types import WKBElement
from typing import Any
from typing_extensions import Annotated
from shapely.geometry import mapping
from geoalchemy2.shape import to_shape


class LivingBuildingBase(BaseModel):
    city_db_house_id: int = Field(..., description="id дома в city_db")
    parent_territory_id: int = Field(..., description="id территории муниципалитета из urban_db")
    center: Any | None = Field(None, description="GeoJSON format of the house center")  # Set as Optional[Any] for GeoJSON

    @field_serializer("center")
    def serialize_center(self, value):
        if isinstance(value, WKBElement):
            # Convert WKBElement to a GeoJSON-compatible dictionary
            shape = to_shape(value)
            return mapping(shape)  # Returns GeoJSON-compatible dict
        return value

class LivingBuildingCreate(LivingBuildingBase):
    pass

class LivingBuilding(LivingBuildingBase):
    id: int

    class Config:
        from_attributes=True
