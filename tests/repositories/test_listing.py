import datetime
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.listing import Listing
from app.schemas import ListingSchema
from app.repositories.listing import ListingRepository
from app.schemas.listing import Property, Entity


@pytest.mark.asyncio
async def test_get_listing_by_id(session: AsyncSession):
    repo = ListingRepository(session)
    # Add a test listing
    listing = Listing(
        listing_id="test123",
        scan_date=datetime.datetime.fromisoformat("2023-01-01T12:00:00"),
        is_active=True,
        image_hashes=["hash1"]
    )
    session.add(listing)
    await session.commit()

    # Retrieve the listing
    retrieved = await repo.get_listing_by_id("test123")
    assert retrieved.listing_id == "test123"
    assert retrieved.is_active


@pytest.mark.asyncio
async def test_create_listing_with_nested_objects(session: AsyncSession):
    repo = ListingRepository(session)
    listing_data = ListingSchema(
        listing_id=str(uuid.uuid4()),
        scan_date=datetime.datetime.fromisoformat("2023-01-01T12:00:00"),
        is_active=True,
        image_hashes=["hash1"],
        properties=[
            Property(name="prop1", type="str", value="value1"),
            Property(name="prop2", type="bool", value=True)
        ],
        entities=[
            Entity(name="entity1", data={"key": "value"})
        ]
    )
    created_listing = await repo.create_listing_with_nested_objects(listing_data)

    assert created_listing.listing_id == listing_data.listing_id


@pytest.mark.asyncio
async def test_delete_listing(session: AsyncSession):
    repo = ListingRepository(session)
    # Add a test listing
    listing = Listing(
        listing_id=str(uuid.uuid4()),
        scan_date=datetime.datetime.fromisoformat("2023-01-01T12:00:00"),
        is_active=True,
        image_hashes=["hash1"]
    )
    session.add(listing)
    await session.commit()

    # Delete the listing
    deleted = await repo.delete_listing(listing.listing_id)
    assert deleted

    # Ensure it's gone
    retrieved = await repo.get_listing_by_id(listing.listing_id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_get_filtered_listings(session: AsyncSession):
    repo = ListingRepository(session)


    listing_ids = [str(uuid.uuid4()) for _ in range(2)]
    session.add_all([
        Listing(
            listing_id=listing_ids[0],
            scan_date=datetime.datetime.fromisoformat("2025-01-01T12:00:00"),
            is_active=True, image_hashes=["hash1"]
        ),
        Listing(
            listing_id=listing_ids[1],
            scan_date=datetime.datetime.fromisoformat("2023-01-02T12:00:00"),
            is_active=False,
            image_hashes=["hash2"]
        )
    ])

    # Retrieve filtered listings
    filters = {"is_active": True}
    listings = await repo.get_filtered_listings(filters, page=1, page_size=10)
    assert len(listings) == 1
    assert listings[0].listing_id == listing_ids[0]
