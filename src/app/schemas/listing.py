"""
This module contains Pydantic schemas
"""
from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class Property(BaseModel):
    """
    Represents a property with a name, type, and value.
    """
    name: str = Field(..., description="The name of the property.")
    type: str = Field(..., description="The type of the property (e.g., 'str', 'bool').")
    value: str | bool = Field(..., description="The value of the property.")


class Entity(BaseModel):
    """
    Represents a dataset entity with associated data.
    """
    name: str = Field(..., description="The name of the dataset entity.")
    data: Dict[str, Any] = Field(..., description="Arbitrary data associated with the entity.")


class ListingSchema(BaseModel):
    """
    Represents a listing with associated properties and entities.
    """
    listing_id: str = Field(..., description="Unique identifier for the listing.")
    scan_date: datetime = Field(..., description="The date and time of the listing scan.")
    is_active: bool = Field(..., description="Whether the listing is active.")
    image_hashes: List[str] = Field(..., description="List of image hash strings.")
    properties: List[Property] = Field(..., description="List of associated properties.")
    entities: List[Entity] = Field(..., description="List of associated dataset entities.")

    @field_validator("scan_date", mode="before")
    def parse_scan_date(cls, value):
        if isinstance(value, datetime):
            return value  # Already a datetime object
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"Invalid date format for scan_date: {value}")


class UpsertListingsSchema(BaseModel):
    """
    Represents the request schema for upserting listings.
    """
    listings: List[ListingSchema] = Field(..., description="List of listings to upsert.")

class ListingFilterSchema(BaseModel):
    """
    Represents the filters that can be applied when querying listings.
    """
    listing_id: str | None = Field(None, description="Filter by listing ID.")
    scan_date_from: str | None = Field(
        default=None,
        description="Filter by minimum scan date (YYYY-MM-DD)."
    )
    scan_date_to: str | None = Field(
        default=None,
        description="Filter by maximum scan date (YYYY-MM-DD)."
    )
    is_active: bool | None = Field(default=None, description="Filter by active status.")
    image_hashes: List[str] | None = Field(default=None, description="Filter by image hashes.")
    dataset_entities: Dict[str, str] | None = Field(
        default=None,
        description="Filter by dataset entities JSON data."
    )
    property_filters: Dict[int, str] = Field(
        default=None,
        description="Dictionary of property filters (property_id: expected_value)."
    )


class PropertyResponse(BaseModel):
    """
    Represents a single property associated with a listing.
    """
    property_id: int = Field(..., description="The unique identifier for the property.")
    value: Any = Field(..., description="The value of the property (string or boolean).")


class EntityResponse(BaseModel):
    """
    Represents a dataset entity associated with a listing.
    """
    name: str = Field(..., description="The name of the dataset entity.")
    data: Dict[str, Any] = Field(..., description="Arbitrary JSON data associated with the entity.")


class ListingResponse(BaseModel):
    """
    Represents the response for a single listing, including its associated properties and entities.
    """
    listing_id: str = Field(..., description="The unique identifier for the listing.")
    scan_date: datetime = Field(..., description="The date and time when the listing was scanned.")
    is_active: bool = Field(..., description="Indicates whether the listing is active.")
    image_hashes: List[str] = Field(
        default_factory=list,
        description="A list of image hashes associated with the listing."
    )
    dataset_entity_ids: List[int] | None = Field(
        default_factory=list,
        description="A list of dataset entity IDs linked to the listing."
    )
    properties: List[PropertyResponse] | None = Field(
        default_factory=list,
        description="A list of properties associated with the listing."
    )
    entities: List[EntityResponse] | None = Field(
        default_factory=list,
        description="A list of entities associated with the listing."
    )


class ListingResult(BaseModel):
    """
    Represents the result of a listing query, including a list of listings and the total count.
    """
    listings: List[ListingResponse] = Field(..., description="List of listing responses.")
    total: int = Field(..., description="Total count of listings matching the filters.")


class UpsertResult(BaseModel):
    """
    Represents the result of an upsert operation for listings.
    """
    inserted: int = Field(0, description="Number of new listings inserted.")
    updated: int = Field(0, description="Number of existing listings updated.")
    message: str = Field(
        default= f"{inserted} new listing(s) inserted successfully, "
                 f"{updated} existing listings updated successfully",
        description="Success message with counts of inserted and updated records.")
