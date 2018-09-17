import os
import json

from common.settings import BASE_DIR


# load config file
CONFIG_PATH = os.path.join(BASE_DIR, 'tracker', 'opensky', 'config.json')
with open(CONFIG_PATH) as f:
    config = json.load(f)

# config variables
OPEN_SKY_URL = 'https://opensky-network.org/api/states/all'
SLEEP_TIME_TO_GET_FLIGHT_IN_SECS = config['FLIGHT_TRACKER']['SLEEP_TIME_TO_GET_FLIGHT_IN_SECS'] 
SLEEP_TIME_TO_SEARCH_NEW_FLIGHTS_IN_SECS = config['FLIGHT_TRACKER']['SLEEP_TIME_TO_SEARCH_NEW_FLIGHTS_IN_SECS']
ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS = config['FLIGHT_TRACKER']['ITERATIONS_LIMIT_TO_SEARCH_FLIGHTS'] 
FLIGHT_PATH_PARTITION_INTERVAL_IN_DEGREES = config['FLIGHT_TRACKER']['FLIGHT_PATH_PARTITION_INTERVAL_IN_DEGREES'] 
CRUISING_VERTICAL_RATE_IN_MS = config['FLIGHT_TRACKER']['CRUISING_VERTICAL_RATE_IN_MS'] # METERS / SECOND
MIN_NUMBER_TO_SAVE_FLIGHT_LOCATIONS = config['FLIGHT_TRACKER']['MIN_NUMBER_TO_SAVE_FLIGHT_LOCATIONS']
SLEEP_TIME_TO_RETRY_NEW_CONNECTION_IN_SECS = config['FLIGHT_TRACKER']['SLEEP_TIME_TO_RETRY_NEW_CONNECTION_IN_SECS'] 
ITERATIONS_LIMIT_TO_RETRY_NEW_CONNECTION = config['FLIGHT_TRACKER']['ITERATIONS_LIMIT_TO_RETRY_NEW_CONNECTION'] 

# BASED ON THE COVER AREA OF STSC (SISTEMA DE TEMPO SEVERO CONVECTIVO)
MIN_LATITUDE_BRAZILIAN_AIRSPACE = config['BRAZILIAN_AIRSPACE']['MIN_LATITUDE_BRAZILIAN_AIRSPACE'] 
MAX_LATITUDE_BRAZILIAN_AIRSPACE = config['BRAZILIAN_AIRSPACE']['MAX_LATITUDE_BRAZILIAN_AIRSPACE'] 
MIN_LONGITUDE_BRAZILIAN_AIRSPACE = config['BRAZILIAN_AIRSPACE']['MIN_LONGITUDE_BRAZILIAN_AIRSPACE'] 
MAX_LONGITUDE_BRAZILIAN_AIRSPACE = config['BRAZILIAN_AIRSPACE']['MAX_LONGITUDE_BRAZILIAN_AIRSPACE'] 
