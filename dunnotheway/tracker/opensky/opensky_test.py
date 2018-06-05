import sys
sys.path.append('/home/iuri/workspace/opensky-api/python')

from opensky_api import OpenSkyApi

def main():
    # instantiate Open Sky API
    api = OpenSkyApi()
    # retrieve aircraft states
    s = api.get_states()
    flight = None 
    for state_vector in s.states:
        if state_vector.callsign.strip() == 'GLO1454':
            flight = state_vector
    print(flight)
    
if __name__ == '__main__':
    main()    
