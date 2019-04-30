from sqlalchemy import Column, Numeric, String, Integer
from common.db import Base
from flight.models.bounding_box import BoundingBox
from flight.models.flight_plan import FlightPlan
from flight.models.flight_location import FlightLocation


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

    def __hash__(self):
        return hash(self.icao_code)

    def __eq__(self, other):
        return self.icao_code == other.icao_code

    @staticmethod
    def callsigns_from_airports(session, departure_airport, destination_airport):
        '''Return callsigns of flights flying from departure airport to destination airport'''
        flight_plans = FlightPlan.flight_plans_from_airports(
            session, departure_airport, destination_airport)
        return {flight_plan.callsign for flight_plan in flight_plans}

    @staticmethod
    def airport_from_icao_code(session, icao_code):
        '''Return airport from airport code'''
        return session.query(Airport).filter(Airport.icao_code == icao_code).first()
        
    @staticmethod
    def should_be_longitude_based(departure_airport, destination_airport):
        '''Return if flight trajectory should be split by longitude or latitude.'''
        longitude_distance = abs(destination_airport.longitude - departure_airport.longitude)
        latitude_distance = abs(destination_airport.latitude - departure_airport.latitude)
        return longitude_distance >= latitude_distance

    @staticmethod
    def _section_points_related_to_airports(
        departure_airport, destination_airport, partition_interval):
        '''Return section points related to flight trajectory'''

        def split_interval_in_section_partitions(
            start_interval, end_interval, partition_interval):
            points = []
            curr_interval = start_interval
            while curr_interval <= end_interval:
                points.append(curr_interval)
                curr_interval = round(curr_interval + partition_interval, 3)
            return points
        
        longitude_based = Airport.should_be_longitude_based(
            departure_airport, destination_airport)

        if longitude_based:
            start_interval, end_interval = sorted([
                float(departure_airport.longitude), float(destination_airport.longitude)])
        else:
            start_interval, end_interval = sorted([
                float(departure_airport.latitude), float(destination_airport.latitude)])

        follow_ascending_order = Airport.follow_ascending_order(
            departure_airport, destination_airport)
        partitions = split_interval_in_section_partitions(
            start_interval, end_interval, partition_interval)
        return partitions if follow_ascending_order else partitions[::-1]

    @staticmethod
    def follow_ascending_order(departure_airport, destination_airport):
        longitude_based = Airport.should_be_longitude_based(
            departure_airport, destination_airport)

        return (float(departure_airport.longitude) < float(destination_airport.longitude) 
                if longitude_based else 
                float(departure_airport.latitude) < float(destination_airport.latitude))
        