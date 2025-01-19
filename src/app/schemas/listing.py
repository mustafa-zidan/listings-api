from pydantic import BaseModel, Field
from typing import List, Union, Optional
from datetime import datetime


class Property(BaseModel):
    name: str = Field(..., description="The name of the property")
    type: str = Field(..., description="The type of the property (e.g., 'str', 'bool')")
    value: Union[str, bool] = Field(..., description="The value of the property")


class Entity(BaseModel):
    name: str = Field(..., description="The name of the dataset entity")
    data: dict = Field(..., description="Arbitrary data associated with the entity")


class ListingSchema(BaseModel):
    listing_id: str = Field(..., description="Unique identifier for the listing")
    scan_date: datetime = Field(..., description="The date and time of the listing scan")
    is_active: bool = Field(..., description="Whether the listing is active")
    image_hashes: List[str] = Field(..., description="List of image hash strings")
    properties: List[Property] = Field(..., description="List of associated properties")
    entities: List[Entity] = Field(..., description="List of associated dataset entities")

