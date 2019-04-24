import time

from common.db import open_database_session
from common.log import logger

from flight.models.airport import Airport
from flight.models.bounding_box import (bounding_box_related_to_airports,
                                        BRAZILIAN_AIRSPACE_BBOX)
from flight.models.flight import Flight
from flight.models.flight_location import FlightLocation
from flight.models.flight_plan import FlightPlan
from flight.opensky.settings import (ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS,
                                     MIN_NUMBER_TO_SAVE_FLIGHT_LOCATIONS,
                                     SLEEP_TIME_TO_GET_FLIGHT_IN_SECS,
                                     SLEEP_TIME_TO_SEARCH_NEW_FLIGHTS_IN_SECS)

from .api import get_states_from_addresses, get_states_from_bounding_box

# global variables
session = None


def track_en_route_flights():
    '''Keep track of ALL en-route flights'''
    global session 

    address_to_flight = {}
    count_iterations = 0
    
    with open_database_session() as session:
        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS:
            time.sleep(SLEEP_TIME_TO_GET_FLIGHT_IN_SECS)
            if _should_update_flight_addresses(count_iterations):
                addresses = _get_addresses_within_brazilian_airspace()
            _update_flights(address_to_flight, addresses)
            count_iterations += 1
            

def track_en_route_flights_by_airports(
    departure_airport_code, destination_airport_code, round_trip_mode=False):
    '''Keep track of current flights information from departure airport to destination airport.'''
    global session 

    logger.info('Track flight addresses from {0} to {1} in {2} mode'.format(
        departure_airport_code, destination_airport_code, 'round trip' if round_trip_mode else 'one way'))
    
    address_to_flight = {}
    count_iterations = 0
    
    with open_database_session() as session:
        departure_airport = Airport.airport_from_icao_code(session, departure_airport_code)
        destination_airport = Airport.airport_from_icao_code(session, destination_airport_code)
        
        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS:
            time.sleep(SLEEP_TIME_TO_GET_FLIGHT_IN_SECS)
            if _should_update_flight_addresses(count_iterations):
                addresses = _update_flight_addresses(
                    departure_airport, destination_airport, round_trip_mode)
            _update_flights(address_to_flight, addresses)
            count_iterations += 1


def _should_update_flight_addresses(count_iterations):
    times = SLEEP_TIME_TO_SEARCH_NEW_FLIGHTS_IN_SECS//SLEEP_TIME_TO_GET_FLIGHT_IN_SECS
    return count_iterations % times == 0

def _update_flight_addresses(departure_airport, destination_airport, round_trip_mode):
    '''Update pool of flight addresses from time to time'''
    logger.info('Update flight addresses from {0!r} to {1!r} in {2} mode'.format(
        departure_airport, destination_airport, 'round trip' if round_trip_mode else 'one way'))

    addresses = _get_flight_addresses_from_airports(departure_airport, destination_airport)
    if round_trip_mode:
        addresses += _get_flight_addresses_from_airports(destination_airport, departure_airport)
    return addresses

def _get_flight_addresses_from_airports(departure_airport, destination_airport):
    '''Return flight ICAO24 addresses from departure airport to destination airport'''
    callsigns = Airport.callsigns_from_airports(
        session, departure_airport, destination_airport)
    bbox = bounding_box_related_to_airports(
        departure_airport, destination_airport)
    addresses = _get_addresses_from_callsigns_inside_bounding_box(callsigns, bbox)    
    logger.debug('Flight addresses found from {0!r} to {1!r}: {2}'.format(
        departure_airport, destination_airport, addresses))
    return addresses

def _get_addresses_within_brazilian_airspace():
    bbox = BRAZILIAN_AIRSPACE_BBOX
    callsigns = FlightPlan.all_callsigns(session)
    addresses = _get_addresses_from_callsigns_inside_bounding_box(callsigns, bbox)
    return addresses

def _get_addresses_from_callsigns_inside_bounding_box(callsigns, bbox):
    addresses = []
    states = get_states_from_bounding_box(bbox)
    for state in states:
        if state.callsign in callsigns:
            addresses.append(state.address)
    return addresses 

def _update_flights(address_to_flight, addresses):
    '''Update address to flight mapping, which maps identifiers to flight objects and keeps track of current state-vector information'''
    _update_finished_flights(address_to_flight, addresses)
    _update_current_flights(address_to_flight, addresses)

def _update_finished_flights(address_to_flight, addresses):
    '''Update finished flights in address to flight mappig'''
    old_addresses = address_to_flight.keys() - addresses
    logger.info('Update finished flights (addresses): {0}'.format(old_addresses))

    def _has_enough_flight_locations(flight):
        return len(flight.flight_locations) >= MIN_NUMBER_TO_SAVE_FLIGHT_LOCATIONS

    for address in old_addresses:
        flight = address_to_flight[address]
        flight.remove_duplicated_flight_locations()
        # save objects in database
        if _has_enough_flight_locations(flight):
            _save_flight(flight) 
        del address_to_flight[address]

def _update_current_flights(address_to_flight, addresses):
    '''Update address to flight mapping with current values of addresses'''
    logger.info('Update current flights: {0}'.format(addresses))

    for state in get_states_from_addresses(addresses):
        address = state.address
        if address not in address_to_flight:
            new_flight = Flight.construct_flight_from_state(session, state)
            address_to_flight[address] = new_flight
        flight = address_to_flight[address]
        (FlightLocation
            .construct_flight_location_from_state_and_flight(state, flight))

def _save_flight(flight):
    '''Save flight information in database (flight locations included)'''
    logger.info('Save flight {0!r}'.format(flight))
    session.add(flight)
    session.commit()
        
