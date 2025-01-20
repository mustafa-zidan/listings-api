from datetime import datetime

import pytest
from httpx import AsyncClient

from app.models import Listing
from app.repositories.listing import ListingRepository
from app.schemas import ListingSchema
from app.schemas.listing import Property, Entity


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
    listing = await repo.create_listing_with_nested_objects(listing_data)

    # Act
    response = await async_client.get("/api/v1/listings/test123")

    # Assert
    assert response.status_code == 200
    assert response.json()["listing_id"] == listing_id


# TODO Add more tests for the remaining endpoints








