
import requests
from app.core.config import settings
from population_restorator.utils.data_structure import city_as_territory
from population_restorator.balancer import balance_houses, balance_territories
from population_restorator.utils.data_saver import to_file
from population_restorator.models.territories import Territory
import itertools
from loguru import logger
import pandas as pd 
from numpy import nan
from functools import lru_cache


@lru_cache()
def get_total_population(territory_id:int, year: int) -> int | None:
    url = f"{settings.indicators_url}/indicators/2/{territory_id}"
    logger.debug(f"Retrieving total population from: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Error retrieving total population from {url}: {response.content}")
    else:
        content = response.json()
        for i in content:
            if i['year'] == year:
                return i['value']
    return None

@lru_cache()
def get_territory_by_id(territory_id):
    url = f"{settings.urban_url}/territory/{territory_id}"
    logger.info(f"Retrieving territory from: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Error retrieving territory ({response.status_code}): {response.content}")
    return response.json()

@lru_cache()
def get_territories_by_parent(territory_id: int, parent_name = None):
    url = f"{settings.urban_url}/territories?parent_id={territory_id}&get_all_levels=false&ordering=asc&page=1&page_size=10000"
    logger.info(f"Retrieving territories from: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Error retrieving territories ({response.status_code}): {response.content}")
    territories = response.json()
    if 'results' in territories.keys():
        results = territories['results']
        if parent_name:
            for i in results:
                i['outer_territory'] = parent_name
        return results
    else:
        logger.error(f"Error parsing territories from {url}. No key 'results'. Available keys: {', '.join(territories.keys())}")
    

@lru_cache()
def get_houses(territory_name:str, subterritory_name: str):



    url = f"{settings.city_url}/api/city/{territory_name}/administrative_unit/{subterritory_name}/houses"
    logger.info(f"Retrieving houses from: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Error retrieving houses ({response.status_code}): {response.content}")
    # here is a geojson
    return response.json()



def model_living_area(row):
    row['living_area'] = int(row['building_area']*0.7)
    return row
        


def get_restorator_data(territory_id: int, year:int):

    # return get_total_population(territory_id, year)
    total_population = get_total_population(territory_id, year)
    urban_territory = get_territory_by_id(territory_id)
    
    
    inner_territories = []
    subterritories = get_territories_by_parent(territory_id)
    for subterritory in subterritories:
        houses_df = pd.DataFrame((entry["properties"] | {"geometry": entry["geometry"]}) for entry in get_houses(urban_territory['name'], subterritory['name'])["features"])
        houses_df = houses_df.apply(lambda row: model_living_area(row), axis=1)
        houses_df = houses_df.dropna(how="all").reset_index(drop=True).replace({nan: None})  
        print(houses_df.shape[0])
        inner_territories.append(
            Territory(
                name=subterritory['name'],
                population=get_total_population(subterritory['territory_id'], year),
                inner_territories=None,
                houses=houses_df
            )
        )
    
    
    
    territory = Territory(
        name=urban_territory['name'],
        population = total_population,
        inner_territories=inner_territories,
        houses=None
        )
    if not territory.population:
        territory.population = sum([t.population for t in territory.inner_territories])
    
    logger.debug('Start balancing territories')
    balance_territories(territory)
    logger.debug('Start balancing houses')
    balance_houses(territory)

    outer_territories_new_df = pd.DataFrame(
            (
                {
                    "name": ot.name,
                    "population": ot.population,
                    "inner_territories_population": ot.get_total_territories_population(),
                    "houses_number": ot.get_all_houses().shape[0],
                    "houses_population": ot.get_total_houses_population(),
                    "total_living_area": ot.get_total_living_area(),
                }
                for ot in territory.inner_territories
            )
        )
    to_file(outer_territories_new_df, 'outer_territories_output.csv')
    to_file(territory.get_all_houses(), 'houses.csv')

    # logger.info("Balancing city houses")
    # balance_houses(city)
    # to_file(city.get_all_houses(), "123.csv")


get_restorator_data(3138, 2023)
# subterritories = get_territories_by_parent(2)
# ot_df = pd.DataFrame.from_records(subterritories) 
# print(ot_df.head())