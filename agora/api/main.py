import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from rich.logging import RichHandler
from starlette.middleware.sessions import SessionMiddleware

from agora.api.crud import init_db
from agora.api.routes.routes import api_router
from agora.config.settings import settings
from agora.utils import driver_install

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler(markup=True)]
)
LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Make sure chromium driver is installed
    driver_install("chromium")
    await init_db()
    LOGGER.info("[green]✓[/green] Migrations complete.")
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


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(settings.TEMPLATES_DIR / "index.html") as f:
        return HTMLResponse(content=f.read())


@app.get("/health-check/")
async def health_check() -> bool:
    return True


app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run(app="agora.api.main:app", host="127.0.0.1", port=8000, reload=True)
