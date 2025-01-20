from datetime import datetime
from typing import List, Sequence, Dict

from sqlalchemy import func, or_, and_, tuple_, String, Text, cast, JSON
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects import postgresql


from app.models import Listing, StringPropertyValue, BooleanPropertyValue, DatasetEntity, Property
from app.schemas.listing import ListingSchema, ListingResult, ListingResponse, PropertyResponse, EntityResponse, \
    ListingFilterSchema, UpsertResult, Entity


class ListingRepository:
    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session."""
        self.session = session

    async def get_listing_by_id(self, listing_id: str) -> ListingResponse | None:
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
            dataset_entity_ids=[]
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
            class_ = StringPropertyValue
            if prop.type == "bool":
                class_ = BooleanPropertyValue
            model_property = class_(
                listing_id=new_listing.listing_id,
                property_id=property_obj.property_id,
                value=prop.value
            )
            self.session.add(model_property)
        self.session.add(new_listing)
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

    async def upsert_listings(self, listings: List[ListingSchema]) -> UpsertResult:
        """
        Retrieve all listings with their associated properties and entities.

        Returns:
            list[ListingResponse]: A list of ListingResponse objects.
        """

        # Fetch existing listings and create a dictionary for quick lookup
        existing_listings = await self._fetch_existing_listings([l.listing_id for l in listings])
        existing_map = {l.listing_id: l for l in existing_listings}

        # Separate listings into new and existing
        updated_listings = [
            {"existing": existing_map[listing.listing_id], "updated": listing}
            for listing in listings
            if listing.listing_id in existing_map
        ]
        new_listings = [listing for listing in listings if
                        listing.listing_id not in [l.listing_id for l in existing_listings]]
        for l in updated_listings:
            await self._update_listing(**l)

        # Create new listings
        for listing in new_listings:
            await self.create_listing_with_nested_objects(listing)
        await self.session.commit()
        return UpsertResult(inserted=len(new_listings), updated=len(updated_listings))

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
        """
        Retrieve listings with filters and pagination.

        Args:
            filters (ListingFilterSchema): The structured filters for querying listings.
            page (int): Page number for pagination.
            limit (int): Number of listings per page.

        Returns:
            ListingResult: A structured result object with listings and total count.
        """
        query = (select(Listing)
                 .options(selectinload(Listing.entities))
                 .options(selectinload(Listing.boolean_properties))
                 .options(selectinload(Listing.string_properties))
                 .distinct())

        # Apply filters
        conditions = []
        if filters.listing_id:
            conditions.append(Listing.listing_id == filters.listing_id)
        if filters.scan_date_from:
            conditions.append(Listing.scan_date >= datetime.strptime(filters.scan_date_from, "%Y-%m-%d"))
        if filters.scan_date_to:
            conditions.append(Listing.scan_date <= datetime.strptime(filters.scan_date_to, "%Y-%m-%d"))
        if filters.is_active is not None:
            conditions.append(Listing.is_active == filters.is_active)
        if filters.image_hashes:
            conditions.append(Listing.image_hashes.op("&&")(filters.image_hashes))
        if filters.dataset_entities:
            query = query.join(DatasetEntity,DatasetEntity.entity_id == func.any_(Listing.dataset_entity_ids))
            dataset_entities_conditions = []
            for key, value in filters.dataset_entities.items():
                dataset_entities_conditions.append(DatasetEntity.data[key].astext == value)
            conditions.append(and_(*dataset_entities_conditions))
        if filters.property_filters:
            query = query.join(StringPropertyValue).join(BooleanPropertyValue)
            property_conditions = []
            for property_id, value in filters.property_filters.items():
                if isinstance(value, str):
                    property_conditions.append(
                        or_(
                            StringPropertyValue.property_id == property_id, StringPropertyValue.value == value
                        )
                    )
                elif isinstance(value, bool):
                    property_conditions.append(
                        or_(
                            BooleanPropertyValue.property_id == property_id, BooleanPropertyValue.value == value
                        )
                    )
            conditions.append(and_(*property_conditions))
        if conditions:
            query = query.where(and_(*conditions))

        # Count total matches
        count_query = query.select_from(Listing).with_only_columns(func.count("*"))
        total_count_result = await self.session.execute(count_query)
        total_count = total_count_result.scalar()

        # Pagination
        query = query.order_by(Listing.listing_id).offset((page - 1) * limit).limit(limit)

        # Execute query
        result = await self.session.execute(query)
        listings = result.scalars().all()

        # Construct response
        return ListingResult(
            listings=[
                ListingResponse(
                    listing_id=listing.listing_id,
                    scan_date=listing.scan_date,
                    is_active=listing.is_active,
                    dataset_entity_ids=listing.dataset_entity_ids,
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
                for listing in listings
            ],
            total=total_count,
        )

    async def _fetch_existing_listings(self, listing_ids: list[str]) -> Sequence[Listing]:
        """
        Fetch existing listings by their IDs.

        Args:
            listing_ids (list[str]): List of listing IDs to fetch.

        Returns:
            list[Listing]: A list of existing Listing objects.
        """
        query = (
            select(Listing)
            .where(Listing.listing_id.in_(listing_ids))
            .options(
                selectinload(Listing.string_properties),
                selectinload(Listing.boolean_properties),
                selectinload(Listing.entities),
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def _update_listing(self, existing: Listing, updated: ListingSchema) -> None:
        """
        Update an existing listing and its related data.

        Args:
            existing (Listing): The existing listing to update.
            updated (ListingSchema): The updated listing data.
        """

        # Update core fields
        existing.scan_date = updated.scan_date
        existing.is_active = updated.is_active
        existing.image_hashes = updated.image_hashes
        self.session.add(existing)
        # Update properties
        await self._update_properties(existing, updated)
        await self._update_entities(existing, updated)
        self.session.add(existing)
        await self.session.commit()

    async def _update_properties(self, existing: Listing, updated: ListingSchema) -> None:
        """
        Update the properties (string and boolean) of a listing based on the updated data.

        Args:
            existing (Listing): The existing listing object to update.
            updated (ListingSchema): The updated listing schema object containing new property data.

        Returns:
            None
        """
        # Create a dictionary of (name, type) to value mappings
        names_and_types = {(prop.name, prop.type): prop.value for prop in updated.properties}

        # Fetch properties matching the given names and types
        matching_properties = await self._fetch_matching_properties(names_and_types)

        existing.string_properties = []
        existing.boolean_properties = []
        for updated_property in updated.properties:
            prop = matching_properties.get((updated_property.name, updated_property.type))
            if not prop:
                prop = Property(name=updated_property.name, type=updated_property.type)
                self.session.add(prop)
                await self.session.commit()
            class_ = StringPropertyValue
            if prop.type == "bool":
                class_ = BooleanPropertyValue
            model_property = class_(
                listing_id=existing.listing_id,
                property_id=prop.property_id,
                value=updated_property.value
            )
            self.session.add(model_property)
            existing.string_properties.append(
                model_property) if prop.type == "str" else existing.boolean_properties.append(
                model_property)

    async def _fetch_matching_properties(
            self, names_and_types: Dict[tuple, str]
    ) -> Dict[tuple, Property]:
        """
        Fetch properties matching the given names and types.

        Args:
            names_and_types (Dict[tuple, str]): A dictionary of (name, type) to value mappings.

        Returns:
            Dict[tuple, Property]: A dictionary of (name, type) to Property objects.
        """
        query = select(Property).where(
            tuple_(Property.name, Property.type).in_(names_and_types.keys())
        )
        result = await self.session.execute(query)
        return {(prop.name, prop.type): prop for prop in result.scalars().all()}

    async def _update_entities(self, existing: Listing, updated: ListingSchema):
        """
        Update entities for a listing, adding new ones, updating existing ones, and removing stale ones.

        Args:
            existing (Listing): The existing Listing object from the database.
            updated (ListingSchema): The updated ListingSchema object containing new entity data.
        """
        # upsert entities
        existing_entities = await self._upsert(updated.entities)
        existing.dataset_entity_ids = [entity.entity_id for entity in existing_entities]

    async def _upsert(self, entities: List[Entity]) -> Sequence[DatasetEntity]:
        """
        Fetch existing entities by their IDs.

        Args:
            entities (list[Entity]): List of entity objects to update or create
        Returns:
            list[DatasetEntity]: A list of existing DatasetEntity objects.
        """
        query = select(DatasetEntity).where(DatasetEntity.name.in_([i.name for i in entities]))
        result = await self.session.execute(query)
        existing_entities = result.scalars().all()
        existing_map = {entity.name: entity for entity in existing_entities}
        upserted = list()
        for entity in entities:
            if entity.name in existing_map:
                existing_map[entity.name].data = entity.data
                upserted.append(existing_map[entity.name])
                self.session.add(existing_map[entity.name])
            else:
                new_entity = DatasetEntity(name=entity.name, data=entity.data)
                self.session.add(new_entity)
                upserted.append(new_entity)
        await self.session.commit()
        return upserted
