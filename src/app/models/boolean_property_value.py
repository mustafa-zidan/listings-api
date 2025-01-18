from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class BooleanPropertyValue(Base):
    __tablename__ = "test_property_values_bool"
    listing_id = Column(String, ForeignKey("test_listings.listing_id"), primary_key=True)
    property_id = Column(Integer, ForeignKey("test_properties.property_id"), primary_key=True)
    value = Column(Boolean, nullable=False)

    listing = relationship("Listing", back_populates="boolean_properties")
    property = relationship("Property")