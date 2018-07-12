import sys
import time 
#import matplotlib.pyplot as plt 
#import seaborn as sns

sys.path.append('/home/iuri/workspace/opensky-api/python')

from opensky_api import OpenSkyApi

def main():
    FLIGHT_CALLSIGN = 'TAM3531'
    ITERATION_LIMIT = 720
    flight = {
        'latitudes': [],
        'longitudes': [],
        'baro_altitudes': [],
        'geo_altitudes': [],
        'headings': [],
        'time_positions': [],
        'vertical_rates': [],
        'velocitys': [],
    }
    # instantiate Open Sky API
    api = OpenSkyApi()
    # retrieve aircraft states
    stop = False
    last_longitude, last_latitude = None, None
    count = 1
    while not stop:
        time.sleep(10)
        print('Iteration', count)
        count += 1
        s = api.get_states()
        for state_vector in s.states:
            if state_vector.callsign.strip() == FLIGHT_CALLSIGN:
                if count > ITERATION_LIMIT or state_vector.on_ground or (last_longitude, last_latitude) == (state_vector.longitude, state_vector.latitude):
                    stop = True
                print(state_vector)
                last_longitude, last_latitude = state_vector.longitude, state_vector.latitude
                flight['latitudes'].append(state_vector.latitude)
                flight['longitudes'].append(state_vector.longitude)
                flight['baro_altitudes'].append(state_vector.baro_altitude)
                flight['geo_altitudes'].append(state_vector.geo_altitude)
                flight['headings'].append(state_vector.heading)
                flight['time_positions'].append(state_vector.time_position)
                flight['vertical_rates'].append(state_vector.vertical_rate)
                flight['velocitys'].append(state_vector.velocity)

'''
    # longitudes and latitudes
    _, axes = plt.subplots()
    axes.scatter(flight['longitudes'], flight['latitudes'])
    axes.set_title('Longitudes vs Latitudes')
    axes.set_xlabel('Longitude')
    axes.set_ylabel('Latitude')
    plt.show()

    _, axes = plt.subplots(nrows=4, ncols=1)
    # baro and geo altitudes
    axes[0].plot(flight['baro_altitudes'], label='baro')
    axes[0].plot(flight['geo_altitudes'], label='geo')
    axes[0].legend()
    axes[0].set_title('Baro and Geo Altitudes')

    # heading, velocity and vertical rate
    axes[1].plot(flight['headings'])
    axes[1].set_title('Heading')

    axes[2].plot(flight['velocitys'])
    axes[2].set_title('Velocity')
    
    axes[3].plot(flight['vertical_rates'])
    axes[3].set_title('Vertical Rate')
    
    plt.show()
'''
if __name__ == '__main__':
    main()    
