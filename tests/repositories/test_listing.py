from datetime import datetime
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.repositories.listing import ListingRepository
from app.schemas import ListingSchema
from app.schemas.listing import Entity
from app.schemas.listing import ListingFilterSchema
from app.schemas.listing import Property


@pytest.mark.asyncio
async def test_get_listing_by_id(session: AsyncSession):
    """Test retrieving a listing by its ID."""
    # Arrange
    repo = ListingRepository(session)
    listing = Listing(
        listing_id="test123",
        scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
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
        scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
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
    await repo.create_listing_with_nested_objects(listing_data)
    await session.commit()
    created_listing = await repo.get_listing_by_id(listing_data.listing_id)

    # Assert
    assert created_listing.listing_id == listing_data.listing_id
    assert created_listing.scan_date == listing_data.scan_date
    assert created_listing.is_active
    assert created_listing.image_hashes == ["hash1"]
    assert len(created_listing.dataset_entity_ids) == 1
    assert len(created_listing.properties) == 2
    assert len(created_listing.image_hashes) == len(listing_data.image_hashes)


@pytest.mark.asyncio
async def test_create_listing_with_empty_properties(session: AsyncSession):
    """Test creating a listing with no properties."""
    # Arrange
    repo = ListingRepository(session)
    listing_data = ListingSchema(
        listing_id=str(uuid.uuid4()),
        scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
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
        scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
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
async def test_upsert_new_listings(session: AsyncSession):
    """Test inserting new listings into the database."""
    # Arrange
    repo = ListingRepository(session)
    listings = [
        ListingSchema(
            listing_id="123",
            scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
            is_active=True,
            image_hashes=["hash1"],
            properties=[
                Property(name="prop1", type="str", value="value1"),
                Property(name="prop2", type="bool", value=True),
            ],
            entities=[
                Entity(name="entity1", data={"key": "value"}),
                Entity(name="entity2", data={"key": "value"}),
            ],
        )
    ]

    # Act
    results = await repo.upsert_listings(listings)

    # Assert
    assert results.inserted == 1
    assert results.updated == 0

@pytest.mark.asyncio
async def test_update_existing_listings(session: AsyncSession):
    """Test updating existing listings in the database."""
    # Arrange: Insert existing data
    repo = ListingRepository(session)
    listing_data = ListingSchema(
        listing_id=str(uuid.uuid4()),
        scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
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

    created_listing = await repo.create_listing_with_nested_objects(listing_data)
    await session.commit()

    updated_listings = [
        ListingSchema(
            listing_id=created_listing.listing_id,
            scan_date=datetime.fromisoformat("2025-01-02T12:00:00"),
            is_active=False,
            image_hashes=["hash2"],
            properties=[
                Property(name="prop3", type="str", value="value3"),
                Property(name="prop4", type="bool", value=False),
            ],
            entities=[
                Entity(name="entity_two", data={"key2": 43}),
            ],
        )
    ]

    # Act
    results = await repo.upsert_listings(updated_listings)

    # Assert
    assert results.inserted == 0
    assert results.updated == 1
    listing = await repo.get_listing_by_id(created_listing.listing_id)
    assert listing.scan_date == datetime.fromisoformat("2025-01-02T12:00:00")
    assert not listing.is_active
    assert listing.image_hashes == ["hash2"]
    assert len(listing.dataset_entity_ids) == 1
    assert listing.properties[0].value == "value3"


@pytest.mark.asyncio
async def test_get_filtered_listings_pagination(session: AsyncSession):
    """Test retrieving listings with pagination."""
    # Arrange: Insert listings into the database
    repo = ListingRepository(session)
    session.add_all([
        Listing(listing_id=str(i),
                scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
                is_active=True,
                image_hashes=[f"hash{i}"]
                )
        for i in range(1, 201)  # Add 200 listings
    ])
    await session.commit()

    # Act
    filters = ListingFilterSchema()
    result = await repo.get_filtered_listings(filters, page=1, limit=100)

    # Assert
    assert len(result.listings) == 100
    assert result.total == 200

@pytest.mark.asyncio
async def test_get_filtered_listings_by_listing_id(session: AsyncSession):
    """Test filtering listings by listing ID."""
    # Arrange
    repo = ListingRepository(session)
    session.add_all([
        Listing(listing_id="123",
                scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
                is_active=True,
                image_hashes=["hash1"]
        ),
        Listing(
            listing_id="456",
            scan_date=datetime.fromisoformat("2025-01-02T12:00:00"),
            is_active=True,
            image_hashes=["hash2"]
        ),
    ])
    await session.commit()

    # Act
    filters = ListingFilterSchema(listing_id="123")
    result = await repo.get_filtered_listings(filters, page=1, limit=100)

    # Assert
    assert len(result.listings) == 1
    assert result.listings[0].listing_id == "123"


@pytest.mark.asyncio
async def test_get_filtered_listings_date_range(session: AsyncSession):
    """Test filtering listings by date range."""
    # Arrange
    repo = ListingRepository(session)
    session.add_all([
        Listing(listing_id="123",
                scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
                is_active=True,
                image_hashes=["hash1"]
        ),
        Listing(
            listing_id="456",
            scan_date=datetime.fromisoformat("2025-01-02T12:00:00"),
            is_active=True,
            image_hashes=["hash2"]
        ),
    ])
    await session.commit()

    # Act
    filters = ListingFilterSchema(scan_date_from="2025-01-01", scan_date_to="2025-01-02")
    result = await repo.get_filtered_listings(filters, page=1, limit=100)

    # Assert
    assert len(result.listings) == 1
    assert result.listings[0].listing_id == "123"


@pytest.mark.asyncio
async def test_get_filtered_listings_by_is_active(session: AsyncSession):
    """Test filtering listings by active status."""
    # Arrange
    repo = ListingRepository(session)
    session.add_all([
        Listing(listing_id="123",
                scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
                is_active=True,
                image_hashes=["hash1"]
        ),
        Listing(
            listing_id="456",
            scan_date=datetime.fromisoformat("2025-01-02T12:00:00"),
            is_active=False,
            image_hashes=["hash2"]
        ),
    ])
    await session.commit()

    # Act
    filters = ListingFilterSchema(is_active=True)
    result = await repo.get_filtered_listings(filters, page=1, limit=100)

    # Assert
    assert len(result.listings) == 1
    assert result.listings[0].listing_id == "123"

@pytest.mark.asyncio
async def test_get_filtered_listings_by_image_hashes(session: AsyncSession):
    """Test filtering listings by image hashes."""
    # Arrange
    repo = ListingRepository(session)
    session.add_all([
        Listing(listing_id="123",
                scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
                is_active=True,
                image_hashes=["hash1"]
        ),
        Listing(
            listing_id="456",
            scan_date=datetime.fromisoformat("2025-01-02T12:00:00"),
            is_active=True,
            image_hashes=["hash2"]
        ),
    ])
    await session.commit()

    # Act
    filters = ListingFilterSchema(image_hashes=["hash1"])
    result = await repo.get_filtered_listings(filters, page=1, limit=100)

    # Assert
    assert len(result.listings) == 1
    assert result.listings[0].listing_id == "123"


@pytest.mark.asyncio
async def test_get_filtered_listings_combined_filters(session: AsyncSession):
    """Test filtering listings by multiple filters."""
    # Arrange
    repo = ListingRepository(session)
    session.add_all([
        Listing(listing_id="123",
                scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
                is_active=True,
                image_hashes=["hash1"]
        ),
        Listing(
            listing_id="456",
            scan_date=datetime.fromisoformat("2025-01-02T12:00:00"),
            is_active=False,
            image_hashes=["hash2"]
        ),
    ])
    await session.commit()

    # Act
    filters = ListingFilterSchema(listing_id="123", is_active=True)
    result = await repo.get_filtered_listings(filters, page=1, limit=100)

    # Assert
    assert len(result.listings) == 1
    assert result.listings[0].listing_id == "123"

@pytest.mark.asyncio
async def test_get_filtered_listings_by_property_filters(session: AsyncSession):
    """Test filtering listings by property filters."""
    # Arrange
    repo = ListingRepository(session)
    listings_data = [
        ListingSchema(
            listing_id="123",
            scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
            is_active=True,
            image_hashes=["hash1"],
            properties=[
                Property(name="prop1", type="str", value="value1"),
                Property(name="prop2", type="bool", value=True),
            ],
            entities=[
                Entity(name="entity1", data={"key": "value"}),
            ],
        ),
        ListingSchema(
            listing_id="456",
            scan_date=datetime.fromisoformat("2025-01-02T12:00:00"),
            is_active=False,
            image_hashes=["hash2"],
            properties=[
                Property(name="prop3", type="str", value="value2"),
                Property(name="prop4", type="bool", value=False),
            ],
            entities=[
                Entity(name="entity2", data={"key": "value"}),
            ],
        ),
    ]
    await repo.upsert_listings(listings_data)
    expected = await repo.get_listing_by_id("123")
    expected_property = expected.properties[0]
    # Act
    filters = ListingFilterSchema(property_filters={expected_property.property_id: expected_property.value})
    result = await repo.get_filtered_listings(filters, page=1, limit=100)

    # Assert
    assert len(result.listings) == 1
    assert result.listings[0].listing_id == "123"

@pytest.mark.asyncio
async def test_get_filtered_listings_by_dataset_entities(session: AsyncSession):
    """Test filtering listings by dataset entities."""
    # Arrange
    repo = ListingRepository(session)
    listings_data = [
        ListingSchema(
            listing_id="123",
            scan_date=datetime.fromisoformat("2025-01-01T12:00:00"),
            is_active=True,
            image_hashes=["hash1"],
            properties=[
                Property(name="prop1", type="str", value="value1"),
                Property(name="prop2", type="bool", value=True),
            ],
            entities=[
                Entity(name="entity1", data={"key": "value"}),
            ],
        ),
        ListingSchema(
            listing_id="456",
            scan_date=datetime.fromisoformat("2025-01-02T12:00:00"),
            is_active=False,
            image_hashes=["hash2"],
            properties=[
                Property(name="prop3", type="str", value="value2"),
                Property(name="prop4", type="bool", value=False),
            ],
            entities=[
                Entity(name="entity2", data={"key2": "value2"}),
            ],
        ),
    ]
    await repo.upsert_listings(listings_data)


    # Act
    filters = ListingFilterSchema(dataset_entities={"key2": "value2"})
    result = await repo.get_filtered_listings(filters, page=1, limit=100)

    # Assert
    assert len(result.listings) == 1
    assert result.listings[0].listing_id == "456"
