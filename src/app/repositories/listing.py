from typing import Annotated, Sequence

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_session
from app.models import Listing, StringPropertyValue, BooleanPropertyValue, DatasetEntity, Property
from app.schemas.listing import ListingSchema

SessionDep = Annotated[AsyncSession, Depends(get_session())]


class ListingRepository:
    def __init__(self, session: SessionDep):
        """Initialize the repository with a database session."""
        self.session = session

    async def get_listing_by_id(self, listing_id: str) -> Listing|None:
        """Retrieve a listing by its ID."""
        query = select(Listing).where(Listing.listing_id == listing_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create_listing_with_nested_objects(self, listing: ListingSchema) -> Listing:
        """Create a new listing and its associated nested properties and entities."""
        # Create the main listing
        new_listing = Listing(
            listing_id=listing.listing_id,
            scan_date=listing.scan_date,
            is_active=listing.is_active,
            image_hashes=listing.image_hashes
        )
        self.session.add(new_listing)

        # Handle properties
        for prop in listing.properties:
            property_obj = await self._get_or_create_property(prop.name, prop.type)
            if prop.type == "str":
                self.session.add(
                    StringPropertyValue(
                        listing_id=new_listing.listing_id,
                        property_id=property_obj.property_id,
                        value=prop.value
                    )
                )
            elif prop.type == "bool":
                self.session.add(
                    BooleanPropertyValue(
                        listing_id=new_listing.listing_id,
                        property_id=property_obj.property_id,
                        value=prop.value
                    )
                )

        # Handle entities
        for entity in listing.entities:
            self.session.add(
                DatasetEntity(
                    name=entity.name,
                    data=entity.data
                )
            )

        await self.session.commit()
        return new_listing

    async def _get_or_create_property(self, name: str, type_: str) -> Property:
        """Retrieve a property by name and type or create it if it doesn't exist."""
        query = select(Property).where(Property.name == name, Property.type == type_)
        result = await self.session.execute(query)
        property_obj = result.scalars().first()

        if not property_obj:
            property_obj = Property(name=name, type=type_)
            self.session.add(property_obj)
            await self.session.commit()
        return property_obj

    async def delete_listing(self, listing_id: str) -> bool:
        """Delete a listing by its ID."""
        listing = await self.get_listing_by_id(listing_id)
        if listing:
            await self.session.delete(listing)
            await self.session.commit()
            return True
        return False

    async def get_filtered_listings(self, filters: dict, page: int, page_size: int) -> Sequence[Listing]:
        """Retrieve listings based on filters with pagination."""
        query = select(Listing)

        # Apply filters dynamically
        if "is_active" in filters:
            query = query.where(Listing.is_active == filters["is_active"])
        if "scan_date" in filters:
            query = query.where(Listing.scan_date == filters["scan_date"])

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        return result.scalars().all()