from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.population import LivingBuildingPopulation
from app.dao.population import LivingBuildingPopulationDAO


router = APIRouter()

@router.get("/by_house_id/{city_db_house_id}", response_model=LivingBuildingPopulation)
async def get_population_by_house_id(city_db_house_id: int, db: AsyncSession = Depends(get_db)):
    population = await LivingBuildingPopulationDAO.get_population_by_city_db_house_id(db, city_db_house_id)
    if not population:
        raise HTTPException(status_code=404, detail="Population record not found for the specified house ID")
    return population

@router.get("/by_parent_territory/{parent_territory_id}", response_model=list[LivingBuildingPopulation])
async def get_population_by_parent_territory(
    parent_territory_id: int,
    limit: int = Query(100, gt=0, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db)
):
    populations = await LivingBuildingPopulationDAO.get_population_by_parent_territory_id(db, parent_territory_id, limit=limit, offset=offset)
    if not populations:
        raise HTTPException(status_code=404, detail="No population records found for the specified parent territory ID")
    return populations