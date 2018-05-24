import sys
sys.path.append('/home/iuri/workspace/opensky-api/python')

from opensky_api import OpenSkyApi

def main():
    # instantiate Open Sky API
    api = OpenSkyApi()
    # retrieve aircraft states
    s = api.get_states()

if __name__ == '__main__':
    main()    
