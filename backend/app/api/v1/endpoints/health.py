from fastapi import APIRouter
from app.schemas.word import HealthCheck

router = APIRouter()


@router.get("/health", response_model=HealthCheck, summary="Health Check")
async def health_check() -> HealthCheck:
    """
    Check the health status of the API service.
    """
    return HealthCheck(status="ok", version="0.1.0")
