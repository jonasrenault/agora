from fastapi import APIRouter

from agora.api.routes import agora, google, login

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(agora.router)
api_router.include_router(google.router)
