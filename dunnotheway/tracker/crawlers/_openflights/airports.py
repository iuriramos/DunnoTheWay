'''Downloader from https://openflights.org/data.html'''

import requests
import pandas as pd

from tracker.common.settings import open_database_session
from tracker.models.airport import Airport

def fetch_airports_information():
    # download the data
    data = download_airports_information()
    
    # put it in a dataframe
    columns = [
        'id', 'name', 'city', 'country', 'iata', 'icao', 
        'latitude', 'longitude', 'altitude', 
        '_', '__', '___', 'type', 'source']
    airports_dataframe = pd.DataFrame(data, columns=columns)

    # filter brazil airports
    airports_dataframe = airports_dataframe[
        airports_dataframe['country'] == 'Brazil']

    # insert airports in database
    with open_database_session() as session:
        for _, airport_data in airports_dataframe.iterrows():
            airport = Airport(
                iata_code = airport_data['iata'],
                icao_code = airport_data['icao'],
                name = airport_data['name'],
                latitude = airport_data['latitude'],
                longitude = airport_data['longitude'],
                altitude = convert_feet_to_meters(airport_data['altitude']),
                country = airport_data['country'])
            session.add(airport)
        session.commit()
    
def download_airports_information():
    r = requests.get('https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat')
    return r.text

def convert_feet_to_meters(feet):
    FOOT_IN_METERS = 0.3048
    return FOOT_IN_METERS*feet