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
    def flight_plans_from_airports(session, departure_airport, destination_airport):
        '''Return flight plans from departure airport to destination airport'''
        flight_plans = session.query(FlightPlan).filter(
            (FlightPlan.departure_airport == departure_airport),
            (FlightPlan.destination_airport == destination_airport))
        return flight_plans

    @staticmethod
    def all_flight_plans(session):
        return session.query(FlightPlan).all()

    @staticmethod
    def all_callsigns(session):
        flight_plans = FlightPlan.all_flight_plans(session)
        return {flight_plan.callsign for flight_plan in flight_plans}

    @staticmethod
    def flight_plan_from_callsign(session, callsign):
        return session.query(FlightPlan).filter(FlightPlan.callsign == callsign).first()

    @staticmethod
    def split_callsign(callsign):
        '''Split callsign in meaninful chunks (airplane designator and flight number)'''
        airplane_designator, flight_number = callsign[:3], callsign[3:]
        return airplane_designator, flight_number

    ##### TODO: Change method location: flight location or normalizer...
    @staticmethod
    def normalized_flight_locations_related_to_flight_plan(flight_plan):
        '''Return flight locations of flight plan'''
        
        def _normalized_flights_related_to_flight_plan(flight_plan):
            flights = flight_plan.flights
            #### TODO: Change database schema
            return [flight for flight in flights if flight.partition_interval is not None] 

        flight_locations = []
        for flight in _normalized_flights_related_to_flight_plan(flight_plan): 
            flight_locations += flight.flight_locations 
        return flight_locations

