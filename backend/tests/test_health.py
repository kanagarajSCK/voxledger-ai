import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_unversioned_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["app_name"] == "VoxLedger AI"
    assert data["version"] == "0.1.0"
    assert data["database_connected"] is True
    assert data["api_version"] == "/api/v1"
    assert "timestamp" in data
    assert data["database_latency_ms"] is not None


@pytest.mark.asyncio
async def test_versioned_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert data["websocket_endpoint"] == "/api/v1/ws/voice"


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "VoxLedger AI"
    assert data["health_check"] == "/api/health"
