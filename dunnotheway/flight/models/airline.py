from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from common.db import Base
from flight.models.flight_plan import FlightPlan


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
        return 'Airline({icao_code}, {name})'.format(
            icao_code=self.icao_code,
            name=self.name)

    @staticmethod
    def airline_from_callsign(session, callsign):
        '''Return Airline associated with callsign'''
        icao_code, _ = FlightPlan.split_callsign(callsign)
        return session.query(Airline).filter(Airline.icao_code == icao_code).first()