from sqlalchemy import Column, Integer, String
from app.models.base import Base


class Property(Base):
    __tablename__ = "test_properties"
    property_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # Values can be 'string' or 'boolean'