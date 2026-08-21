from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheck(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
