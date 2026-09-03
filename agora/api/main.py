import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

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

# we need this middleware to save temporary code & state in session
# for OAuth2 flow
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="agora_session",
    max_age=14400,  # Session expiry in seconds (e.g., 4 hours)
    same_site="lax",  # Session needs to persist between callbacks to google servers
    https_only=settings.FASTAPI_ENV != "development",  # Recommended for production
)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/health-check/")
async def health_check() -> bool:
    return True


app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
