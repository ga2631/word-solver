from fastapi import APIRouter
from app.api.v1.endpoints import daily, health, random, word

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(daily.router, tags=["Daily"])
api_router.include_router(random.router, tags=["Random"])
api_router.include_router(word.router, tags=["Word"])
