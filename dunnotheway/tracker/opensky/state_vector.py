from tracker.models.airplane import Airplane
from tracker.models.airline import Airline


class StateVector:
    '''Representation of State-Vector Class of OpenSky Network API'''
    
    def __init__(self, icao24, callsign, origin_country, time_position, last_contact, 
                longitude, latitude, geo_altitude, on_ground, velocity, true_track, 
                vertical_rate, sensors, baro_altitude, squawk, spi, position_source):
        '''Initialize State-Vector object'''
        self.icao24 = icao24
        self._callsign = callsign
        self.origin_country = origin_country
        self.time_position = time_position
        self.last_contact = last_contact
        self.longitude = longitude
        self.latitude = latitude
        self.geo_altitude = geo_altitude
        self.on_ground = on_ground
        self.velocity = velocity
        self.true_track = true_track
        self.vertical_rate = vertical_rate
        self.sensors = sensors
        self.baro_altitude = baro_altitude
        self.squawk = squawk
        self.spi = spi
        self.position_source = position_source

    def __repr__(self):
        return 'StateVector({icao24})'.format(
            icao24=repr(self.icao24))

    @staticmethod
    def build_from_dict(response_dict):
        if response_dict['states'] is None:
            return []
        state_vectors = []
        for args in response_dict['states']:
            state_vector = StateVector(*args)
            state_vectors.append(state_vector)
        return state_vectors

    def check_valid_state(self):
        '''Check if vector-state is valid'''
        return (
            self.time_position and
            self.longitude and 
            self.latitude and 
            self.velocity and 
            self.baro_altitude
        )

    @property
    def address(self):
        '''Return state-vector flight ICAO24 address'''
        return self.icao24 # flight identifier

    @property
    def callsign(self):
        '''Return state-vector flight callsign'''
        return self._callsign.strip()


    @staticmethod
    def airplane_from_state(session, state):
        '''Return airplane object from state-vector if the airplane was recorded in db before,
        create and return new airplane object, otherwise.'''
        icao_code = state.address
        if Airplane.exists_airplane(session, icao_code):
            airplane = Airplane.airplane_from_icao_code(session, icao_code)
        else: # create new airplane object
            airplane = Airplane(
                icao_code=icao_code,
                airline=Airline.airline_from_callsign(session, state.callsign))
        return airplane