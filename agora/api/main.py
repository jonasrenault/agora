import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from rich.logging import RichHandler
from starlette.middleware.sessions import SessionMiddleware

from agora.api import templates
from agora.api.crud import init_db
from agora.api.deps import CurrentUser, OptionalUser
from agora.api.render import create_context
from agora.api.routes.routes import api_router
from agora.config import settings

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler(markup=True)]
)
LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    LOGGER.info("[green]✓[/green] Migrations complete.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.FASTAPI_ENV == "development" else None,
)

app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)


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

# Static files
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, optional_user: OptionalUser) -> Response:
    if optional_user is not None:
        return RedirectResponse(url=request.url_for("dashboard"))
    return templates.TemplateResponse(
        request=request, name="pages/index.html", context=create_context(optional_user)
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: CurrentUser) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="pages/dashboard.html", context=create_context(current_user)
    )


@app.get("/health-check/")
async def health_check() -> bool:
    return True


app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run(app="agora.api.main:app", host="127.0.0.1", port=8000, reload=True)
