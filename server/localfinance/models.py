from sqlalchemy import (
    Column,
    Index,
    Integer,
    Float,
    Text,
    Unicode,
    ForeignKey,
    DateTime,
    SmallInteger,
    )

from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import HSTORE

from sqlalchemy.ext.hybrid import hybrid_property

from geoalchemy2 import Geometry

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

SRID = 4326
ADMIN_LEVEL_CITY = 5
ADMIN_LEVEL_CITY_ARR = 6

class AdminZone(Base):
    # XXX: Only cities and cities arr at the moment"""
    __tablename__ = 'adminzone'
    id = Column(Integer, primary_key=True)
    admin_level = Column(SmallInteger)
    code_department  = Column(Unicode(2))
    code_city  = Column(Unicode(3))
    name = Column(Unicode(100))
    geometry = Column(Geometry('MULTIPOLYGON', srid=SRID, management=True))

    @hybrid_property
    def code_insee(self):
        return self.code_department + self.code_city

class AdminZoneFinance(Base):
    __tablename__ = 'adminzonefinance'
    id = Column(Integer, primary_key=True)
    adminzone_id   = Column(Integer, ForeignKey('adminzone.id'))
    year = Column(Integer)
    data = Column(MutableDict.as_mutable(HSTORE))

class Stats(Base):
    __tablename__ = 'stats'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100))
    data = Column(MutableDict.as_mutable(HSTORE))
