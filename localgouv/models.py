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

GENDER_MALE = 0
GENDER_FEMALE = 1
class Politician(Base):
    __tablename__ = 'politician'
    id = Column(Integer, primary_key=True)
    firstname = Column(Unicode(100))
    lastname = Column(Unicode(100))
    gender = Column(SmallInteger)

class Mandate(Base):
    """ XXX: have only mayor for the moment"""
    __tablename__ = 'mandate'
    id = Column(Integer, primary_key=True)
    politician_id   = Column(Integer, ForeignKey('politician.id'))
    adminzone_id   = Column(Integer, ForeignKey('adminzone.id'))
    position = Column(Unicode(100))

class MunicipalElectionResult(Base):
    __tablename__ = 'municipalelectionresult'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    politician_id   = Column(Integer, ForeignKey('politician.id'))
    adminzone_id   = Column(Integer, ForeignKey('adminzone.id'))
    vote = Column(Integer)
    pct_vote = Column(Float)

class AdminZoneFinance(Base):
    __tablename__ = 'adminzonefinance'
    id = Column(Integer, primary_key=True)
    adminzone_id   = Column(Integer, ForeignKey('adminzone.id'))
    year = Column(Integer)
    data = Column(MutableDict.as_mutable(HSTORE))
