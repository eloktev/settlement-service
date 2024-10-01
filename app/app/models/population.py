from sqlalchemy import Table, Column, Integer, String, ForeignKey, Float, PrimaryKeyConstraint, Enum, UniqueConstraint
import enum
from sqlalchemy.orm import relationship
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from .base import metadata, Base

class Gender(enum.Enum):
    male = 1
    female = 2


class LivingBuildingPopulation(Base):
    __tablename__ = "living_building_population"
    living_building_id = Column(Integer, ForeignKey("living_building.id"), unique=False, index=True)
    living_building = relationship("LivingBuilding")
    year = Column(Integer, index=True, unique=False, nullable=False)
    forecast_type = Column(String, index=True, nullable=False,)
    count = Column(Integer)


    __table_args__ = (
        PrimaryKeyConstraint(living_building_id, year, forecast_type),
        UniqueConstraint('living_building_id', 'year', 'forecast_type' , name='_building_year_type_uc'),
        {'postgresql_partition_by': 'RANGE (year, forecast_type)',},
    )


class LivingBuildingPopulationDistribution(Base):
    __tablename__ = "living_building_population_distribution"
    living_building_id = Column(Integer, ForeignKey("living_building.id"), unique=False, index=True)
    living_building = relationship("LivingBuilding")

    year = Column(Integer, index=True, unique=False, nullable=False)
    forecast_type = Column(String, index=True, nullable=False,)
    gender = Column(Enum(Gender), nullable=False, index=True, unique=False)
    age = Column(String, nullable=False, index=True, unique=False)
    count = Column(Integer)


    __table_args__ = (
        PrimaryKeyConstraint(living_building_id, age, gender, year, forecast_type),
        UniqueConstraint('living_building_id', 'year', 'forecast_type', 'gender', 'age' , name='_building_year_type_gender_age_uc'),
        {'postgresql_partition_by': 'RANGE (year, forecast_type)',},
    )