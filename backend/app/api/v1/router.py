from fastapi import APIRouter
from app.api.v1.endpoints import health, words

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(words.router, prefix="/words", tags=["Words"])
