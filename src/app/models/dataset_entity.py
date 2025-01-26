from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSON

from app.models.base import Base


class DatasetEntity(Base):
    __tablename__ = "test_dataset_entities"
    entity_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    data = Column(JSON)