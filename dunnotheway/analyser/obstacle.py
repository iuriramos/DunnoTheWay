from sqlalchemy import Column, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from common.db import Base


class Obstacle(Base):
    __tablename__ = 'obstacles'

    id = Column(Integer, primary_key=True)
    flight_location_id = Column(Integer, ForeignKey('flight_locations.id'))
    flight_location = relationship('FlightLocation', backref='obstacles')
    convection_cell_id = Column(Integer, ForeignKey('convection_cells.id'))
    convection_cell = relationship('ConvectionCell', backref='obstacles')
    how_likely = Column(Float)
    
    def __init__(self, flight_location, convection_cell, how_likely):
        self.flight_location = flight_location
        self.convection_cell = convection_cell
        self.how_likely = how_likely

    def __repr__(self):
        return 'Obstacle({fl}, {cc}, {hl})'.format(
            fl=repr(self.flight_location),
            cc=repr(self.convection_cell),
            hl=self.how_likely
        )