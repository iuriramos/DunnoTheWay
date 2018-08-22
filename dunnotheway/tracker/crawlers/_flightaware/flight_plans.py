import sys
sys.path.append('/home/iuri/workspace/dunnotheway/dunnotheway')

import re
import requests
from bs4 import BeautifulSoup

from tracker.common.settings import open_database_session
from tracker.models.airline import Airline
from tracker.models.airport import Airport
from tracker.models.flight_plan import FlightPlan


def fetch_flight_plans():
    # fetch flight plans data
    data = fetch_flight_plans_data()
    
    # transform flight plans data into flight plans
    flight_plans = get_flight_plans_from_flight_plans_data(data)

    # insert flight plans into database
    insert_flight_plans_in_database(flight_plans)

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
        for flight_plan in flight_plans:
            session.add(flight_plan)
        session.commit()

def fetch_flight_plans_data():
    data = []
    for html_page in fetch_flight_plans_html_pages():
        partial_data = get_flight_plans_data_from_html_page(html_page)
        data.extend(partial_data)
    return data

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
    table = get_callsign_table(html_page)
    table_rows = get_callsign_table_rows(table)
    flight_plans_data = []
    for row in table_rows:
        flight_plan_data = get_callsign_from_table_row(row)
        if has_flight_plan_data_valid_airline(flight_plan_data):
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
    return not html_page.find_all('td', class_='smallrow1')

def get_callsign_table(html_page):
    return html_page.find('table', class_='prettyTable')

def get_callsign_table_rows(table):
    return table.tbody.contents

def get_callsign_from_table_row(row):
    iterator = row.children
    callsign_tag = next(iterator)
    _ = next(iterator)
    destination_airport_tag = next(iterator)
    destination_airport = get_destination_airport_from_table_col(destination_airport_tag)
    callsign = {
        'callsign': callsign_tag.string,
        'destination_airport': destination_airport}
    return callsign

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
    _, destination_airport = destination_airport_tag_string.split('/')
    return destination_airport.strip()

def has_flight_plan_data_valid_airline(flight_plan_data):
    callsign = flight_plan_data['callsign']
    with open_database_session() as session:
        airlines = session.query(Airline).all()
        return any(callsign.startswith(airline.icao_code) for airline in airlines)    

def get_all_airports():
    with open_database_session() as session:
        return session.query(Airport).all()

def get_html_page_of_url(url):
    r = requests.get(url)
    return BeautifulSoup(r.text) 


if __name__ == '__main__':
    fetch_flight_plans()

