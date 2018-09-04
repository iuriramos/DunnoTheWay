import json
import os
import time
from datetime import datetime

from sqlalchemy import literal

from tracker.common.plot import create_report
from tracker.common.settings import (CRUISING_VERTICAL_RATE_IN_MS,
                                     FLIGHT_PATH_PARTITION_INTERVAL_IN_DEGREES,
                                     ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS,
                                     MAX_LATITUDE_BRAZILIAN_AIRSPACE,
                                     MAX_LONGITUDE_BRAZILIAN_AIRSPACE,
                                     MIN_LATITUDE_BRAZILIAN_AIRSPACE,
                                     MIN_LONGITUDE_BRAZILIAN_AIRSPACE,
                                     MIN_NUMBER_TO_SAVE_FLIGHT_LOCATIONS,
                                     SLEEP_TIME_TO_GET_FLIGHT_IN_SECS,
                                     SLEEP_TIME_TO_SEARCH_NEW_FLIGHTS_IN_SECS,
                                     logger, open_database_session)
from tracker.models.airline import Airline
from tracker.models.airplane import Airplane
from tracker.models.airport import Airport
from tracker.models.flight import Flight
from tracker.models.flight_location import FlightLocation
from tracker.models.flight_plan import FlightPlan

from .api import (get_flight_address_from_callsign, get_states,
                  get_states_from_addresses, get_states_from_bounding_box)
from .state_vector import StateVector

# global variables
session = None


def track_en_route_flight_by_callsign(callsign):
    '''Keep track of flight information from its callsign'''
    global session

    if not get_flight_plan_from_callsign(callsign):
        return
    address_to_flight = {}
    count_iterations = 0
    with open_database_session() as session:
        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS:
            # time.sleep(SLEEP_TIME_TO_GET_FLIGHT_IN_SECS)
            address = get_flight_address_from_callsign(callsign)
            update_flights(address_to_flight, addresses=[address])
            count_iterations += 1


def track_en_route_flights_by_airports(departure_airport_code, destination_airport_code, round_trip_mode=False):
    '''Keep track of current flights information from departure airport to destination airport'''
    global session 

    logger.info('Track flight addresses from {0} to {1} in {2} mode'.format(
        departure_airport_code, destination_airport_code, 'round trip' if round_trip_mode else 'one way'))
    
    address_to_flight = {}
    count_iterations = 0
    
    with open_database_session() as session:
        departure_airport = get_airport_from_airport_code(departure_airport_code)
        destination_airport = get_airport_from_airport_code(destination_airport_code)
    
        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS:
            time.sleep(SLEEP_TIME_TO_GET_FLIGHT_IN_SECS)
            if should_update_flight_addresses(count_iterations):
                addresses = update_flight_addresses(departure_airport, destination_airport, round_trip_mode)
            update_flights(address_to_flight, addresses)
            count_iterations += 1


def track_en_route_flights():
    '''Keep track of ALL en-route flights'''
    global session 

    address_to_flight = {}
    count_iterations = 0
    
    with open_database_session() as session:
        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS:
            time.sleep(SLEEP_TIME_TO_GET_FLIGHT_IN_SECS)
            if should_update_flight_addresses(count_iterations):
                addresses = get_addresses_within_brazilian_airspace()
            update_flights(address_to_flight, addresses)
            count_iterations += 1


def should_update_flight_addresses(count_iterations):
    times = SLEEP_TIME_TO_SEARCH_NEW_FLIGHTS_IN_SECS//SLEEP_TIME_TO_GET_FLIGHT_IN_SECS
    return count_iterations % times == 0

def update_flight_addresses(departure_airport, destination_airport, round_trip_mode):
    '''Update pool of flight addresses from time to time'''
    logger.info('Update flight addresses from {0!r} to {1!r} in {2} mode'.format(
        departure_airport, destination_airport, 'round trip' if round_trip_mode else 'one way'))

    addresses = get_flight_addresses_from_airports(departure_airport, destination_airport)
    if round_trip_mode:
        addresses += get_flight_addresses_from_airports(destination_airport, departure_airport)
    return addresses

def get_flight_addresses_from_airports(departure_airport, destination_airport):
    '''Return flight ICAO24 addresses from departure airport to destination airport'''
    callsigns = get_callsigns_from_airports(departure_airport, destination_airport)
    bbox = Airport.get_bounding_box_from_airports(departure_airport, destination_airport)
    addresses = get_addresses_from_callsigns_within_bounding_box(callsigns, bbox)    
    logger.debug('Flight addresses found from {0!r} to {1!r}: {2}'.format(
        departure_airport, destination_airport, addresses))
    return addresses

def get_addresses_within_brazilian_airspace():
    bbox = get_brazilian_airspace_bounding_box()
    callsigns = get_all_callsigns()
    addresses = get_addresses_from_callsigns_within_bounding_box(callsigns, bbox)
    return addresses

def get_brazilian_airspace_bounding_box():
    bbox = (
        MIN_LATITUDE_BRAZILIAN_AIRSPACE,
        MAX_LATITUDE_BRAZILIAN_AIRSPACE,
        MIN_LONGITUDE_BRAZILIAN_AIRSPACE,
        MAX_LONGITUDE_BRAZILIAN_AIRSPACE
    )
    return bbox

def get_all_callsigns():
    flight_plans = session.query(FlightPlan).all()
    return get_callsigns_from_flight_plans(flight_plans)
        
def get_callsigns_from_airports(departure_airport, destination_airport):
    '''Return callsigns of flights flying from departure airport to destination airport'''
    flight_plans = (session.query(FlightPlan)
        .filter(FlightPlan.departure_airport == departure_airport, FlightPlan.destination_airport == destination_airport)
        .all()) 
    return get_callsigns_from_flight_plans(flight_plans)
    
def get_callsigns_from_flight_plans(flight_plans):
    return {fp.callsign for fp in flight_plans}

def get_addresses_from_callsigns_within_bounding_box(callsigns, bbox):
    addresses = []
    states = get_states_from_bounding_box(bbox)
    for state in states:
        if state.callsign in callsigns:
            addresses.append(state.address)
    return addresses 

def get_flight_plan_from_callsign(callsign):
    '''Return FlightPlan associated with callsign'''
    flight_plan = session.query(Airline).filter(FlightPlan.callsign == callsign).first()
    return flight_plan

def get_airport_from_airport_code(airport_code):
    '''Return airport from airport code'''
    airport = session.query(Airport).filter(Airport.icao_code == airport_code).first()
    return airport
    
def update_flights(address_to_flight, addresses):
    '''Update address to flight mapping, which maps identifiers to flight objects and keeps track of current state-vector information'''
    update_finished_flights(address_to_flight, addresses)
    update_current_flights(address_to_flight, addresses)

def update_finished_flights(address_to_flight, addresses):
    '''Update finished flights in address to flight mappig'''
    old_addresses = address_to_flight.keys() - addresses
    logger.info('Update finished flights (addresses): {0}'.format(old_addresses))

    def has_enough_flight_locations(flight):
        return len(flight.flight_locations) >= MIN_NUMBER_TO_SAVE_FLIGHT_LOCATIONS

    for address in old_addresses:
        flight = address_to_flight[address]
        normalize_flight_locations(flight)
        if has_enough_flight_locations(flight):
            save_flight(flight) # save flight locations as well
            create_report(flight) # create report if flag is set to True
        del address_to_flight[address]

def save_flight(flight):
    '''Save flight information in database'''
    logger.info('Save flight {0!r}'.format(flight))
    session.add(flight)
    session.commit()

def update_current_flights(address_to_flight, addresses):
    '''Update address to flight mapping with current values of addresses'''
    logger.info('Update current flights: {0}'.format(addresses))

    for state in get_states_from_addresses(addresses):
        address = state.address
        if address not in address_to_flight:
            new_flight = get_flight_from_state(state)
            address_to_flight[address] = new_flight
        flight = address_to_flight[address]
        flight.flight_locations.append(get_flight_location_from_state(state, flight))

def get_flight_from_state(state):
    '''Return flight object from state-vector.'''
    flight_plan = get_flight_plan_from_state(state)
    airplane = get_airplane_from_state(state)
    longitude_based = should_partition_by_longitude(flight_plan) 
    
    flight = Flight (
        airplane=airplane,
        flight_plan=flight_plan,
        partition_interval=FLIGHT_PATH_PARTITION_INTERVAL_IN_DEGREES,
        longitude_based=longitude_based
    )

    logger.debug('Create new flight object: {0!r}'.format(flight))
    return flight

def get_flight_location_from_state(state, flight):
    '''Return flight location from state-vector and flight object'''
    flight_location = FlightLocation(
        timestamp=from_timestamp_to_datetime(state.time_position), # timestamp as datetime object
        longitude=state.longitude,
        latitude=state.latitude,
        altitude=state.baro_altitude, # barometric altitude
        speed=state.velocity,
        flight=flight
    )        
    logger.debug('Create new flight location object: {0!r}'.format(flight_location))
    return flight_location

def get_airplane_from_state(state):
    '''Return airplane object from state-vector if the airplane is in database.
    Otherwise, create and return new airplane object.'''
    icao_code = state.address
    q = session.query(Airplane).filter(Airplane.icao_code == icao_code)
    if session.query(literal(True)).filter(q.exists()).scalar():
        airplane = q.first()
    else: # create new airplane object
        airplane = Airplane(
            icao_code=icao_code,
            airline=get_airline_from_state(state)
        )
    return airplane

def should_partition_by_longitude(flight_plan):
    '''Return if flight trajectory should be split by longitude or latitude.'''
    departure_airport = flight_plan.departure_airport
    destination_airport = flight_plan.destination_airport
    longitude_distance = abs(destination_airport.longitude - departure_airport.longitude)
    latitude_distance = abs(destination_airport.latitude - departure_airport.latitude)
    return longitude_distance >= latitude_distance

def get_airline_from_state(state):
    '''Return airline associated with state-vector'''
    callsign = state.callsign
    return get_airline_from_callsign(callsign)

def get_airline_from_callsign(callsign):
    '''Return Airline associated with callsign'''
    icao_code, _ = split_callsign(callsign)
    airline = session.query(Airline).filter(Airline.icao_code == icao_code).first()
    return airline

def split_callsign(callsign):
    '''Split callsign in meaninful chunks (airplane designator and flight number)'''
    airplane_designator, flight_number = callsign[:3], callsign[3:]
    return airplane_designator, flight_number

def get_flight_plan_from_state(state):
    '''Return flight plan information from state-vector'''
    flight_plan = session.query(FlightPlan).filter(FlightPlan.callsign == state.callsign).first()
    return flight_plan

def normalize_flight_locations(flight):
    '''Normalize flight locations information.'''
    logger.info('Normalize flight locations of flight {0!r}'.format(flight))
    filter_duplicated_flight_locations(flight)
    # filter_cruising_flight_locations(flight)
    fixed_points = get_flight_trajectory_fixed_points(flight)
    filter_fixed_points_flight_locations(flight, fixed_points)

def filter_duplicated_flight_locations(flight):
    '''Remove duplicated flight locations.'''
    flight_locations = []

    def check_equal_flight_locations(prev, curr):
        return prev and (prev.longitude, prev.latitude) == (curr.longitude, curr.latitude)

    prev = None
    for curr in flight.flight_locations:
        if not check_equal_flight_locations(prev, curr):
            flight_locations.append(curr)
        prev = curr
    
    logger.debug('Reduce {0} duplicated flight locations to {1} unique ones'.format(
        len(flight.flight_locations), len(flight_locations)))
    # update flight locations of flight
    flight.flight_locations = flight_locations

def filter_cruising_flight_locations(flight):
    '''Filter only flight locations in cruising speed.'''
    flight_locations = []

    # def check_cruising_flight_location(prev, curr): # VERY STRICT
    #     return prev and prev.altitude == curr.altitude

    def check_cruising_flight_location(prev, curr):
        if not prev:
            return False
        vertical_rate = (
            (float(curr.altitude) - float(prev.altitude))
            / (from_datetime_to_timestamp(curr.timestamp) - from_datetime_to_timestamp(prev.timestamp)))
        return abs(vertical_rate) <= CRUISING_VERTICAL_RATE_IN_MS

    prev = None
    for curr in flight.flight_locations:
        if check_cruising_flight_location(prev, curr):
            flight_locations.append(curr)
        prev = curr

    logger.debug('Reduce {0} flight locations to {1} crusing flight locations'.format(
        len(flight.flight_locations), len(flight_locations)))
    # update flight locations of flight
    flight.flight_locations = flight_locations

def filter_fixed_points_flight_locations(flight, fixed_points):
    '''Filter flight locations for specific fixed points'''
    flight_locations = flight.flight_locations
    if len(flight_locations) < 2:
        return []
    
    fixed_flight_locations = []
    longitude_based = flight.longitude_based
    follow_increasing_order = fixed_points[-1] > fixed_points[0] 
    fixed_points_iterator = iter(fixed_points)
    mid_point = next(fixed_points_iterator)

    for prev_location, curr_location in zip(flight_locations, flight_locations[1:]):
        try:
            while check_mid_point_before_location(mid_point, prev_location, longitude_based, follow_increasing_order): 
                mid_point = next(fixed_points_iterator) # might raise StopIteration Exception
        except StopIteration:
            logger.error('Invalid set of flight locations {0!r} and {1!r} of flight {2!r}'.format(prev_location, curr_location, flight))
            break # leave for outer loop
     
        if check_mid_point_within_flight_locations(mid_point, prev_location, curr_location, longitude_based):
            fixed_flight_location = get_fixed_flight_location(mid_point, prev_location, curr_location, longitude_based)
            fixed_flight_locations.append(fixed_flight_location)
    
    logger.debug('Reduce {0} flight locations to {1} fixed flight locations'.format(
        len(flight_locations), len(fixed_flight_locations)))
    flight.flight_locations = fixed_flight_locations

def check_mid_point_before_location(mid_point, location, longitude_based, follow_increasing_order):
    '''Check if mid point comes before location.'''
    if longitude_based:
        base_point = float(location.longitude)
    else: # latitude based
        base_point = float(location.latitude)
    # logger.debug('Check if mid_point {0} before location {1} following {2} order'.format(mid_point, base_point, ('decreasing', 'increasing')[follow_increasing_order]))
    return mid_point < base_point if follow_increasing_order else mid_point > base_point

def check_mid_point_within_flight_locations(mid_point, prev_location, curr_location, longitude_based):
    '''Check if mid point is within two flight locations (`prev_location` and `curr_location`)
    comparing either to the longitude or to the latitude of points.'''
    if longitude_based:
        start_interval, end_interval = (
            float(prev_location.longitude), float(curr_location.longitude))
    else: # latitude based
        start_interval, end_interval = (
            float(prev_location.latitude), float(curr_location.latitude))
    # logger.debug('Check if mid_point {0} within interval [{1}, {2}]'.format(mid_point, start_interval, end_interval))
    return start_interval <= mid_point < end_interval or end_interval <= mid_point < start_interval

def get_fixed_flight_location(mid_point, prev_location, curr_location, longitude_based):
    '''Return fixed flight location within two flight locations (`prev_location` and `curr_location`)
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
    timestamp = from_timestamp_to_datetime(
        find_mid_value(alpha, 
            from_datetime_to_timestamp(prev_location.timestamp), 
            from_datetime_to_timestamp(curr_location.timestamp)
        )
    )     
    return FlightLocation(
        timestamp=timestamp, # as datetime object
        longitude=longitude,
        latitude=latitude,
        speed=speed,
        altitude=altitude,
        flight=prev_location.flight
    )

def from_datetime_to_timestamp(dt):
    '''Convert datetime object in timestamp'''
    return time.mktime(dt.timetuple())

def from_timestamp_to_datetime(ts):
    '''Convert timestamp in datetime object'''
    return datetime.fromtimestamp(ts)

def get_flight_trajectory_fixed_points(flight):
    '''Return fixed points related to flight trajectory'''

    def split_interval_in_fixed_partitions(start_interval, end_interval, partition_interval):
        points = []
        curr_interval = start_interval
        while curr_interval <= end_interval:
            points.append(curr_interval)
            curr_interval = round(curr_interval + partition_interval, 3)
        return points

    if flight.longitude_based:
        start_interval, end_interval = (
            float(flight.flight_plan.departure_airport.longitude), 
            float(flight.flight_plan.destination_airport.longitude))
    else:
        start_interval, end_interval = (
            float(flight.flight_plan.departure_airport.latitude), 
            float(flight.flight_plan.destination_airport.latitude))
    
    follow_increasing_order = start_interval < end_interval
    partition_interval = float(flight.partition_interval)
    start_interval, end_interval = sorted([start_interval, end_interval])
    partitions = split_interval_in_fixed_partitions(start_interval, end_interval, partition_interval)
    return partitions if follow_increasing_order else partitions[::-1]

