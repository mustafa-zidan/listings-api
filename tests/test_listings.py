import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_listings(async_client: AsyncClient):
    response = await async_client.get("/api/v1/listings/?page=1")
    assert response.status_code == 200
    assert "listings" in response.json()
