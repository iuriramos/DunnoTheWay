from sqlalchemy import Column, Numeric, String, Integer
from tracker.models.base import Base


class Airport(Base):
    __tablename__ = 'airports'

    id = Column(Integer, primary_key=True)
    iata_code = Column(String(3), unique=True, nullable=False) # IATA airport code / location identifier
    icao_code = Column(String(4), unique=True, nullable=False) # ICAO airport code / location identifier
    name = Column(String, nullable=False)
    latitude = Column(Numeric, nullable=False)
    longitude = Column(Numeric, nullable=False)
    altitude = Column(Numeric, nullable=False)
    country = Column(String)

    def __init__(self, iata_code, icao_code, name, latitude, longitude, altitude, country):
        self.iata_code = iata_code
        self.icao_code = icao_code
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.country = country
        
    def __repr__(self):
        return 'Airport({iata_code})'.format(iata_code=self.iata_code)

    @staticmethod
    def get_bounding_box_from_airports(departure_airport, destination_airport):
        '''Return bounding box from departure airport to destination airport 
        (min latitude, max latitude, min longitude, max longitude)'''
        bbox = (
            float(min(departure_airport.latitude, destination_airport.latitude)), 
            float(max(departure_airport.latitude, destination_airport.latitude)),
            float(min(departure_airport.longitude, destination_airport.longitude)), 
            float(max(departure_airport.longitude, destination_airport.longitude))
        )
        # logger.debug('Select bounding box {0} from departure airport {1!r} to destination airport {2!r}'.format(
        #     bbox, departure_airport, destination_airport))
        return bbox