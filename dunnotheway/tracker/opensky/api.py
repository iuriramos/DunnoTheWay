import os
import time 
import json
import requests
from sqlalchemy import literal
from contextlib import contextmanager
from datetime import datetime
import matplotlib.pyplot as plt 

from common.settings import BASE_DIR
from tracker.common.settings import logger
from tracker.models.airport import Airport
from tracker.models.airline import Airline
from tracker.models.airplane import Airplane
from tracker.models.flight import Flight
from tracker.models.flight_plan import FlightPlan
from tracker.models.flight_location import FlightLocation
from tracker.models.base import Session

from .state_vector import StateVector

# load config file
CONFIG_PATH = os.path.join(BASE_DIR, 'tracker', 'common', 'config.json')
with open(CONFIG_PATH) as f:
    config = json.load(f)

# config variables
OPEN_SKY_URL = 'https://opensky-network.org/api/states/all'
SLEEP_TIME_GET_FLIGHT = config['DEFAULT']['SLEEP_TIME_GET_FLIGHT'] 
SLEEP_TIME_SEARCH_FLIGHT = config['DEFAULT']['SLEEP_TIME_SEARCH_FLIGHT'] 
ITERATIONS_LIMIT = config['DEFAULT']['ITERATIONS_LIMIT'] 
FLIGHT_PATH_PARTITION_INTERVAL = config['DEFAULT']['FLIGHT_PATH_PARTITION_INTERVAL'] 
SIMILAR_STATE_VECTORS_LIMIT = config['DEFAULT']['SIMILAR_STATE_VECTORS_LIMIT'] 
BOUNDING_BOX_EXTENSION = config['DEFAULT']['BOUNDING_BOX_EXTENSION']


@contextmanager
def open_database_session():
    '''Contexto manager to handle session related to db'''
    global session
    session = Session()
    yield
    session.close()


def get_flight_address_from_callsign(callsign):
    '''Return flight ICAO24 address from callsign'''
    for state in get_states():
        if get_state_callsign(state) == callsign:
            return get_state_address(state)
    return None

def get_states():
    '''Return current state-vectors'''
    r = requests.get(OPEN_SKY_URL)
    states = StateVector.build_from_dict(r.json())
    valid_states = [state for state in states if check_valid_state(state)]
    return valid_states

def get_states_from_bounding_box(bbox):
    '''Return current state-vectors within bounding box'''
    lamin, lamax, lomin, lomax = bbox
    payload = dict(lamin=lamin, lamax=lamax, lomin=lomin, lomax=lomax)
    r = requests.get(OPEN_SKY_URL, params=payload)
    states = StateVector.build_from_dict(r.json())
    valid_states = [state for state in states if check_valid_state(state)]
    return valid_states

def get_states_from_addresses(addresses):
    '''Return state-vectors of flights flying from a list of addresses or a single address'''
    if not addresses: # empty list
        return []
    payload = dict(icao24=addresses)
    r = requests.get(OPEN_SKY_URL, params=payload)
    states = StateVector.build_from_dict(r.json())
    valid_states = [state for state in states if check_valid_state(state)]
    logger.debug('State-Vectors found from addresses {0}: {1}'.format(
        addresses, valid_states))
    return valid_states

def get_callsigns_from_airports(departure_airport, destination_airport):
    '''Return callsigns of flights flying from departure airport to destination airport'''
    flightplans = (session.query(FlightPlan)
        .filter(FlightPlan.departure_airport == departure_airport, FlightPlan.destination_airport == destination_airport)
        .all()) 
    callsigns = {fp.callsign for fp in flightplans}
    return callsigns

def get_bounding_box_from_airports(departure_airport, destination_airport):
    '''Return bounding box from departure airport to destination airport 
    (min latitude, max latitude, min longitude, max longitude)'''
    bbox = (
        float(min(departure_airport.latitude, destination_airport.latitude)), 
        float(max(departure_airport.latitude, destination_airport.latitude)),
        float(min(departure_airport.longitude, destination_airport.longitude)), 
        float(max(departure_airport.longitude, destination_airport.longitude))
    )
    logger.debug('Select bounding box {0} from departure airport {1!r} to destination airport {2!r}'.format(
        bbox, departure_airport, destination_airport))
    return bbox

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

def save_flight(flight):
    '''Save flight information in database'''
    logger.info('Save flight {0!r}'.format(flight))
    session.add(flight)
    session.commit()

def normalize_flight_locations(flight):
    '''Normalize flight locations information.'''
    logger.info('Normalize flight locations of flight {0!r}'.format(flight))
    filter_duplicated_flight_locations(flight)
    filter_cruising_flight_locations(flight)
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

    def check_cruising_flight_location(prev, curr): # also check other attributes
        return prev and prev.altitude == curr.altitude

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
        len(flight.flight_locations), len(fixed_flight_locations)))
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
    
    # speed and timestamp operations
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
        altitude=prev_location.altitude,
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

# check assumptions in a visual way
def create_report(flight): 
    '''Create report from flight (flight location, speed, vertical_rate)'''
    logger.info('Create report for flight {0!r}'.format(flight))
    draw_flight_path(flight)    
    draw_flight_location_params(flight)

def draw_flight_path(flight):
    '''Draw flight locations (longitude, latitude) path from departure airport to destination airport'''
    flight_locations = flight.flight_locations
    longitudes = [float(flight_location.longitude) for flight_location in flight_locations]
    latitudes = [float(flight_location.latitude) for flight_location in flight_locations]
    _, axes = plt.subplots()
    
    # draw flight path
    axes.scatter(longitudes, latitudes)
    axes.set_title('Longitudes vs Latitudes')
    axes.set_xlabel('Longitude')
    axes.set_ylabel('Latitude')

    filepath = get_reports_filepath(flight) + '_path.pdf'
    plt.savefig(filepath)

def draw_flight_location_params(flight):
    '''Draw flight locations parameters'''
    flight_locations = flight.flight_locations
    _, axes = plt.subplots(nrows=2, ncols=1)
    axis_altitude, axis_speed = axes

    # draw flight location params
    draw_flight_location_altitudes(flight_locations, axis_altitude)
    draw_flight_location_speeds(flight_locations, axis_speed)
    
    filepath = get_reports_filepath(flight) + '_params.pdf'
    plt.savefig(filepath)

def get_reports_filepath(flight):
    '''Return file path of the flight report'''
    REPORTS_DIR = os.path.join(BASE_DIR, 'tracker', 'reports')
    subdir_name = flight.flight_plan.departure_airport.code + '-' + flight.flight_plan.destination_airport.code
    REPORTS_SUBDIR = os.path.join(REPORTS_DIR, subdir_name)
    if not os.path.exists(REPORTS_SUBDIR):
        os.makedirs(REPORTS_SUBDIR)
    filename = str(flight.id)
    return os.path.join(REPORTS_SUBDIR, filename)

def draw_flight_location_speeds(flight_locations, axis):
    speeds = [float(flight_location.speed) for flight_location in flight_locations]
    axis.plot(speeds)
    axis.set_title('Cruising Speed')

def draw_flight_location_altitudes(flight_locations, axis):
    altitudes = [float(flight_location.altitude) for flight_location in flight_locations]
    axis.plot(altitudes)
    axis.set_title('Barometric Altitudes')

def track_flight_from_callsign(callsign):
    '''Keep track of flight information from its callsign'''
    if not get_flight_plan_from_callsign(callsign):
        return
    address_to_flight = {}
    count_iterations = 0
    with open_database_session():
        while count_iterations < ITERATIONS_LIMIT:
            # time.sleep(SLEEP_TIME_GET_FLIGHT)
            address = get_flight_address_from_callsign(callsign)
            update_flights(address_to_flight, addresses=[address])
            count_iterations += 1

def get_flight_plan_from_callsign(callsign):
    '''Return FlightPlan associated with callsign'''
    flight_plan = session.query(Airline).filter(FlightPlan.callsign == callsign).first()
    return flight_plan

def track_flights_from_airports(departure_airport_code, destination_airport_code, round_trip_mode=False):
    '''Keep track of current flights information from departure airport to destination airport'''
    logger.info('Track flight addresses from {0} to {1} in {2} mode'.format(
        departure_airport_code, destination_airport_code, 'round trip' if round_trip_mode else 'one way'))
    
    address_to_flight = {}
    count_iterations = 0
    
    def should_update_flight_addresses(count_iterations):
        times = SLEEP_TIME_SEARCH_FLIGHT//SLEEP_TIME_GET_FLIGHT
        return count_iterations % times == 0

    with open_database_session():
        departure_airport = get_airport_from_airport_code(departure_airport_code)
        destination_airport = get_airport_from_airport_code(destination_airport_code)
    
        while count_iterations < ITERATIONS_LIMIT:
            time.sleep(SLEEP_TIME_GET_FLIGHT)
            if should_update_flight_addresses(count_iterations):
                addresses = update_flight_addresses(departure_airport, destination_airport, round_trip_mode)
            update_flights(address_to_flight, addresses)
            count_iterations += 1

def get_airport_from_airport_code(airport_code):
    '''Return airport from airport code'''
    airport = session.query(Airport).filter(Airport.code == airport_code).first()
    return airport

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
    addresses = []
    callsigns = get_callsigns_from_airports(departure_airport, destination_airport)
    bbox = get_bounding_box_from_airports(departure_airport, destination_airport)
    states = get_states_from_bounding_box(bbox)
    
    for state in states:
        if get_state_callsign(state) in callsigns:
            addresses.append(get_state_address(state))
    
    logger.debug('Flight addresses found from {0!r} to {1!r}: {2}'.format(
        departure_airport, destination_airport, addresses))
    return addresses

def update_flights(address_to_flight, addresses):
    '''Update address to flight mapping, which maps identifiers to flight objects and keeps track of current state-vector information'''
    update_finished_flights(address_to_flight, addresses)
    update_current_flights(address_to_flight, addresses)

def update_finished_flights(address_to_flight, addresses):
    '''Update finished flights in address to flight mappig'''
    old_addresses = address_to_flight.keys() - addresses
    logger.info('Update finished flights (addresses): {0}'.format(old_addresses))

    def has_flight_locations(flight):
        return flight.flight_locations

    for address in old_addresses:
        flight = address_to_flight[address]
        normalize_flight_locations(flight)
        if has_flight_locations(flight):
            save_flight(flight) # save flight locations as well
            create_report(flight) # create report if flag is set to True
        del address_to_flight[address]

def update_current_flights(address_to_flight, addresses):
    '''Update address to flight mapping with current values of addresses'''
    logger.info('Update current flights: {0}'.format(addresses))

    for state in get_states_from_addresses(addresses):
        address = get_state_address(state)
        if address not in address_to_flight:
            new_flight = get_flight_from_state(state)
            address_to_flight[address] = new_flight
        flight = address_to_flight[address]
        flight.flight_locations.append(get_flight_location_from_state(state, flight))

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

def get_flight_from_state(state):
    '''Return flight object from state-vector.'''
    flight_plan = get_flight_plan_from_state(state)
    airplane = get_airplane_from_state(state)
    longitude_based = should_partition_by_longitude(flight_plan) 
    
    flight = Flight (
        airplane=airplane,
        flight_plan=flight_plan,
        partition_interval=FLIGHT_PATH_PARTITION_INTERVAL,
        longitude_based=longitude_based
    )

    logger.debug('Create new flight object: {0!r}'.format(flight))
    return flight

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
    icao_code, _ = split_callsign(callsign)
    airline = session.query(Airline).filter(Airline.icao_code == icao_code).first()
    return airline

def split_callsign(callsign):
    '''Split callsign in meaninful chunks (airplane designator and flight number)'''
    airplane_designator, flight_number = callsign[:3], callsign[3:]
    return airplane_designator, flight_number

def get_flight_plan_from_state(state):
    '''Return flight plan information from state-vector'''
    callsign = get_state_callsign(state)
    flight_plan = session.query(FlightPlan).filter(FlightPlan.callsign == callsign).first()
    return flight_plan

