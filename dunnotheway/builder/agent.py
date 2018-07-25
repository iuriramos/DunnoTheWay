
# from collections import Counter ### object should be hashable
# from sklearn.cluster import KMeans

from tracker.common.settings import open_database_session
from tracker.models.airport import Airport
from tracker.models.flight import Flight
from tracker.models.flight_plan import FlightPlan
from tracker.models.flight_location import FlightLocation

from .settings import logger
from .settings import NUMBER_ENTRIES_PER_SECTION, NUMBER_SECTIONS
from .plot import plot_flight_section

# global variables
session = None


def build_airways_from_airports(departure_airport_code, destination_airport_code):
    '''Build cruising paths from departure airport to destination airport'''
    global session 
    
    sections = []
    
    with open_database_session() as session:
        departure_airport = get_airport_from_airport_code(departure_airport_code)
        destination_airport = get_airport_from_airport_code(destination_airport_code)
        flight_locations = get_flight_locations_from_airports(departure_airport, destination_airport)
        sections = get_sections_from_flight_locations(flight_locations)
        sections = filter_sections(sections)

        for section in sections:
            # centroids = build_centroids_from_section(section) 
            # save_centroids(centroids) 
            create_report(section, centroids=[])

def build_centroids_from_section(section):
    '''Build centroids from section (set of flight locations)'''
    pass

def save_centroids(centroids):
    '''Save centroids in database including their created timestamp'''
    pass

def create_report(section, centroids):
    '''Create report with section points and centroids'''
    plot_flight_section(section)  

def get_flight_locations_from_airports(departure_airport, destination_airport):
    '''Return registered flight locations from departure airport to destination airport'''
    flight_locations = []
    flight_plans = get_flight_plans_from_airports(departure_airport, destination_airport)
    for flight_plan in flight_plans:
        flight_locations += get_flight_locations_from_flight_plan(flight_plan)
    return flight_locations      

def get_sections_from_flight_locations(flight_locations):
    '''Divide flight locations into groups called `sections` sharing the same latitude or longitude,
    depending on the `longitude_based` Flight attribute'''
    if not flight_locations:
        return []

    def check_on_same_section(prev, curr):
        return (float(prev.longitude) == float(curr.longitude) if longitude_based
            else float(prev.latitude) == float(curr.latitude))

    sections = []
    sort_flight_locations(flight_locations) # sort entries first
    
    prev = flight_locations[0]
    section = [prev]
    longitude_based = check_longitude_based(prev)

    for curr in flight_locations[1:]:
        if check_on_same_section(prev, curr):
            section.append(curr)
        else:
            if len(section) >= NUMBER_ENTRIES_PER_SECTION:
                sections.append(section.copy())
            section = [curr]
        prev = curr

    return sections

def sort_flight_locations(flight_locations):
    '''Sort flight locations according to `longitude_based` Flight attribute'''
    longitude_based = check_longitude_based(flight_locations[0])
    flight_locations.sort(
        key=lambda x: x.longitude if longitude_based else x.latitude)

def check_longitude_based(flight_location):
    longitude_based = flight_location.flight.longitude_based
    return longitude_based

def filter_sections(sections):
    '''Return at most `NUMBER_SECTIONS` sections'''
    len_sections = len(sections)
    step = max(1, len_sections//NUMBER_SECTIONS)
    return sections[::step]

def get_flight_plans_from_airports(departure_airport, destination_airport):
    '''Return flight plans from departure airport to destination airport'''
    flight_plans = session.query(FlightPlan).filter(
        FlightPlan.departure_airport == departure_airport and
        FlightPlan.destination_airport == destination_airport)
    return flight_plans

def get_flight_locations_from_flight_plan(flight_plan):
    '''Return flight locations of flight plan'''
    flight_locations = []
    flights = flight_plan.flights 
    for flight in flights:
        flight_locations += flight.flight_locations 
    return flight_locations

# DUPLICATED CODE - REFACTOR
def get_airport_from_airport_code(airport_code):
    '''Return airport from airport code'''
    airport = session.query(Airport).filter(Airport.code == airport_code).first()
    return airport