from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from tracker.models.base import Base


class Airplane(Base):
    __tablename__ = 'airplanes'

    id = Column(Integer, primary_key=True)
    icao_code = Column(String(6), unique=True, nullable=False) # ICAO 24-bit identifier
    airline_id = Column(Integer, ForeignKey('airlines.id'))
    airline = relationship('Airline', backref='airplanes')
    manufacturer = Column(String)
    model = Column(String)

    def __init__(self, icao_code, airline, manufacturer=None, model=None):
        self.icao_code = icao_code
        self.airline = airline
        self.manufacturer = manufacturer
        self.model = model

    def __repr__(self):
        return 'Airplane({icao_code}, {airline})'.format(
            icao_code=self.icao_code,
            airline=self.airline
        )
