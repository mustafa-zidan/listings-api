from sqlalchemy import func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import Listing, StringPropertyValue, BooleanPropertyValue, DatasetEntity, Property
from app.schemas.listing import ListingSchema, ListingResult, ListingResponse, PropertyResponse, EntityResponse, \
    ListingFilterSchema


class ListingRepository:
    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session."""
        self.session = session

    async def get_listing_by_id(self, listing_id: str) -> ListingResponse | None:
        """Retrieve a listing by its ID."""
        async def get_listing_with_entities(self, listing_id: str) -> ListingResponse | None:
            """
            Retrieve a listing along with its associated dataset entities.

            Args:
                listing_id (str): The ID of the listing to retrieve.

            Returns:
                ListingResponse | None: A ListingResponse object containing the listing and its entities, or None if not found.
            """
        query = (
            select(Listing)
            .where(Listing.listing_id == listing_id)
            .options(selectinload(Listing.entities))
            .options(selectinload(Listing.boolean_properties))
            .options(selectinload(Listing.string_properties))
        )
        result = await self.session.execute(query)
        listing = result.scalars().first()

        if not listing:
            return None

        # Construct the response
        return ListingResponse(
            listing_id=listing.listing_id,
            scan_date=listing.scan_date,
            is_active=listing.is_active,
            dataset_entity_ids=listing.dataset_entity_ids or [],
            image_hashes=listing.image_hashes,
            properties=[
                PropertyResponse(property_id=p.property_id, value=p.value)
                for p in listing.string_properties + listing.boolean_properties
            ],
            entities=[
                EntityResponse(name=entity.name, data=entity.data)
                for entity in listing.entities
            ],
        )

    async def create_listing_with_nested_objects(self, listing: ListingSchema) -> Listing:
        """Create a new listing and its associated nested properties and entities."""
        # Create the main listing
        new_listing = Listing(
            listing_id=listing.listing_id,
            scan_date=listing.scan_date,
            is_active=listing.is_active,
            image_hashes=listing.image_hashes,
            dataset_entity_ids=[],
        )
        # Handle entities    t
        for entity in listing.entities:
            model_entity = DatasetEntity(
                name=entity.name,
                data=entity.data
            )
            self.session.add(model_entity)
            await self.session.commit()
            new_listing.dataset_entity_ids.append(model_entity.entity_id)

        self.session.add(new_listing)

        # Handle properties
        # TODO: Refactor this to a separate method
        # protect against NoneType
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
        query = select(Listing).where(Listing.listing_id == listing_id)
        result = await self.session.execute(query)
        listing = result.scalars().first()
        if listing:
            await self.session.delete(listing)
            await self.session.commit()
            return True
        return False

    async def get_filtered_listings(self, filters: ListingFilterSchema, page: int = 1,
                                    limit: int = 100) -> ListingResult:
        """
        Retrieves listings with filters and pagination.

        Args:
            filters (ListingFilterSchema): The structured filters for querying listings.
            page (int): The page number for pagination (1-indexed).
            limit (int): The number of listings per page.

        Returns:
            ListingResult: An object containing the filtered listings and the total count.
        """
        query = select(Listing).distinct()

        # Apply filters dynamically
        conditions = []
        if filters.listing_id:
            conditions.append(Listing.listing_id == filters.listing_id)
        if filters.scan_date_from:
            conditions.append(Listing.scan_date >= filters.scan_date_from)
        if filters.scan_date_to:
            conditions.append(Listing.scan_date <= filters.scan_date_to)
        if filters.is_active is not None:
            conditions.append(Listing.is_active == filters.is_active)
        if filters.image_hashes:
            conditions.append(func.array_overlap(Listing.image_hashes, filters.image_hashes))
        if filters.dataset_entities:
            query = query.join(DatasetEntity)
            for key, value in filters.dataset_entities.items():
                conditions.append(DatasetEntity.data[key].astext == value)
        if filters.property_filters:
            query = query.outerjoin(StringPropertyValue).outerjoin(BooleanPropertyValue)
            for property_id, value in filters.property_filters.items():
                conditions.append(
                    or_(
                        and_(StringPropertyValue.property_id == property_id, StringPropertyValue.value == value),
                        and_(BooleanPropertyValue.property_id == property_id, BooleanPropertyValue.value == value),
                    )
                )

        # Apply conditions to the query
        if conditions:
            query = query.where(and_(*conditions))

        # Count total matches
        count_query = query.with_only_columns([func.count()]).order_by(None)
        total_count_result = await self.session.execute(count_query)
        total_count = total_count_result.scalar()

        # Apply pagination
        query = query.order_by(Listing.listing_id).offset((page - 1) * 100).limit(limit)

        # Fetch results
        result = await self.session.execute(query)
        listings = result.scalars().all()

        # Construct the response object
        response = ListingResult(
            listings=[
                ListingResponse(
                    listing_id=listing.listing_id,
                    scan_date=listing.scan_date,
                    is_active=listing.is_active,
                    dataset_entity_ids=listing.dataset_entity_ids or [],
                    image_hashes=listing.image_hashes or [],
                    properties=[
                        PropertyResponse(property_id=p.property_id, value=p.value)
                        for p in listing.string_properties + listing.boolean_properties
                    ],
                    entities=[
                        EntityResponse(name=e.name, data=e.data)
                        for e in listing.dataset_entity_ids
                    ],
                )
                for listing in listings
            ],
            total_count=total_count,
        )

        return response
