from sqlalchemy import Column, String, DateTime, Boolean, ARRAY, Integer
from sqlalchemy.orm import relationship
from app.models.base import Base


class Listing(Base):
    __tablename__ = "test_listings"
    listing_id = Column(String, primary_key=True)
    scan_date = Column(DateTime)
    is_active = Column(Boolean)
    dataset_entity_ids = Column(ARRAY(Integer))
    image_hashes = Column(ARRAY(String))

    string_properties = relationship("StringPropertyValue", back_populates="listing", cascade="all, delete-orphan")
    boolean_properties = relationship("BooleanPropertyValue", back_populates="listing", cascade="all, delete-orphan")

    entities = relationship(
        "DatasetEntity",
        primaryjoin="any_(Listing.dataset_entity_ids)==foreign(DatasetEntity.entity_id)",
        viewonly=True,
    )