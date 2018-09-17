from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from common.db import Base


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

    def __repr__(self):
        return 'FlightPlan({callsign}, {departure_airport}, {destination_airport})'.format(
            callsign=self.callsign,
            departure_airport=repr(self.departure_airport),
            destination_airport=repr(self.destination_airport))

    @staticmethod
    def normalized_flight_locations_related_to_flight_plan(flight_plan):
        '''Return flight locations of flight plan'''
        
        def _normalized_flights_related_to_flight_plan(flight_plan):
            flights = flight_plan.flights
            # TODO: Change database schema
            return [flight for flight in flights if flight.partition_interval is not None] 

        flight_locations = []
        for flight in _normalized_flights_related_to_flight_plan(flight_plan): 
            flight_locations += flight.flight_locations 
        return flight_locations

