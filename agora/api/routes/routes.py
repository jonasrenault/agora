from fastapi import APIRouter

from agora.api.routes import google, login, runs, users

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(runs.router)
api_router.include_router(google.router)
