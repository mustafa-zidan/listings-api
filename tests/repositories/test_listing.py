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
    """Test retrieving a listing by its ID."""
    # Arrange
    repo = ListingRepository(session)
    listing = Listing(
        listing_id="test123",
        scan_date=datetime.datetime.fromisoformat("2023-01-01T12:00:00"),
        is_active=True,
        image_hashes=["hash1"],
    )
    session.add(listing)
    await session.commit()

    # Act
    retrieved = await repo.get_listing_by_id("test123")

    # Assert
    assert retrieved.listing_id == "test123"
    assert retrieved.is_active


@pytest.mark.asyncio
async def test_create_listing_with_nested_objects(session: AsyncSession):
    """Test creating a listing with nested properties and entities."""
    # Arrange
    repo = ListingRepository(session)
    listing_data = ListingSchema(
        listing_id=str(uuid.uuid4()),
        scan_date=datetime.datetime.fromisoformat("2023-01-01T12:00:00"),
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

    # Act
    created_listing = await repo.create_listing_with_nested_objects(listing_data)

    # Assert
    assert created_listing.listing_id == listing_data.listing_id
    assert len(created_listing.image_hashes) == len(listing_data.image_hashes)
    assert created_listing.is_active


@pytest.mark.asyncio
async def test_create_listing_with_empty_properties(session: AsyncSession):
    """Test creating a listing with no properties."""
    # Arrange
    repo = ListingRepository(session)
    listing_data = ListingSchema(
        listing_id=str(uuid.uuid4()),
        scan_date=datetime.datetime.fromisoformat("2023-01-01T12:00:00"),
        is_active=False,
        image_hashes=["hash2"],
        properties=[],
        entities=[],
    )

    # Act
    created_listing = await repo.create_listing_with_nested_objects(listing_data)

    # Assert
    assert created_listing.listing_id == listing_data.listing_id
    assert not created_listing.is_active
    assert created_listing.image_hashes == ["hash2"]


@pytest.mark.asyncio
async def test_delete_listing(session: AsyncSession):
    """Test deleting a listing."""
    # Arrange
    repo = ListingRepository(session)
    listing = Listing(
        listing_id=str(uuid.uuid4()),
        scan_date=datetime.datetime.fromisoformat("2023-01-01T12:00:00"),
        is_active=True,
        image_hashes=["hash1"],
    )
    session.add(listing)
    await session.commit()

    # Act
    deleted = await repo.delete_listing(listing.listing_id)

    # Assert
    assert deleted

    # Act (Ensure the listing is gone)
    retrieved = await repo.get_listing_by_id(listing.listing_id)

    # Assert
    assert retrieved is None


@pytest.mark.asyncio
async def test_get_filtered_listings(session: AsyncSession):
    """Test retrieving filtered listings with pagination."""
    # Arrange
    repo = ListingRepository(session)
    listing_ids = [str(uuid.uuid4()) for _ in range(3)]
    session.add_all([
        Listing(
            listing_id=listing_ids[0],
            scan_date=datetime.datetime.fromisoformat("2025-01-01T12:00:00"),
            is_active=True,
            image_hashes=["hash1"],
        ),
        Listing(
            listing_id=listing_ids[1],
            scan_date=datetime.datetime.fromisoformat("2023-01-02T12:00:00"),
            is_active=False,
            image_hashes=["hash2"],
        ),
        Listing(
            listing_id=listing_ids[2],
            scan_date=datetime.datetime.fromisoformat("2024-01-01T12:00:00"),
            is_active=True,
            image_hashes=["hash3"],
        ),
    ])
    await session.commit()

    # Act
    filters = {"is_active": True}
    listings = await repo.get_filtered_listings(filters, page=1, page_size=2)

    # Assert
    assert len(listings) == 2
    assert listings[0].listing_id == listing_ids[0]
    assert listings[1].listing_id == listing_ids[2]


@pytest.mark.asyncio
async def test_get_filtered_listings_empty_results(session: AsyncSession):
    """Test retrieving filtered listings when no match is found."""
    # Arrange
    repo = ListingRepository(session)

    # Act
    filters = {"is_active": False}
    listings = await repo.get_filtered_listings(filters, page=1, page_size=10)

    # Assert
    assert len(listings) == 0