from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from common.db import Base
from .flight_location import FlightLocation
from .flight_plan import FlightPlan
from flight.opensky.models.state_vector import StateVector


class Flight(Base):
    __tablename__ = 'flights'

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime)
    airplane_id = Column(Integer, ForeignKey('airplanes.id'))
    airplane = relationship('Airplane', backref='flights')
    flight_plan_id = Column(Integer, ForeignKey('flight_plans.id'))
    flight_plan = relationship('FlightPlan', backref='flights')
    flight_locations = relationship('FlightLocation', back_populates='flight', cascade="all, delete-orphan")

    def __init__(self, airplane, flight_plan):
        self.created_date = datetime.now()
        self.airplane = airplane
        self.flight_plan = flight_plan
        
    def __repr__(self):
        return 'Flight({id}, {airplane})'.format(
            id=self.id,
            airplane=repr(self.airplane))

    @staticmethod
    def construct_flight_from_state(session, state):
        '''Return flight object from state-vector.'''
        flight_plan = FlightPlan.flight_plan_from_callsign(session, state.callsign)
        airplane = StateVector.airplane_from_state(session, state)
        return Flight(airplane=airplane, flight_plan=flight_plan)
        
    def remove_duplicated_flight_locations(self):
        '''Remove duplicated flight locations.'''
        unique_flight_locations = []
        prev = None
        for curr in self.flight_locations:
            if not FlightLocation.check_equal_flight_locations(prev, curr):
                unique_flight_locations.append(curr)
            prev = curr
        self.flight_locations = unique_flight_locations
