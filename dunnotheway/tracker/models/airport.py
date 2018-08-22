from sqlalchemy import Column, Numeric, String, Integer
from tracker.models.base import Base


class Airport(Base):
    __tablename__ = 'airports'

    id = Column(Integer, primary_key=True)
    icao_code = Column(String(4), unique=True, nullable=False) # ICAO airport code / location identifier
    iata_code = Column(String(3)) # IATA airport code / location identifier
    name = Column(String, nullable=False)
    latitude = Column(Numeric, nullable=False)
    longitude = Column(Numeric, nullable=False)
    altitude = Column(Numeric)
    country = Column(String)

    def __init__(self, icao_code, name, latitude, longitude, altitude=None, iata_code=None, country='Brazil'):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.icao_code = icao_code
        self.iata_code = iata_code
        self.country = country
        
    def __repr__(self):
        return 'Airport({icao_code})'.format(icao_code=self.icao_code)

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