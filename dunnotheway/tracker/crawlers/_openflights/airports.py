'''Downloader from https://openflights.org/data.html'''

import os
import sys
sys.path.append('/home/iuri/workspace/dunnotheway/dunnotheway')

from io import StringIO

import requests
import numpy as np
import pandas as pd

from tracker.common.settings import open_database_session
from tracker.models.airport import Airport

def fetch_airports_information():
    # fetch airports dataframe
    airports_dataframe = fetch_airports_dataframe()

    # filter brazilian airports
    airports_dataframe = airports_dataframe[
        airports_dataframe['country'] == 'Brazil']

    # insert airports in database
    insert_airports_in_database(airports_dataframe)

def fetch_airports_dataframe():
    data = download_airports_information()
    columns = [
        'id', 'name', 'city', 'country', 'iata', 'icao', 
        'latitude', 'longitude', 'altitude', 
        '_', '__', '___', 'type', 'source']
    airports_dataframe = pd.read_csv(
        data, na_values=r'\N', header=None, names=columns)
    return airports_dataframe

def download_airports_information():
    URL = 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat'
    r = requests.get(URL)
    return StringIO(r.text)

def insert_airports_in_database(airports_dataframe):
    with open_database_session() as session:
        for _, airport_data in airports_dataframe.iterrows():
            if check_valid_airport(airport_data):
                airport = get_airport_from_airport_data(airport_data)
                session.add(airport)
        session.commit()
    
def get_airport_from_airport_data(airport_data):
    return Airport(
        icao_code = airport_data['icao'], 
        name = airport_data['name'], 
        latitude = round(airport_data['latitude'], 3), 
        longitude = round(airport_data['longitude'], 3), 
        altitude = convert_feet_to_meters(airport_data['altitude']), 
        iata_code = airport_data['iata'] if not pd.isnull(airport_data['iata']) else None, 
        country = airport_data['country'])

def check_valid_airport(data):
    icao_codes = fetch_icao_codes_of_main_airports()
    return data['icao'] in icao_codes
    
def fetch_icao_codes_of_main_airports():
    icao_codes = set()
    filepath = get_filepath_icao_codes_of_main_airports()
    with open(filepath, 'r') as f:
        _header = next(f)
        for line in f:
            icao_code, _ = line.split('/')
            icao_code = icao_code.strip()
            icao_codes.add(icao_code)
    return icao_codes

def get_filepath_icao_codes_of_main_airports():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        'main_brazilian_airports.txt')
    
def convert_feet_to_meters(feet):
    FOOT_IN_METERS = 0.3048
    return round(FOOT_IN_METERS*feet, 0)


if __name__ == '__main__':
    fetch_airports_information()

