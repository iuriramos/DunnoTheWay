from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from common.db import Base
from flight.models.bounding_box import (bounding_box_related_to_airports,
                                        is_coordinate_inside_bounding_box)


class ConvectionCell(Base):
    __tablename__ = 'convection_cells'
    
    id = Column(Integer, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    radius = Column(Float)
    timestamp = Column(DateTime)
        
    def __init__(self, latitude, longitude, radius, timestamp):
        self.latitude = latitude
        self.longitude = longitude
        self.radius = radius
        self.timestamp = timestamp

    def __repr__(self):
        return 'ConvectionCell({0}, {1}, {2}, {3}, {4})'.format(
            self.id, self.latitude, self.longitude, self.radius, self.timestamp)

    def __iter__(self):
        yield self.latitude
        yield self.longitude
        yield self.radius

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        # do not compare cell timesamp 
        # since the same cell might be tracked in different timestamps
        return tuple(self) == tuple(other)

    def __lt__(self, other):
        return tuple(self) < tuple(other)

    @staticmethod
    def all_convection_cells(session):
        return session.query(ConvectionCell).all()

    def is_convection_cells_between_airports(self, departure_airport, destination_airport):
        bbox = bounding_box_related_to_airports(departure_airport, destination_airport)
        return is_coordinate_inside_bounding_box(
            coordinate=(self.latitude, self.longitude), bbox=bbox)

            