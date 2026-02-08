
from fastapi import APIRouter
from app.api.endpoints import books, tasks, voice, config, version

api_router = APIRouter()
api_router.include_router(books.router, tags=["books"])
api_router.include_router(tasks.router, tags=["tasks"])
api_router.include_router(voice.router, tags=["voice"])
api_router.include_router(config.router, tags=["config"])
api_router.include_router(version.router, tags=["version"])

