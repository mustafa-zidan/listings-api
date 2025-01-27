from datetime import datetime

from httpx import AsyncClient
import pytest

from app.repositories.listing import ListingRepository
from app.schemas import ListingSchema
from app.schemas.listing import Entity
from app.schemas.listing import Property


@pytest.mark.asyncio
async def test_get_listing_by_id(async_client: AsyncClient, session):
    # Arrange
    listing_id = "test123"
    repo = ListingRepository(session)
    listing_data = ListingSchema(
        listing_id=listing_id,
        scan_date=datetime.fromisoformat("2023-01-01T12:00:00"),
        is_active=True,
        image_hashes=["hash1"],
        properties=[
            Property(name="prop1", type="str", value="value1"),
            Property(name="prop2", type="bool", value=True),
        ],
        entities=[
            Entity(name="entity1", data={"key": "value"}),
        ],
    )
    await repo.create_listing_with_nested_objects(listing_data)
    await session.commit()

    # Act
    response = await async_client.get("/api/v1/listings/test123")

    # Assert
    assert response.status_code == 200
    assert response.json()["listing_id"] == listing_id


# TODO Add more tests for the remaining endpoints








