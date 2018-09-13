import math
from sqlalchemy import Column, Numeric, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from common.db import Base
from common.log import logger
from common.utils import from_datetime_to_timestamp, from_timestamp_to_datetime
from tracker.models.airport import Airport



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
            flight=repr(self.flight))

    @staticmethod
    def normalized_flight_locations_related_to_flight_plan(flight_plan):
        '''Return flight locations of flight plan'''
        
        def _normalized_flights_related_to_flight_plan(flight_plan):
            flights = flight_plan.flights
            return [flight for flight in flights if flight.partition is not None] 

        flight_locations = []
        for flight in _normalized_flights_related_to_flight_plan(flight_plan): 
            flight_locations += flight.flight_locations 
        return flight_locations

    @staticmethod
    def normalize_flight_locations(flight_locations):
        '''Filter flight locations for specific section points'''
        if not flight_locations:
            return flight_locations
        flight_locations.sort(key=lambda fl: fl.timestamp)

        fl = flight_locations[0]
        flight, flight_plan = fl.flight, fl.flight.flight_plan

        section_points = Airport._section_points_related_to_airports(
            flight_plan.departure_airport, flight_plan.destination_airport, 
            flight.partition_interval)
        return FlightLocation._find_normalized_flight_locations_from_section_points(
            flight_locations, section_points)

    @staticmethod
    def _find_normalized_flight_locations_from_section_points(flight_locations, section_points):
        normalized_flight_locations = []
        fl = flight_locations[0]
        flight = fl.flight

        longitude_based = flight.longitude_based
        follow_ascending_order = section_points[-1] > section_points[0] 
        section_points_iterator = iter(section_points)
        mid_point = next(section_points_iterator)

        for prev_location, curr_location in zip(flight_locations, flight_locations[1:]):
            try:
                while FlightLocation._check_mid_point_before_location(
                    mid_point, prev_location, longitude_based, follow_ascending_order): 
                    mid_point = next(section_points_iterator)
            except StopIteration:
                logger.error('Invalid set of flight locations {0!r} and {1!r} of flight {2!r}'.
                            format(prev_location, curr_location, flight))
                break # leave the outer for loop
        
            if FlightLocation._check_mid_point_within_flight_locations(
                mid_point, prev_location, curr_location, longitude_based):
                normalized_flight_location = FlightLocation._normalize_flight_location(
                    mid_point, prev_location, curr_location, longitude_based)
                normalized_flight_locations.append(normalized_flight_location)
        
        logger.debug('Reduce {0} flight locations to {1} normalized flight locations'.
                    format(len(flight_locations), len(normalized_flight_locations)))
        return normalized_flight_locations

    @staticmethod
    def _check_mid_point_before_location(
        mid_point, location, longitude_based, follow_ascending_order):
        '''Check if mid point comes before location.'''
        if longitude_based:
            base_point = float(location.longitude)
        else: # latitude based
            base_point = float(location.latitude)
        logger.debug('Check if mid_point {0} before location {1} following {2} order'.format(mid_point, base_point, ('decreasing', 'increasing')[follow_ascending_order]))
        return mid_point < base_point if follow_ascending_order else mid_point > base_point

    @staticmethod
    def _check_mid_point_within_flight_locations(
        mid_point, prev_location, curr_location, longitude_based):
        '''Check if mid point is within two flight locations (`prev_location` and `curr_location`)
        comparing either to the longitude or to the latitude of points.'''
        if longitude_based:
            start_interval, end_interval = (
                float(prev_location.longitude), float(curr_location.longitude))
        else: # latitude based
            start_interval, end_interval = (
                float(prev_location.latitude), float(curr_location.latitude))
       
        logger.debug('Check if mid_point {0} within interval [{1}, {2}]'.
                    format(mid_point, start_interval, end_interval))
        return (start_interval <= mid_point < end_interval or 
                end_interval <= mid_point < start_interval)

    @staticmethod
    def _normalize_flight_location(
        mid_point, prev_location, curr_location, longitude_based):
        '''Return normalized flight location within two flight locations (`prev_location` and `curr_location`)
        comparing either to the longitude or to the latitude of points.'''
        
        def find_mid_value(alpha, start, end):
            return start + alpha * (end-start)
        
        if longitude_based:
            longitude = mid_point
            start_interval, end_interval = float(prev_location.longitude), float(curr_location.longitude)
            alpha = (mid_point-start_interval)/(end_interval-start_interval) # DivisionByZeroError not possible 
            latitude = find_mid_value(alpha, float(prev_location.latitude), float(curr_location.latitude))
        else: # latitude based
            latitude = mid_point
            start_interval, end_interval = float(prev_location.latitude), float(curr_location.latitude)
            alpha = (mid_point-start_interval)/(end_interval-start_interval) # DivisionByZeroError not possible 
            longitude = find_mid_value(alpha, float(prev_location.longitude), float(curr_location.longitude))
        
        # altitude, speed and timestamp operations
        altitude = find_mid_value(alpha, float(prev_location.altitude), float(curr_location.altitude))
        speed = find_mid_value(alpha, float(prev_location.speed), float(curr_location.speed))
        timestamp = from_timestamp_to_datetime( # as datetime object
            find_mid_value(alpha, 
                from_datetime_to_timestamp(prev_location.timestamp), 
                from_datetime_to_timestamp(curr_location.timestamp)
            )
        )   

        return FlightLocation(timestamp, longitude, latitude, speed, altitude, flight=prev_location.flight)