from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from tracker.models.base import Base


class FlightPlan(Base):
    __tablename__ = 'flight_plans'

    id = Column(Integer, primary_key=True)
    callsign = Column(String, unique=True, nullable=False)
    departure_airport_id = Column(Integer, ForeignKey('airports.id'))
    departure_airport = relationship('Airport', foreign_keys=[departure_airport_id], backref='departure_flightplans')
    destination_airport_id = Column(Integer, ForeignKey('airports.id'))
    destination_airport = relationship('Airport', foreign_keys=[destination_airport_id], backref='destination_flightplans')

    def __init__(self, callsign, departure_airport, destination_airport):
        self.callsign = callsign
        self.departure_airport = departure_airport
        self.destination_airport = destination_airport

