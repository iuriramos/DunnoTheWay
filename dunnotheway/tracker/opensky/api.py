import requests
from tracker.common.settings import logger
from tracker.common.settings import OPEN_SKY_URL
from .state_vector import StateVector


def get_flight_address_from_callsign(callsign):
    '''Return flight ICAO24 address from callsign'''
    for state in get_states():
        if state.callsign == callsign:
            return state.address
    return None

def get_states():
    '''Return current state-vectors'''
    r = requests.get(OPEN_SKY_URL)
    states = StateVector.build_from_dict(r.json())
    valid_states = [state for state in states if state.check_valid_state()]
    return valid_states

def get_states_from_bounding_box(bbox):
    '''Return current state-vectors within bounding box'''
    lamin, lamax, lomin, lomax = bbox
    payload = dict(lamin=lamin, lamax=lamax, lomin=lomin, lomax=lomax)
    r = requests.get(OPEN_SKY_URL, params=payload)
    states = StateVector.build_from_dict(r.json())
    valid_states = [state for state in states if state.check_valid_state()]
    return valid_states

def get_states_from_addresses(addresses):
    '''Return state-vectors of flights flying from a list of addresses or a single address'''
    if not addresses: # empty list
        return []
    payload = dict(icao24=addresses)
    r = requests.get(OPEN_SKY_URL, params=payload)
    states = StateVector.build_from_dict(r.json())
    valid_states = [state for state in states if state.check_valid_state()]
    logger.debug('State-Vectors found from addresses {0}: {1}'.format(
        addresses, valid_states))
    return valid_states

