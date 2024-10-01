from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.project_name,
    #   openapi_url=f"{settings.api_v1_str}/openapi.json",
    version=settings.api_version,
    contact={"name": "Egor Loktev", "url": "https://t.me/eloktev"},
)
