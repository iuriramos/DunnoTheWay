from datetime import datetime
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from common.db import Base


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

    def __hash__(self):
        return hash((self.latitude, self.longitude, self.radius))

    def __eq__(self, other):
        # do not compare cell timesamp 
        # since the same cell might be tracked in different timestamps
        return (self.latitude == other.latitude and
                self.longitude == other.longitude and
                self.radius == other.radius)

    @staticmethod
    def all_convection_cells(session):
        return session.query(ConvectionCell).all()
    

