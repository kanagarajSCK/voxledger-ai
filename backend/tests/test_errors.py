import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_404_structured_error(async_client: AsyncClient):
    response = await async_client.get("/api/v1/nonexistent-route")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "timestamp" in data
