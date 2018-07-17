class StateVector:
    '''Representation of State-Vector Class of OpenSky Network API'''
    
    def __init__(self, icao24, callsign, origin_country, time_position, last_contact, 
                longitude, latitude, geo_altitude, on_ground, velocity, true_track, 
                vertical_rate, sensors, baro_altitude, squawk, spi, position_source):
        '''Initialize State-Vector object'''
        self.icao24 = icao24
        self.callsign = callsign
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

    @staticmethod
    def build_from_dict(response_dict):
        if response_dict['states'] is None:
            return []
        state_vectors = []
        for args in response_dict['states']:
            state_vector = StateVector(*args)
            state_vectors.append(state_vector)
        return state_vectors