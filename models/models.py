from datetime import datetime

from flask_marshmallow import Schema
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, Column, String, Integer, Boolean, ARRAY, Float
from sqlalchemy.dialects.postgresql import JSON, UUID

from uuid import uuid4

from sqlalchemy.ext.mutable import MutableDict

db = SQLAlchemy()


class OAI_PMH(db.Model):
    __tablename__ = 'OAI_PMH'
    id = Column(Integer, primary_key=True)
    repository_name = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False)
    namespace_identifier = Column(String(150), nullable=False)

    def __init__(self, repository_name, url, namespace_identifier):
        self.repository_name = repository_name
        self.url = url
        self.namespace_identifier = namespace_identifier

    def __str__(self):
        return self.repository_name


class ROAR(db.Model):
    __tablename__ = 'ROAR'
    id = Column(db.Integer, primary_key=True)
    repository_name = Column(String(500), nullable=False)
    home_page = Column(String(500), nullable=False)
    oai_pmh = db.Column(String(150), nullable=True)

    def __init__(self, repository_name, home_page, oai_pmh):
        self.repository_name = repository_name
        self.home_page = home_page
        self.oai_pmh = oai_pmh

    def __str__(self):
        return self.repository_name


class Record(db.Model):
    __tablename__ = 'Record'

    token = Column(UUID(as_uuid=True), primary_key=True, default=str(uuid4()))
    data = Column(MutableDict.as_mutable(JSON))
    created_on = Column(DateTime, default=datetime.utcnow())
    last_updated = Column(DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())
    rating = Column(Float, default=0)
    repository_url = Column(String(500), nullable=False)
    repository_names = Column(ARRAY(String(500)), nullable=False)
    last_item_evaluated = Column(String(20), nullable=False, default='Started')
    is_completed = Column(Boolean, nullable=False, default=False)

    def __init__(self, data, repository_url, repository_names):
        self.data = data
        self.repository_url = repository_url
        self.repository_names = repository_names

    def __str__(self):
        return str(self.token)


class RecordSchema(Schema):
    class Meta:
        model = Record
        fields = (
        'token', 'repository_url', 'repository_names', 'created_on', 'last_updated', 'rating', 'last_item_evaluated',
        'is_completed')
