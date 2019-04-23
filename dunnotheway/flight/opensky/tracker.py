import json
import os
import time
from datetime import datetime

from analyser.flight_location_normalizer import normalize_flight_locations
from analyser.obstacle_detector import ObstacleDetector
from common.db import open_database_session
from common.log import logger
from common.utils import from_datetime_to_timestamp, from_timestamp_to_datetime
from flight.models.airline import Airline
from flight.models.airplane import Airplane
from flight.models.airport import Airport
from flight.models.bounding_box import (BoundingBox,
                                         bounding_box_related_to_airports,
                                         brazilian_airspace_bounding_box)
from flight.models.flight import Flight
from flight.models.flight_location import FlightLocation
from flight.models.flight_plan import FlightPlan
from flight.opensky.plot import create_report
from flight.opensky.settings import (FLIGHT_PATH_PARTITION_INTERVAL_IN_DEGREES,
                                      ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS,
                                      MIN_NUMBER_TO_SAVE_FLIGHT_LOCATIONS,
                                      SLEEP_TIME_TO_GET_FLIGHT_IN_SECS,
                                      SLEEP_TIME_TO_SEARCH_NEW_FLIGHTS_IN_SECS)

from .api import (get_flight_address_from_callsign, get_states,
                  get_states_from_addresses, get_states_from_bounding_box)
from .state_vector import StateVector

# global variables
session = None


def track_en_route_flight_by_callsign(callsign, tracking_mode=True):
    '''Keep track of flight information from its callsign'''
    global session
    address_to_flight = {}
    count_iterations = 0
    detector = ObstacleDetector()

    with open_database_session() as session:
        if not FlightPlan.flight_plan_from_callsign(session, callsign):
            logger.error('Callsign does not exist.')
            return

        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS:
            # time.sleep(SLEEP_TIME_TO_GET_FLIGHT_IN_SECS)
            address = get_flight_address_from_callsign(callsign)
            update_flights(detector, address_to_flight, [address], tracking_mode)
            count_iterations += 1


def track_en_route_flights_by_airports(
    departure_airport_code, destination_airport_code, 
    round_trip_mode=False, tracking_mode=True):
    '''
    Keep track of current flights information from departure airport to destination airport
    
    round trip mode: interchanging departure and destination airports as well
    building mode: record flight and their fight locations to build Air Space Graph 
    '''
    global session 

    logger.info('Track flight addresses from {0} to {1} in {2} mode'.format(
        departure_airport_code, destination_airport_code, 'round trip' if round_trip_mode else 'one way'))
    
    address_to_flight = {}
    count_iterations = 0
    detector = ObstacleDetector()
    
    with open_database_session() as session:
        departure_airport = Airport.airport_from_icao_code(session, departure_airport_code)
        destination_airport = Airport.airport_from_icao_code(session, destination_airport_code)
        
        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS:
            time.sleep(SLEEP_TIME_TO_GET_FLIGHT_IN_SECS)
            if should_update_flight_addresses(count_iterations):
                addresses = update_flight_addresses(departure_airport, destination_airport, round_trip_mode)
            update_flights(detector, address_to_flight, addresses, tracking_mode)
            count_iterations += 1


def track_en_route_flights(tracking_mode=True, tracking_airports_list=None):
    '''
    Keep track of ALL en-route flights
    
    building mode: record flight and their fight locations to build Air Space Graph 
    '''
    global session 

    address_to_flight = {}
    count_iterations = 0
    detector = ObstacleDetector()

    
    with open_database_session() as session:
        tracking_list = build_tracking_list(tracking_airports_list)
        
        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS:
            time.sleep(SLEEP_TIME_TO_GET_FLIGHT_IN_SECS)
            if should_update_flight_addresses(count_iterations):
                addresses = get_addresses_within_brazilian_airspace()
            update_flights(
                detector, address_to_flight, addresses, tracking_mode, tracking_list)
            count_iterations += 1

def build_tracking_list(tracking_airports_list):
    tracking_airports_list = tracking_airports_list or []

    tracking_list = []
    for departure_airport_code, destination_airport_code in tracking_airports_list:
        departure_airport = Airport.airport_from_icao_code(session, departure_airport_code)
        destination_airport = Airport.airport_from_icao_code(session, destination_airport_code)
        tracking_list.append((departure_airport, destination_airport))
    return tracking_list

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
    bbox = bounding_box_related_to_airports(departure_airport, destination_airport)
    addresses = get_addresses_from_callsigns_inside_bounding_box(callsigns, bbox)    
    logger.debug('Flight addresses found from {0!r} to {1!r}: {2}'.format(
        departure_airport, destination_airport, addresses))
    return addresses

def get_addresses_within_brazilian_airspace():
    bbox = brazilian_airspace_bounding_box()
    callsigns = get_all_callsigns()
    addresses = get_addresses_from_callsigns_inside_bounding_box(callsigns, bbox)
    return addresses

def get_all_callsigns():
    flight_plans = FlightPlan.all_flight_plans(session)
    return get_callsigns_from_flight_plans(flight_plans)
        
def get_callsigns_from_airports(departure_airport, destination_airport):
    '''Return callsigns of flights flying from departure airport to destination airport'''
    flight_plans = FlightPlan.flight_plans_from_airports(
        session, departure_airport, destination_airport)
    return get_callsigns_from_flight_plans(flight_plans)
    
def get_callsigns_from_flight_plans(flight_plans):
    return {fp.callsign for fp in flight_plans}

def get_addresses_from_callsigns_inside_bounding_box(callsigns, bbox):
    addresses = []
    states = get_states_from_bounding_box(bbox)
    for state in states:
        if state.callsign in callsigns:
            addresses.append(state.address)
    return addresses 

def update_flights(
    detector, address_to_flight, addresses, tracking_mode, tracking_list=None):
    '''Update address to flight mapping, which maps identifiers to flight objects and keeps track of current state-vector information'''
    update_finished_flights(address_to_flight, addresses)
    update_current_flights(
        detector, address_to_flight, addresses, tracking_mode, tracking_list)

def update_finished_flights(address_to_flight, addresses):
    '''Update finished flights in address to flight mappig'''
    old_addresses = address_to_flight.keys() - addresses
    logger.info('Update finished flights (addresses): {0}'.format(old_addresses))

    def has_enough_flight_locations(flight):
        return len(flight.flight_locations) >= MIN_NUMBER_TO_SAVE_FLIGHT_LOCATIONS

    for address in old_addresses:
        flight = address_to_flight[address]
        remove_duplicated_flight_locations(flight)
        # save objects in database
        if has_enough_flight_locations(flight):
            save_flight(flight) 
        del address_to_flight[address]

def save_flight(flight):
    '''Save flight information in database (flight locations included)'''
    logger.info('Save flight {0!r}'.format(flight))
    session.add(flight)
    session.commit()

def update_current_flights(
    detector, address_to_flight, addresses, tracking_mode, tracking_list):
    '''Update address to flight mapping with current values of addresses'''
    logger.info('Update current flights: {0}'.format(addresses))

    for state in get_states_from_addresses(addresses):
        address = state.address
        if address not in address_to_flight:
            new_flight = get_flight_from_state(state)
            address_to_flight[address] = new_flight
        flight = address_to_flight[address]
        flight_plan = flight.flight_plan
        _ = get_flight_location_from_state_and_flight(state, flight) # append it automatically
        
        # detection of obstacles are handled here
        if ((tracking_mode or check_flight_plan_in_tracking_list(flight_plan, tracking_list)) and 
            len(flight.flight_locations) >= 2):
            # prev, curr = prev_and_curr_flight_locations_from_flight(flight) 
            prev, curr = flight.flight_locations[-2:]
            if not FlightLocation.check_equal_flight_locations(prev, curr):
                _ = (detector.
                    check_obstacles_related_to_flight_location(prev, curr))

def check_flight_plan_in_tracking_list(flight_plan, tracking_list):
    tracking_list = tracking_list or []
    
    for departure_airport, destination_airport in tracking_list:
        if (flight_plan.departure_airport == departure_airport and
            flight_plan.destination_airport == destination_airport):
            return True
    return False

def get_flight_from_state(state):
    '''Return flight object from state-vector.'''
    flight_plan = FlightPlan.flight_plan_from_callsign(session, state.callsign)
    airplane = StateVector.airplane_from_state(session, state)
    flight = Flight(
        airplane=airplane,
        flight_plan=flight_plan)
    
    logger.debug('Create new flight object: {0!r}'.format(flight))
    return flight

def get_flight_location_from_state_and_flight(state, flight):
    '''Return flight location from state-vector and flight object'''
    flight_location = FlightLocation(
        timestamp=from_timestamp_to_datetime(state.time_position), # timestamp as datetime object
        longitude=state.longitude,
        latitude=state.latitude,
        altitude=state.baro_altitude, # barometric altitude
        speed=state.velocity,
        flight=flight
    )        
    # logger.debug('Create new flight location object: {0!r}'.format(flight_location))
    return flight_location

def remove_duplicated_flight_locations(flight):
    '''Remove duplicated flight locations.'''
    flight_locations = []

    prev = None
    for curr in flight.flight_locations:
        if not FlightLocation.check_equal_flight_locations(prev, curr):
            flight_locations.append(curr)
        prev = curr
    
    logger.debug('Reduce {0} duplicated flight locations to {1} unique ones'.format(
        len(flight.flight_locations), len(flight_locations)))
    # update flight locations of flight
    flight.flight_locations = flight_locations
