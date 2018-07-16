from sqlalchemy import Column, Numeric, String, Integer
from tracker.models.base import Base


class Airport(Base):
    __tablename__ = 'airports'

    id = Column(Integer, primary_key=True)
    code = Column(String(3), unique=True, nullable=False) # IATA airport code / location identifier
    name = Column(String, nullable=False)
    latitude = Column(Numeric, nullable=False)
    longitude = Column(Numeric, nullable=False)
    country = Column(String)

    def __init__(self, code, name, latitude, longitude, country):
        self.code = code
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.country = country
        
    def __repr__(self):
        return 'Airport({code})'.format(code=self.code)
