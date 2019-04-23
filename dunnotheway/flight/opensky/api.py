import time

import requests

from common.log import logger
from flight.opensky.settings import (ITERATIONS_LIMIT_TO_RETRY_NEW_CONNECTION,
                                      OPEN_SKY_URL,
                                      SLEEP_TIME_TO_RETRY_NEW_CONNECTION_IN_SECS)

from .state_vector import StateVector


def get_flight_address_from_callsign(callsign):
    '''Return flight ICAO24 address from callsign'''
    for state in get_states():
        if state.callsign == callsign:
            return state.address
    return None

def get_states():
    '''Return current state-vectors'''
    r = request_open_sky_api()
    states = StateVector.build_from_dict(r.json())
    valid_states = [state for state in states if state.check_valid_state()]
    return valid_states

def get_states_from_bounding_box(bbox):
    '''Return current state-vectors within bounding box'''
    lamin, lamax, lomin, lomax = bbox
    payload = dict(lamin=lamin, lamax=lamax, lomin=lomin, lomax=lomax)
    r = request_open_sky_api(payload)
    states = StateVector.build_from_dict(r.json())
    valid_states = [state for state in states if state.check_valid_state()]
    return valid_states

def get_states_from_addresses(addresses):
    '''Return state-vectors of flights flying from a list of addresses or a single address'''
    if not addresses: # empty list
        return []
    payload = dict(icao24=addresses)
    r = request_open_sky_api(payload)
    states = StateVector.build_from_dict(r.json())
    valid_states = [state for state in states if state.check_valid_state()]
    logger.debug('State-Vectors found from addresses {0}: {1}'.format(
        addresses, valid_states))
    return valid_states

def request_open_sky_api(payload=None, iterations=0):
    '''Return request object of `OPEN_SKY_URL` with `payload`.
    Try to establish connection `ITERATIONS_LIMIT_TO_RETRY_NEW_CONNECTION` times
    waiting `SLEEP_TIME_TO_RETRY_NEW_CONNECTION_IN_SECS` seconds between each trial.''' 
    try:
        return requests.get(OPEN_SKY_URL, params=payload if payload else {})
    except requests.exceptions.RequestException as exception:
        handle_request_exception(exception, iterations)
        iterations += 1
    return request_open_sky_api(payload, iterations) 
    
def handle_request_exception(exception, iterations):
    time.sleep(SLEEP_TIME_TO_RETRY_NEW_CONNECTION_IN_SECS)
    if iterations >= ITERATIONS_LIMIT_TO_RETRY_NEW_CONNECTION:
        raise exception
