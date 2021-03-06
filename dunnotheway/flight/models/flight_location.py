import math
from sqlalchemy import Column, Numeric, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from common.db import Base
from common.utils import from_timestamp_to_datetime
# from .flight import Flight


class FlightLocation(Base):
    __tablename__ = 'flight_locations'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    longitude = Column(Numeric, nullable=False)
    latitude = Column(Numeric, nullable=False)
    altitude = Column(Numeric, nullable=False)
    speed = Column(Numeric, nullable=False)
    flight_id = Column(Integer, ForeignKey('flights.id'), nullable=False)
    # flight = relationship('Flight', back_populates='flight_locations')

    def __init__(self, timestamp, longitude, latitude, altitude, speed, flight):
        self.timestamp = timestamp
        self.longitude = longitude
        self.latitude = latitude
        self.altitude = altitude
        self.speed = speed
        self.flight = flight

    def __repr__(self):
        return 'FlightLocation({timestamp}, {longitude}, {latitude}, {altitude}, {flight})'.format(
            timestamp=self.timestamp,
            longitude=self.longitude,
            latitude=self.latitude,
            altitude=self.altitude,
            flight=repr(self.flight))

    def __iter__(self):
        yield float(self.latitude)
        yield float(self.longitude)
        yield float(self.altitude)

    @staticmethod
    def construct_flight_location_from_state_and_flight(state, flight):
        '''Return flight location from state-vector and flight object'''
        return FlightLocation(
            timestamp=from_timestamp_to_datetime(state.time_position), # timestamp as datetime object
            longitude=state.longitude,
            latitude=state.latitude,
            altitude=state.baro_altitude, # barometric altitude
            speed=state.velocity,
            flight=flight
        )        

    @property
    def coordinates(self):
        '''Transform flight location into raw tuple (latitude, longitude, altitude)'''
        return tuple(self)

    @staticmethod
    def check_equal_flight_locations(this, that):
        return (this and that and tuple(this) == tuple(that))