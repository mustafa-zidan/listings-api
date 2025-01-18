import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


# Set the event loop scope explicitly
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def async_client(anyio_backend):
    async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client