from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from tracker.models.base import Base


class Airline(Base):
    __tablename__ = 'airlines'

    id = Column(Integer, primary_key=True)
    icao_code = Column(String(3), unique=True, nullable=False) # ICAO airline designators
    name = Column(String)
    country = Column(String)
    
    def __init__(self, icao_code, name, country):
        self.icao_code = icao_code
        self.name = name
        self.country = country

    def __repr__(self):
        return 'Airline({icao_code}, {name}, {country})'.format(
            icao_code=self.icao_code,
            name=self.name,
            country=self.country
        )
