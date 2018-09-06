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
    partition_interval = Column(Numeric)
    longitude_based = Column(Boolean)
    flight_locations = relationship('FlightLocation', back_populates='flight', cascade="all, delete-orphan")

    def __init__(self, airplane, flight_plan, partition_interval=None, longitude_based=None):
        self.created_date = datetime.now()
        self.airplane = airplane
        self.flight_plan = flight_plan
        self.partition_interval = partition_interval
        self.longitude_based = longitude_based

    def __repr__(self):
        return 'Flight({airplane})'.format(airplane=repr(self.airplane))
