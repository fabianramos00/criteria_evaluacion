from sqlalchemy import func, Index, Numeric
from sqlalchemy import Column, String, Integer, Boolean, ARRAY, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    __table_args__ = (
        Index("ix_record_repository_url", "repository_url"),
        Index("ix_record_last_item_evaluated", "last_item_evaluated"),
        Index("ix_record_is_completed", "is_completed"),
        Index("ix_record_updated_at", "updated_at"),
        Index(
            "ix_record_repository_names_gin", "repository_names", postgresql_using="gin"
        ),
        # Trigram index ix_record_repository_names_trgm (array_to_string +
        # gin_trgm_ops) is managed in the Alembic migration.
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    data = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    rating = Column(Numeric(precision=5, scale=2), default=0)
    repository_url = Column(String(500), nullable=False)
    repository_names = Column(ARRAY(String(500)), nullable=False)
    links = Column(JSONB, nullable=True)
    last_item_evaluated = Column(String(20), nullable=False, default="started")
    is_completed = Column(Boolean, nullable=False, default=False)
