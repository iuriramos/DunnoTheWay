import math
from sqlalchemy import Column, Numeric, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from tracker.models.base import Base


class FlightLocation(Base):
    __tablename__ = 'flight_locations'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    longitude = Column(Numeric, nullable=False)
    latitude = Column(Numeric, nullable=False)
    altitude = Column(Numeric, nullable=False)
    speed = Column(Numeric, nullable=False)
    flight_id = Column(Integer, ForeignKey('flights.id'), nullable=False)
    flight = relationship("Flight", back_populates="flight_locations")

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
            flight=repr(self.flight)
        )
 
