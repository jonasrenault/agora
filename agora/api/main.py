from fastapi import FastAPI

from agora.api.routes.routes import api_router
from agora.config.settings import settings

app = FastAPI(title=settings.PROJECT_NAME)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/health-check/")
async def health_check() -> bool:
    return True


app.include_router(api_router, prefix=settings.API_V1_STR)
