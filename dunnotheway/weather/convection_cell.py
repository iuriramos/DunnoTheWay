from datetime import datetime
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from common.db import Base

class ConvectionCell(Base):
    __tablename__ = 'convection_cells'
    
    id = Column(Integer, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    radius = Column(Float)
    cluster = Column(Integer)
        
    def __init__(self, latitude, longitude, radius, cluster=None):
        self.latitude = latitude
        self.longitude = longitude
        self.radius = radius
        self.cluster = cluster

    def __repr__(self):
        return 'ConvectionCell({0}, {1}, {2})'.format(
            self.latitude, self.longitude, self.radius)

    def __hash__(self):
        return hash((self.latitude, self.longitude, self.radius))

    def __eq__(self, other):
        return (self.latitude == other.latitude and
                self.longitude == other.longitude and
                self.radius == other.radius)
    

