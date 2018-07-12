from sqlalchemy import Column, Numeric, String, Integer
from tracker.models.base import Base


class Airport(Base):
    __tablename__ = 'airports'

    id = Column(Integer, primary_key=True)
    code = Column(String(3), unique=True, nullable=False) # IATA airport code / location identifier
    name = Column(String, nullable=False)
    longitude = Column(Numeric, nullable=False)
    latitude = Column(Numeric, nullable=False)
    country = Column(String)

    def __init__(self, code, name, longitude, latitude, country):
        self.code = code
        self.name = name
        self.longitude = longitude
        self.latitude = latitude
        self.country = country
        
