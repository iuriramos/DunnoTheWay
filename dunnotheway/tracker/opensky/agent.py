import json
import os
import time
from datetime import datetime

from sqlalchemy import literal

from common.db import open_database_session
from common.log import logger
from common.utils import from_datetime_to_timestamp, from_timestamp_to_datetime
from detector.agent import check_weather_conflicts
from normalizer.agent import normalize_flight_locations_into_sections
from tracker.models.bounding_box import BoundingBox, brazilian_airspace_bounding_box
from tracker.models.airline import Airline
from tracker.models.airplane import Airplane
from tracker.models.airport import Airport
from tracker.models.flight import Flight
from tracker.models.flight_location import FlightLocation
from tracker.models.flight_plan import FlightPlan
from tracker.opensky.plot import create_report
from tracker.opensky.settings import (FLIGHT_PATH_PARTITION_INTERVAL_IN_DEGREES,
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

    if not get_flight_plan_from_callsign(callsign):
        return
    address_to_flight = {}
    count_iterations = 0
    with open_database_session() as session:
        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS:
            # time.sleep(SLEEP_TIME_TO_GET_FLIGHT_IN_SECS)
            address = get_flight_address_from_callsign(callsign)
            update_flights(address_to_flight, [address], tracking_mode)
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
    
    with open_database_session() as session:
        departure_airport = get_airport_from_airport_code(departure_airport_code)
        destination_airport = get_airport_from_airport_code(destination_airport_code)
    
        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS:
            time.sleep(SLEEP_TIME_TO_GET_FLIGHT_IN_SECS)
            if should_update_flight_addresses(count_iterations):
                addresses = update_flight_addresses(departure_airport, destination_airport, round_trip_mode)
            update_flights(address_to_flight, addresses, tracking_mode)
            count_iterations += 1


def track_en_route_flights(tracking_mode=True):
    '''
    Keep track of ALL en-route flights
    
    building mode: record flight and their fight locations to build Air Space Graph 
    '''
    global session 

    address_to_flight = {}
    count_iterations = 0
    
    with open_database_session() as session:
        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS:
            time.sleep(SLEEP_TIME_TO_GET_FLIGHT_IN_SECS)
            if should_update_flight_addresses(count_iterations):
                addresses = get_addresses_within_brazilian_airspace()
            update_flights(address_to_flight, addresses, tracking_mode)
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
    bbox = Airport.bounding_box_related_to_airports(departure_airport, destination_airport)
    addresses = get_addresses_from_callsigns_within_bounding_box(callsigns, bbox)    
    logger.debug('Flight addresses found from {0!r} to {1!r}: {2}'.format(
        departure_airport, destination_airport, addresses))
    return addresses

def get_addresses_within_brazilian_airspace():
    bbox = brazilian_airspace_bounding_box()
    callsigns = get_all_callsigns()
    addresses = get_addresses_from_callsigns_within_bounding_box(callsigns, bbox)
    return addresses

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
    
def update_flights(address_to_flight, addresses, tracking_mode):
    '''Update address to flight mapping, which maps identifiers to flight objects and keeps track of current state-vector information'''
    update_finished_flights(address_to_flight, addresses, tracking_mode)
    update_current_flights(address_to_flight, addresses, tracking_mode)

def update_finished_flights(address_to_flight, addresses, tracking_mode):
    '''Update finished flights in address to flight mappig'''
    old_addresses = address_to_flight.keys() - addresses
    logger.info('Update finished flights (addresses): {0}'.format(old_addresses))

    def has_enough_flight_locations(flight):
        return len(flight.flight_locations) >= MIN_NUMBER_TO_SAVE_FLIGHT_LOCATIONS

    for address in old_addresses:
        flight = address_to_flight[address]
        normalize_flight_locations(flight, tracking_mode)
        if has_enough_flight_locations(flight):
            save_flight(flight) 
            # create_report(flight) 
        del address_to_flight[address]

def save_flight(flight):
    '''Save flight information in database (flight locations included)'''
    logger.info('Save flight {0!r}'.format(flight))
    session.add(flight)
    session.commit()

def update_current_flights(address_to_flight, addresses, tracking_mode):
    '''Update address to flight mapping with current values of addresses'''
    logger.info('Update current flights: {0}'.format(addresses))

    for state in get_states_from_addresses(addresses):
        address = state.address
        if address not in address_to_flight:
            new_flight = get_flight_from_state(state, tracking_mode)
            address_to_flight[address] = new_flight
        flight = address_to_flight[address]
        flight.flight_locations.append(get_flight_location_from_state(state, flight))
        # tracking conflicts being handled HERE
        if tracking_mode:
            check_weather_conflicts(session, flight)

def get_flight_from_state(state, tracking_mode):
    '''Return flight object from state-vector.'''
    flight_plan = get_flight_plan_from_state(state)
    airplane = get_airplane_from_state(state)
    longitude_based = Airport.should_be_longitude_based(
        flight_plan.departure_airport, flight_plan.destination_airport)
    
    if not tracking_mode:
        flight = Flight (
            airplane=airplane,
            flight_plan=flight_plan,
            partition_interval=FLIGHT_PATH_PARTITION_INTERVAL_IN_DEGREES,
            longitude_based=longitude_based
        )
    else:
        flight = Flight (
            airplane=airplane,
            flight_plan=flight_plan
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

def normalize_flight_locations(flight, tracking_mode):
    '''Normalize flight locations information.'''
    logger.info('Normalize flight locations of flight {0!r}'.format(flight))
    filter_duplicated_flight_locations(flight)
    if not tracking_mode:
        flight.flight_locations = (FlightLocation.
            normalize_flight_locations(flight.flight_locations))

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
