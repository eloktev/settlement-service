from sqlalchemy import Table, Column, Integer, String, ForeignKey, Float, PrimaryKeyConstraint, Enum
import enum
from sqlalchemy.orm import relationship
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from geoalchemy2 import Geometry
from .base import metadata, Base

class Gender(enum.Enum):
    male = "male"
    female = "female"


class LivingBuilding(Base):
    __tablename__ = "living_building"

    id = Column(Integer, primary_key=True)
    city_db_house_id = Column(Integer, unique=True, nullable=True)
    parent_territory_id = Column(Integer)
    center = Column(Geometry('POINT'))
    # year = Column(Integer, index=True, unique=False, nullable=False)
    # forecast_type = Column(String, index=True, nullable=False,)
    # gender = Column(Enum(Gender), nullable=False, index=True, unique=False, nullable=False)
    # age = Column(String, nullable=False, index=True, unique=False, nullable=False)
    # count = Column(Integer)
