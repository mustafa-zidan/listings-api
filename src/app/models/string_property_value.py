from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class StringPropertyValue(Base):
    __tablename__ = "test_property_values_str"
    listing_id = Column(String, ForeignKey("test_listings.listing_id"), primary_key=True)
    property_id = Column(Integer, ForeignKey("test_properties.property_id"), primary_key=True)
    value = Column(String, nullable=False)

    listing = relationship("Listing", back_populates="string_properties")
    property = relationship("Property")