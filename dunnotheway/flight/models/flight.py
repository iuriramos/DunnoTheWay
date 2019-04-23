from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from common.db import Base


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