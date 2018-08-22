from collections import defaultdict, namedtuple

from hdbscan import HDBSCAN
import numpy as np
from sklearn.cluster import DBSCAN

from common.utils import distance_three_dimensions_coordinates
from tracker.common.settings import open_database_session
from tracker.models.airport import Airport
from tracker.models.flight import Flight
from tracker.models.flight_location import FlightLocation
from tracker.models.flight_plan import FlightPlan

from .plot import plot_flight_records
from .settings import (DBSCAN_MAXIMUM_DISTANCE, DBSCAN_NUMBER_SAMPLES_CLUSTER,
                       DBSCAN_PERCENTAGE_NOISE, NUMBER_ENTRIES_PER_GROUP,
                       NUMBER_GROUPS, logger)

# Record namedtuple
Record = namedtuple('Record', ['longitude', 'latitude', 'altitude'])

# global variables
session = None


def build_airways_from_airports(departure_airport_code, destination_airport_code):
    '''Build cruising paths from departure airport to destination airport'''
    global session 
    
    flight_locations_groups = []
    
    with open_database_session() as session:
        departure_airport = get_airport_from_airport_code(departure_airport_code)
        destination_airport = get_airport_from_airport_code(destination_airport_code)
        flight_locations = get_flight_locations_from_airports(departure_airport, destination_airport)
        flight_locations_groups = get_groups_from_flight_locations(flight_locations)
        flight_locations_groups = filter_groups(flight_locations_groups)

        for flight_locations in flight_locations_groups:
            records = get_flight_locations_records(flight_locations)
            labels = find_labels_from_records(records) 
            centroids = find_centroids(records, labels) 
            # then save centroids in database
            create_report(records, labels, centroids)


def get_flight_locations_records(flight_locations):
    '''Return flight locations records (longitude, latitude, altitude)'''
    records = [Record(fl.longitude, fl.latitude, fl.altitude) for fl in flight_locations]
    return records

def find_labels_from_records(records):
    '''Find labels from records (set of flight locations)'''
    records.sort(key=lambda x: x.altitude) # trick, stay tuned!
    # clf = DBSCAN(
    #     eps=DBSCAN_MAXIMUM_DISTANCE, 
    #     min_samples=DBSCAN_NUMBER_SAMPLES_CLUSTER, 
    #     metric=distance_between_records)
    clf = HDBSCAN(
        min_samples=DBSCAN_NUMBER_SAMPLES_CLUSTER,
        metric=distance_between_records)
    clf.fit(records)
    return clf.labels_

def distance_between_records(this, that):
    '''Define distance between two records'''
    this, that = Record(*this), Record(*that)
    this_polar_coordinate = this.latitude, this.longitude, this.altitude
    that_polar_coordinate = that.latitude, that.longitude, that.altitude
    return distance_three_dimensions_coordinates(this_polar_coordinate, that_polar_coordinate)

def find_centroids(records, labels):
    '''Find centroids from records and labels'''
    centroids_map = defaultdict(list)
    for record, label in zip(records, labels):
        centroids_map[label].append(record)
    centroids = [
        get_centroid_from_records(recs) 
        for label, recs in sorted(centroids_map.items())[1:]] # skip outliers, label=-1
    return centroids

def get_centroid_from_records(recs):
    '''Return centroid from records'''
    longitude = np.mean([rec.longitude for rec in recs])
    latitude = np.mean([rec.latitude for rec in recs])
    altitude = np.mean([rec.altitude for rec in recs])
    return Record(longitude, latitude, altitude)

def create_report(records, labels, centroids):
    '''Create report with records and labels'''
    plot_flight_records(records, labels, centroids)  

def get_flight_locations_from_airports(departure_airport, destination_airport):
    '''Return registered flight locations from departure airport to destination airport'''
    flight_locations = []
    flight_plans = get_flight_plans_from_airports(departure_airport, destination_airport)
    for flight_plan in flight_plans:
        flight_locations += get_flight_locations_from_flight_plan(flight_plan)
    return flight_locations      

def get_groups_from_flight_locations(flight_locations):
    '''Divide flight locations into groups called `groups` sharing the same latitude or longitude,
    depending on the `longitude_based` Flight attribute'''
    if not flight_locations:
        return []

    def check_on_same_group(prev, curr):
        return (float(prev.longitude) == float(curr.longitude) if longitude_based
            else float(prev.latitude) == float(curr.latitude))

    groups = []
    sort_flight_locations(flight_locations) # sort entries first
    
    prev = flight_locations[0]
    group = [prev]
    longitude_based = check_longitude_based(prev)

    for curr in flight_locations[1:]:
        if check_on_same_group(prev, curr):
            group.append(curr)
        else:
            if len(group) >= NUMBER_ENTRIES_PER_GROUP:
                groups.append(group.copy())
            group = [curr]
        prev = curr

    return groups

def sort_flight_locations(flight_locations):
    '''Sort flight locations according to `longitude_based` Flight attribute'''
    longitude_based = check_longitude_based(flight_locations[0])
    flight_locations.sort(
        key=lambda x: x.longitude if longitude_based else x.latitude)

def check_longitude_based(flight_location):
    longitude_based = flight_location.flight.longitude_based
    return longitude_based

def filter_groups(groups):
    '''Return at most `NUMBER_groupS` groups'''
    len_groups = len(groups)
    step = max(1, len_groups//NUMBER_GROUPS)
    return groups[::step]

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
    airport = session.query(Airport).filter(Airport.icao_code == airport_code).first()
    return airport
