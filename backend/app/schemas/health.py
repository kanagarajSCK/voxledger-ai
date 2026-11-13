from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    timestamp: datetime = Field(..., description="Server timestamp (UTC)")
    app_name: str = Field(..., example="VoxLedger AI")
    version: str = Field(..., example="0.1.0")
    environment: str = Field(..., example="development")
    database_connected: bool = Field(..., description="Database connection health status")
    database_latency_ms: Optional[float] = Field(None, description="Database ping roundtrip latency in ms")
    api_version: str = Field(..., example="/api/v1")
    websocket_endpoint: str = Field(..., example="/api/v1/ws/voice")
