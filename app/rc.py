import requests
from app.core.config import settings
from population_restorator.balancer import balance_houses, balance_territories
from population_restorator.models.territories import Territory
from app.dao.living_building import LivingBuildingDAO
from app.dao.population import LivingBuildingPopulationDAO
from app.schemas.living_building import LivingBuildingCreate
from app.schemas.population import LivingBuildingPopulationCreate
import pandas as pd
from numpy import nan
import asyncio
from loguru import logger
import json  
import sys

# Constants
FORECAST_TYPE = "CURRENT"
logger.remove()
logger.add(sys.stderr, level="INFO")

def get_total_population(territory_id: int, year: int) -> int | None:
    url = f"{settings.indicators_url}/indicators/2/{territory_id}"
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Error retrieving total population: {response.content}")
        return None
    content = response.json()
    return next((item['value'] for item in content if item['year'] == year), None)


def get_territory_by_id(territory_id):
    url = f"{settings.urban_url}/territory/{territory_id}"
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Error retrieving territory: {response.content}")
    return response.json()


def get_territories_by_parent(territory_id: int, parent_name=None):
    url = f"{settings.urban_url}/territories?parent_id={territory_id}&get_all_levels=false&page_size=10000"
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Error retrieving territories: {response.content}")
    territories = response.json().get('results', [])
    if parent_name:
        for territory in territories:
            territory['outer_territory'] = parent_name
    return territories


def get_houses(territory_name: str, subterritory_name: str):
    url = f"{settings.city_url}/api/city/{territory_name}/administrative_unit/{subterritory_name}/houses"
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Error retrieving houses: {response.content}")
    return response.json()

def model_living_area(row):
    row['living_area'] = int(row['building_area'] * 0.7)
    return row

async def save_living_building_data(df: pd.DataFrame, parent_territory_id: int):
    batch_data = []
    for _, row in df.iterrows():
        center_data = json.dumps(row['geometry']) if isinstance(row['geometry'], dict) else row['geometry']
        batch_data.append(LivingBuildingCreate(
            city_db_house_id = row['building_id'],
            parent_territory_id = parent_territory_id,
            center = center_data
        ))
    
    # Insert buildings and get mapping of existing records
    await LivingBuildingDAO.batch_insert(batch_data)
    return await LivingBuildingDAO.get_existing_ids([b.city_db_house_id for b in batch_data])



async def save_population_data(df: pd.DataFrame, building_id_map: dict, year: int):
    batch_data = []
    missing_ids = []
    for _, row in df.iterrows():
        building_id = building_id_map.get(row['building_id'])
        if building_id:
            batch_data.append(
                LivingBuildingPopulationCreate(
                    living_building_id=building_id,
                    year=year,
                    forecast_type=FORECAST_TYPE,
                    count=row['population']
                ))
        else:
            missing_ids.append(row['building_id'])

    logger.info(f"Total missing building IDs: {len(missing_ids)}")
    if missing_ids:
        logger.info(f"Sample missing building IDs: {missing_ids[:10]}")  # Show a sample of missing IDs
    logger.info(f"Total records prepared for insertion: {len(batch_data)}")

    # Batch insert population data using PopulationDAO
    await LivingBuildingPopulationDAO.batch_insert(batch_data)

async def get_restorator_data(territory_id: int, year: int, do_house_sync:bool = False):
    total_population = get_total_population(territory_id, year)
    urban_territory = get_territory_by_id(territory_id)
    subterritories = get_territories_by_parent(territory_id)
    inner_territories = []

    for subterritory in subterritories:
        houses_data = get_houses(urban_territory['name'], subterritory['name'])["features"]
        houses_df = pd.DataFrame(
            {**entry["properties"], "geometry": entry["geometry"]} for entry in houses_data
        )
        houses_df = houses_df.apply(model_living_area, axis=1).dropna(how="all").replace({nan: None})
        building_id_map = await save_living_building_data(houses_df, subterritory['territory_id'])


        inner_territories.append(Territory(
            name=subterritory['name'],
            population=get_total_population(subterritory['territory_id'], year),
            inner_territories=None,
            houses=houses_df
        ))

    # Process the main territory after subterritories
    territory = Territory(
        name=urban_territory['name'],
        population=total_population or sum(t.population for t in inner_territories if t.population),
        inner_territories=inner_territories,
        houses=None
    )

    logger.debug('Start balancing territories')
    balance_territories(territory)
    logger.debug('Start balancing houses')
    balance_houses(territory)
    houses_df = territory.get_all_houses()
    logger.info(f"Total houses in enriched_houses_df: {len(houses_df)}")
    enriched_houses_df = pd.DataFrame({
        "building_id": houses_df["building_id"],  # Access columns directly
        "population": houses_df.get("population", 0)  # Use `get` for optional columns
    })
    logger.info(f"Total enriched houses prepared for population: {len(enriched_houses_df)}")
    # Save population data with the correct building_id
    
    await save_population_data(enriched_houses_df, building_id_map, year)
# Main entry
if __name__ == "__main__":
    asyncio.run(get_restorator_data(3138, 2023, False))