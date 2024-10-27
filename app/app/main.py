from app import app
from app.routers import population


app.include_router(population.router, prefix="/population", tags=["population"])
