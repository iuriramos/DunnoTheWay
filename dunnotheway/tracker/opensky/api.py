import os
import sys
import time 
import json
# load opensky-api
sys.path.append('/home/iuri/workspace/opensky-api/python')

from sqlalchemy import literal
from opensky_api import OpenSkyApi
from common.settings import BASE_DIR
from tracker.models.airport import Airport
from tracker.models.airline import Airline
from tracker.models.airplane import Airplane
from tracker.models.flight import Flight
from tracker.models.flight_plan import FlightPlan
from tracker.models.flight_location import FlightLocation
from tracker.models.base import Session
# import matplotlib.pyplot as plt 

# load config file
CONFIG_PATH = os.path.join(BASE_DIR, 'tracker', 'common', 'config.json')
with open(CONFIG_PATH) as f:
    config = json.load(f)

# config variables
SLEEP_TIME_GET_FLIGHT = config['DEFAULT']['SLEEP_TIME_GET_FLIGHT'] 
SLEEP_TIME_SEARCH_FLIGHT = config['DEFAULT']['SLEEP_TIME_SEARCH_FLIGHT'] 
ITERATIONS_LIMIT = config['DEFAULT']['ITERATIONS_LIMIT'] 
FLIGHT_PATH_PARTITION_INTERVAL = config['DEFAULT']['FLIGHT_PATH_PARTITION_INTERVAL'] 
SIMILAR_STATE_VECTORS_LIMIT = config['DEFAULT']['SIMILAR_STATE_VECTORS_LIMIT'] 


def get_flight_address_from_callsign(callsign):
    '''Return flight ICAO24 address from callsign'''
    for state in get_states():
        if get_state_callsign(state) == callsign:
            return get_state_address(state)
    return None

def get_flight_addresses_from_airports(departure_airport, destination_airport):
    '''Return flight ICAO24 addresses from departure airport to destination airport'''
    addresses = []
    callsigns = get_callsigns_from_airports(departure_airport, destination_airport)
    bbox = get_bounding_box_from_airports(departure_airport, destination_airport)
    # states = get_states()
    states = get_states_from_bounding_box(bbox)
    for state in states:
        if get_state_callsign(state) in callsigns:
            addresses.append(get_state_address(state))
    return addresses

def get_states():
    api = OpenSkyApi()
    return [state for state in api.get_states().states if check_valid_state(state)]

def get_states_from_bounding_box(bbox):
    api = OpenSkyApi()
    valid_states = [state for state in api.get_states(bbox=bbox).states if check_valid_state(state)]
    return valid_states

def get_states_from_addresses(addresses):
    '''Return state-vectors of flights flying from a list of addresses or a single address'''
    if not addresses: # empty list
        return []
    api = OpenSkyApi()
    valid_states = [state for state in api.get_states(icao24=addresses).states if check_valid_state(state)]
    return valid_states

def get_callsigns_from_airports(departure_airport, destination_airport):
    '''Return callsigns of flights flying from departure airport to destination airport'''
    session = Session()
    # query database for flighplans from departure airport to destination airport
    flightplans = (session.query(FlightPlan)
        .filter(FlightPlan.departure_airport == departure_airport, FlightPlan.destination_airport == destination_airport)
        .all()) 
    callsigns = {fp.callsign for fp in flightplans}
    return callsigns

def get_bounding_box_from_airports(departure_airport, destination_airport):
    '''Return bounding box from departure airport to destination airport 
    (min latitude, max latitude, min longitude, max longitude)'''
    return (
        float(min(departure_airport.latitude, destination_airport.latitude)), 
        float(max(departure_airport.latitude, destination_airport.latitude)),
        float(min(departure_airport.longitude, destination_airport.longitude)), 
        float(max(departure_airport.longitude, destination_airport.longitude))
    )

def check_valid_state(state):
    '''Check if vector-state is valid'''
    return (
        state.time_position and
        state.longitude and 
        state.latitude and 
        state.velocity and 
        state.baro_altitude
    )

def get_state_address(state):
    '''Return state-vector flight ICAO24 address'''
    return state.icao24 # flight identifier

def get_state_callsign(state):
    '''Return state-vector flight callsign'''
    return state.callsign.strip()
    

# def find_flight_from_flightplan(flightplan):
#     '''Return current flight from its flightplan'''
#     pass

# def find_flightlocations_from_flight(flight):
#     '''Return cruising flight locations of flight'''
#     pass

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
    # update flight locations of flight
    flight.flight_locations = flight_locations

def filter_cruising_flight_locations(flight):
    '''Filter only flight locations in cruising speed.'''
    flight_locations = []

    def check_cruising_flight_location(prev, curr): # TODO:check other attributes
        return prev and prev.altitude == curr.altitude

    prev = None
    for curr in flight.flight_locations:
        if check_cruising_flight_location(prev, curr):
            flight_locations.append(curr)
        prev = curr
    # update flight locations of flight
    flight.flight_locations = flight_locations

def filter_fixed_points_flight_locations(flight, fixed_points):
    '''Filter flight locations for specific fixed points'''
    fixed_flight_locations = []
    flight_locations = flight.flight_locations
    if len(flight_locations) < 2:
        return fixed_flight_locations
    longitude_based = flight.longitude_based
    fixed_points_iterator = iter(fixed_points)
    mid_point = next(fixed_points_iterator)
    for prev_location, curr_location in zip(flight_locations, flight_locations[1:]):
        while not check_mid_point_within_flight_locations(mid_point, prev_location, curr_location, longitude_based):
            mid_point = next(fixed_points_iterator)
        fixed_flight_locations.append(get_fixed_flight_location(mid_point, prev_location, curr_location, longitude_based))
    flight.flight_locations = fixed_flight_locations

def check_mid_point_within_flight_locations(mid_point, prev_location, curr_location, longitude_based):
    '''Check if mid point is in between two flight locations (`prev_location` and `curr_location`)
    comparing either to the longitude or to the latitude of points.'''
    if longitude_based:
        start_interval, end_interval = sorted([
            prev_location.longitude, curr_location.longitude])
    else: # latitude based
        start_interval, end_interval = sorted([
            prev_location.latitude, curr_location.latitude])
    return start_interval <= mid_point <= end_interval

def get_fixed_flight_location(mid_point, prev_location, curr_location, longitude_based):
    '''Return fixed flight location within two flight locations (`prev_location` and `curr_location`)
    comparing either to the longitude or to the latitude of points.'''
    
    def find_mid_value(alpha, start, end):
        return start + alpha * (end-start)
    
    if longitude_based:
        longitude = mid_point
        start_interval, end_interval = prev_location.longitude, curr_location.longitude
        alpha = (mid_point-start_interval)/(end_interval-start_interval) # TODO:DivisionByZeroError
        timestamp = find_mid_value(alpha, prev_location.timestamp, curr_location.timestamp)
        latitude = find_mid_value(alpha, prev_location.latitude, curr_location.latitude)
        speed = find_mid_value(alpha, prev_location.speed, curr_location.speed)
    else: # latitude based
        latitude = mid_point
        start_interval, end_interval = prev_location.latitude, curr_location.latitude
        timestamp = find_mid_value(alpha, prev_location.timestamp, curr_location.timestamp)
        longitude = find_mid_value(alpha, prev_location.longitude, curr_location.longitude)
        speed = find_mid_value(alpha, prev_location.speed, curr_location.speed)
    
    return FlightLocation(
        timestamp=timestamp,
        longitude=longitude,
        latitude=latitude,
        speed=speed,
        altitude=prev_location.altitude,
        flight=prev_location.flight
    )

def get_flight_trajectory_fixed_points(flight):
    '''Return fixed points related to flight trajectory'''
    partition_interval = flight.partition_interval

    def split_interval_in_fixed_partitions(start_interval, end_interval, partition_interval):
        points = []
        curr_interval = start_interval
        while curr_interval <= end_interval:
            points.append(curr_interval)
            curr_interval += partition_interval
        return points

    if flight.longitude_based:
        start_interval, end_interval = sorted([
            flight.flight_plan.departure_airport.longitude, 
            flight.flight_plan.destination_airport.longitude])
    else:
        start_interval, end_interval = sorted([
            flight.flight_plan.departure_airport.latitude, 
            flight.flight_plan.destination_airport.latitude])
    return split_interval_in_fixed_partitions(
        start_interval, end_interval, partition_interval)
    
def normalize_flight_locations(flight):
    '''Normalize flight locations information.'''
    filter_duplicated_flight_locations(flight)
    filter_cruising_flight_locations(flight)
    fixed_points = get_flight_trajectory_fixed_points(flight)
    filter_fixed_points_flight_locations(flight, fixed_points)

def save_flight(flight):
    '''Save flight information in database'''
    session = Session()
    normalize_flight_locations(flight)
    session.add(flight)
    session.commit()
    session.close()

# TODO: save figure to check assumptions in a visual way
def create_report(flight_entries): 
    '''Create report from flight entries (flight location, speed, vertical_rate)'''
    pass

def track_flight_from_callsign(callsign):
    '''Keep track of flight information from its callsign'''
    if not get_flight_plan_from_callsign(callsign):
        return
    address_to_flight = {}
    count_iterations = 0
    while count_iterations < ITERATIONS_LIMIT:
        # time.sleep(SLEEP_TIME_GET_FLIGHT)
        address = get_flight_address_from_callsign(callsign)
        update_flights(address_to_flight, addresses=[address])
        count_iterations += 1

def get_flight_plan_from_callsign(callsign):
    '''Return FlightPlan associated with callsign'''
    session = Session()
    flight_plan = session.query(Airline).filter(FlightPlan.callsign == callsign).first()
    return flight_plan

def track_flights_from_airports(departure_airport_code, destination_airport_code, round_trip_mode=False):
    '''Keep track of current flights information from departure airport to destination airport'''
    address_to_flight = {}
    count_iterations = 0
    departure_airport = get_airport_from_airport_code(departure_airport_code)
    destination_airport = get_airport_from_airport_code(destination_airport_code)
    
    def should_update_flight_addresses(count_iterations):
        times = SLEEP_TIME_SEARCH_FLIGHT//SLEEP_TIME_GET_FLIGHT
        return count_iterations % times == 0

    while count_iterations < ITERATIONS_LIMIT:
        time.sleep(SLEEP_TIME_GET_FLIGHT)
        if should_update_flight_addresses(count_iterations):
            addresses = update_flight_addresses(departure_airport, destination_airport, round_trip_mode)
        update_flights(address_to_flight, addresses)
        count_iterations += 1

def get_airport_from_airport_code(airport_code):
    '''Return airport from airport code'''
    session = Session()
    return session.query(Airport).filter(Airport.code == airport_code).first()

def update_flight_addresses(departure_airport, destination_airport, round_trip_mode):
    '''Update pool of flight addresses from time to time'''
    addresses = get_flight_addresses_from_airports(departure_airport, destination_airport)
    if round_trip_mode:
        addresses += get_flight_addresses_from_airports(destination_airport, departure_airport)
    return addresses

def update_flights(address_to_flight, addresses):
    '''Update address to flight mapping, which maps identifiers to flight objects and keeps track of current state-vector information'''
    update_finished_flights(address_to_flight, addresses)
    update_current_flights(address_to_flight, addresses)

def update_finished_flights(address_to_flight, addresses):
    '''Update finished flights in address to flight mappig'''
    old_addresses = address_to_flight.keys() - addresses
    for address in old_addresses:
        flight = address_to_flight[address]
        save_flight(flight) # save flight locations as well
        create_report(flight) # create report if flag is set to True
        del address_to_flight[address]

def update_current_flights(address_to_flight, addresses):
    '''Update address to flight mapping with current values of addresses'''
    for state in get_states_from_addresses(addresses):
        address = get_state_address(state)
        if address not in address_to_flight:
            new_flight = get_flight_from_state(state)
            address_to_flight[address] = new_flight
        flight = address_to_flight[address]
        flight.flight_locations.append(get_flight_location_from_state(state, flight))

def get_flight_location_from_state(state, flight):
    '''Return flight location from state-vector and flight object'''
    return FlightLocation(
        timestamp=state.time_position, # TODO: epoch to datetime
        longitude=state.longitude,
        latitude=state.latitude,
        altitude=state.baro_altitude, # barometric altitude
        speed=state.velocity,
        flight=flight
    )        

def get_flight_from_state(state):
    '''Return flight object from state-vector.'''
    flight_plan = get_flight_plan_from_state(state)
    airplane = get_airplane_from_state(state)
    longitude_based = should_partition_by_longitude(flight_plan) 
    return Flight (
        airplane=airplane,
        flight_plan=flight_plan,
        partition_interval=FLIGHT_PATH_PARTITION_INTERVAL,
        longitude_based=longitude_based
    )

def should_partition_by_longitude(flight_plan):
    '''Return if flight trajectory should be split by longitude or latitude.'''
    departure_airport = flight_plan.departure_airport
    destination_airport = flight_plan.destination_airport
    longitude_distance = abs(destination_airport.longitude - departure_airport.longitude)
    latitude_distance = abs(destination_airport.latitude - departure_airport.latitude)
    return longitude_distance >= latitude_distance

def get_airplane_from_state(state):
    '''Return airplane object from state-vector if the airplane is in database.
    Otherwise, create and return new airplane object.'''
    session = Session()
    icao_code = get_state_address(state)
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
    callsign = get_state_callsign(state)
    return get_airline_from_callsign(callsign)

def get_airline_from_callsign(callsign):
    '''Return Airline associated with callsign'''
    session = Session()
    icao_code, _ = split_callsign(callsign)
    return session.query(Airline).filter(Airline.icao_code == icao_code).first()

def split_callsign(callsign):
    '''Split callsign in meaninful chunks (airplane designator and flight number)'''
    airplane_designator, flight_number = callsign[:3], callsign[3:]
    return airplane_designator, flight_number

def get_flight_plan_from_state(state):
    '''Return flight plan information from state-vector'''
    session = Session()
    callsign = get_state_callsign(state)
    flight_plan = session.query(FlightPlan).filter(FlightPlan.callsign == callsign).first()
    return flight_plan
