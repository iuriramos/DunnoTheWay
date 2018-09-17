from sqlalchemy import literal, Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from common.db import Base


class Airplane(Base):
    __tablename__ = 'airplanes'

    id = Column(Integer, primary_key=True)
    icao_code = Column(String(6), unique=True, nullable=False) # ICAO 24-bit identifier
    airline_id = Column(Integer, ForeignKey('airlines.id'))
    airline = relationship('Airline', backref='airplanes')
    manufacturer = Column(String)
    model = Column(String)

    def __init__(self, icao_code, airline, manufacturer=None, model=None):
        self.icao_code = icao_code
        self.airline = airline
        self.manufacturer = manufacturer
        self.model = model

    def __repr__(self):
        return 'Airplane({icao_code}, {airline})'.format(
            icao_code=self.icao_code,
            airline=self.airline)

    @staticmethod
    def exists_airplane(session, icao_code):
        q = session.query(Airplane).filter(Airplane.icao_code == icao_code)
        return session.query(literal(True)).filter(q.exists()).scalar()

    @staticmethod
    def airplane_from_icao_code(session, icao_code):
        return session.query(Airplane).filter(Airplane.icao_code == icao_code).first()
        
        