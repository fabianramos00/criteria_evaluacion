from sqlalchemy import func
from sqlalchemy import Column, String, Integer, Boolean, ARRAY, Float, DateTime
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.ext.mutable import MutableDict
from uuid import uuid4
from src.database.session import Base


class OAI_PMH(Base):
    __tablename__ = "OAI_PMH"
    id = Column(Integer, primary_key=True)
    repository_name = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False)
    namespace_identifier = Column(String(150), nullable=False)


class ROAR(Base):
    __tablename__ = "ROAR"
    id = Column(Integer, primary_key=True)
    repository_name = Column(String(500), nullable=False)
    home_page = Column(String(500), nullable=False)
    oai_pmh = Column(String(150), nullable=True)


class Record(Base):
    __tablename__ = "Record"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    data = Column(MutableDict.as_mutable(JSON), default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    rating = Column(Float, default=0)
    repository_url = Column(String(500), nullable=False)
    repository_names = Column(ARRAY(String(500)), nullable=False)
    links = Column(ARRAY(MutableDict.as_mutable(JSON)), nullable=True)
    last_item_evaluated = Column(String(20), nullable=False, default="started")
    is_completed = Column(Boolean, nullable=False, default=False)
