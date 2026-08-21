from fastapi import APIRouter
from app.api.v1.endpoints import daily, health, words

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(daily.router, tags=["Daily"])
api_router.include_router(words.router, prefix="/words", tags=["Words"])
