import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from agora.api.routes.routes import api_router
from agora.config.settings import settings
from agora.utils import driver_install

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Make sure chromium driver is installed
    driver_install("chromium")
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/health-check/")
async def health_check() -> bool:
    return True


app.include_router(api_router, prefix=settings.API_V1_STR)
