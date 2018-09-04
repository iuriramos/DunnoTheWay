import sys
sys.path.append('/home/iuri/workspace/dunnotheway/dunnotheway')

import os
import re
import json
import requests
from collections import namedtuple
from sqlalchemy import literal
from bs4 import BeautifulSoup

from common.settings import BASE_DIR
from tracker.common.settings import open_database_session
from tracker.models.airline import Airline
from tracker.models.airport import Airport
from tracker.models.flight_plan import FlightPlan

DATA_TMP_FILE_NAME = 'data.tmp'
DATA_TMP_FILE_PATH = os.path.join(BASE_DIR, 'tracker', 'crawlers', '_flightaware', DATA_TMP_FILE_NAME)


def fetch_flight_plans():
    # fetch flight plans data
    data = fetch_flight_plans_data()

    # remove duplicate callsigns
    data = remove_invalid_flight_plans_data(data)
    
    # transform flight plans data into flight plan objects
    flight_plans = get_flight_plans_from_flight_plans_data(data)

    # insert flight plans into database
    insert_flight_plans_in_database(flight_plans)

def remove_invalid_flight_plans_data(data):
    '''
    Remove invalid flight plans data, which is 
    
    1. data having departure airport equals to destination airport;
    2. callsigns not represing repetitive flights (should be more than 5 flights).
    '''
    MIN_COUNT = 5
    DataWithCount = namedtuple('DataWithCount', ['data', 'count'])
    
    def similar_entries(this, that):
        return (this['departure_airport'] == that['departure_airport'] and 
                this['destination_airport'] == that['destination_airport'])

    unique = {} # callsign (hashable) >> DataWithCount(flight plan data, count)
    visited = set() # callsigns (hashable)

    for curr in (entry for entry in data 
                        if entry['departure_airport'] != entry['destination_airport']):
        callsign = curr['callsign']
        if callsign not in visited:
            unique[callsign] = DataWithCount(curr, 1)
            visited.add(callsign)
        elif callsign in unique: # already visited
            prev, count = unique[callsign]
            if similar_entries(curr, prev):
                unique[callsign] = DataWithCount(data, count+1)
            else:
                del unique[callsign]

    return (curr for curr, count in unique.values() if count >= MIN_COUNT)


def get_flight_plans_from_flight_plans_data(data):
    flight_plans = []
    for flight_plan_data in data:
        flight_plan = get_flight_plan_from_flight_plan_data(flight_plan_data)
        flight_plans.append(flight_plan)
    return flight_plans

def get_flight_plan_from_flight_plan_data(data):
    departure_airport = get_airport_from_icao_code(data['departure_airport'])
    destination_airport = get_airport_from_icao_code(data['destination_airport'])
    return FlightPlan(
        callsign=data['callsign'], 
        departure_airport=departure_airport, 
        destination_airport=destination_airport)

def get_airport_from_icao_code(icao_code):
    with open_database_session() as session:
        return session.query(Airport).filter(Airport.icao_code == icao_code).first()

def insert_flight_plans_in_database(flight_plans):
    with open_database_session() as session:
        for i, flight_plan in enumerate(flight_plans):
            q = session.query(FlightPlan).filter(
                FlightPlan.callsign == flight_plan.callsign)
            if (not session.query(literal(True))
                    .filter(q.exists()).scalar()):
                session.add(flight_plan)
                session.commit()

def fetch_flight_plans_data():
    if os.path.exists(DATA_TMP_FILE_PATH):
        return read_flight_plans_data_from_file()
    
    data = []
    for html_page in fetch_flight_plans_html_pages():
        partial_data = get_flight_plans_data_from_html_page(html_page)
        data.extend(partial_data)

    write_flight_plans_data_to_file(data)
    return data

def read_flight_plans_data_from_file():
    with open(DATA_TMP_FILE_PATH) as f:
        return json.load(f)

def write_flight_plans_data_to_file(data):
    with open(DATA_TMP_FILE_PATH, 'w') as f:
        json.dump(data, f, ensure_ascii=False)

def fetch_flight_plans_html_pages():
    for departure_airport in get_all_airports():
        for html_page in get_departure_airport_html_pages(departure_airport):
            yield html_page
    
def get_departure_airport_html_pages(airport):
    for url in get_departure_airport_urls(airport):
        html_page = get_html_page_of_url(url)
        if not has_flight_plan_data_in_html_page(html_page):
            raise StopIteration
        yield html_page

def get_flight_plans_data_from_html_page(html_page):
    table = get_flight_plan_data_table(html_page)
    table_rows = get_flight_plan_data_table_rows(table)
    flight_plans_data = []
    for row in table_rows:
        flight_plan_data = get_flight_plan_data_from_table_row(row)
        if is_flight_plan_data_valid(flight_plan_data):
            insert_departure_airport_in_flight_plan_data(flight_plan_data, table)
            flight_plans_data.append(flight_plan_data)
    return flight_plans_data

def get_departure_airport_urls(airport):
    URL = 'https://pt.flightaware.com/live/airport/{icao_code}/departures?;offset={offset}'
    OFFSET_START, OFFSET_STEP = 0, 20
    
    offset = OFFSET_START 
    while True:
        url = URL.format(icao_code=airport.icao_code, offset=offset)
        yield url
        offset += OFFSET_STEP

def has_flight_plan_data_in_html_page(html_page):
    return html_page.find_all('td', class_='smallrow1')

def get_flight_plan_data_table(html_page):
    return html_page.find('table', class_='prettyTable')

def get_flight_plan_data_table_rows(table):
    return table.contents[1:] # skip the first element thead

def get_flight_plan_data_from_table_row(row):
    iterator = row.children
    callsign_tag = next(iterator)
    _ = next(iterator)
    destination_airport_tag = next(iterator)
    destination_airport = get_destination_airport_from_table_col(destination_airport_tag)
    flight_plan_data = {
        'callsign': callsign_tag.span.string,
        'destination_airport': destination_airport}
    return flight_plan_data

def insert_departure_airport_in_flight_plan_data(flight_plan_data, table):
    departure_airport = get_departure_airport_from_table(table)
    flight_plan_data['departure_airport'] = departure_airport

def get_departure_airport_from_table(table):
    REGEX = r'\[(\w*)\]'
    departure_airport_tag_string = table.thead.th.string
    pattern = re.compile(REGEX)
    search = pattern.search(departure_airport_tag_string)
    return search.group(1)
    
def get_destination_airport_from_table_col(destination_airport_tag):
    destination_airport_tag_string = destination_airport_tag.a.string
    try:
        _, destination_airport = destination_airport_tag_string.split('/')
    except ValueError: # is not divided such as 'iata_code / icao_code'
        destination_airport = ''
    return destination_airport.strip()

def is_flight_plan_data_valid(flight_plan_data):
    return (has_flight_plan_data_valid_callsign(flight_plan_data) and
            has_flight_plan_data_valid_destination_airport(flight_plan_data))
    
def has_flight_plan_data_valid_callsign(flight_plan_data):
    callsign = flight_plan_data['callsign']
    with open_database_session() as session:
        airlines = session.query(Airline).all()
        return any(callsign.startswith(airline.icao_code) for airline in airlines)   
    
def has_flight_plan_data_valid_destination_airport(flight_plan_data):
    icao_code = flight_plan_data['destination_airport']
    with open_database_session() as session:
        q = session.query(Airport).filter(Airport.icao_code == icao_code)
        return session.query(literal(True)).filter(q.exists()).scalar()
        
def get_all_airports():
    with open_database_session() as session:
        return session.query(Airport).all()

def get_html_page_of_url(url):
    r = requests.get(url)
    return BeautifulSoup(r.text, 'html.parser') 


if __name__ == '__main__':
    fetch_flight_plans()

