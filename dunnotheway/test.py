import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from collections import defaultdict, namedtuple

from common.db import open_database_session
from common.utils import distance_two_dimensions_coordinates

import flight.models.fixtures
from flight.models.airport import Airport
from flight.models.flight import Flight
from flight.models.flight_location import FlightLocation
from weather.models.convection_cell import ConvectionCell
from analyser.models.section import Section
from analyser.models.obstacle import Obstacle
from analyser._obstacle_detector import ObstacleDetector


matplotlib.use('Agg')

session = None

# TODO: change to attributes / maybe a class is more convenient?
# Intersection = namedtuple(
#     'Intersection', ['convection_cell', 'departure_airport', 'destination_airports', 'impact?'])
Intersection = namedtuple(
    'Intersection', ['convection_cell', 'partition', 'flight_ids', 'all_flight_ids'])

reference_point = (lambda x, longitude_based: 
    x.longitude if longitude_based else x.latitude)


def convection_cells_stats(convection_cell_ids):
    global session

    with open_database_session() as session:
        BSB = Airport.airport_from_icao_code(session, 'SBBR')
        GRU = Airport.airport_from_icao_code(session, 'SBGR')
        
        print('create intersections table from', BSB, 'to', GRU)
        # create_intersections_table(session, convection_cell_ids, BSB, GRU)
        print('#' * 20)
        print()

        print('create intersections table from', GRU, 'to', BSB)
        create_intersections_table(session, convection_cell_ids, GRU, BSB)
        print('#' * 20)
        print()

        print('generate flights vs convection cells charts')
        plot_flights_vs_convection_cells(session, convection_cell_ids)


def create_intersections_table(session, convection_cell_ids, departure_airport, destination_airport):
    convection_cell_to_partition_likelihood = {}
    convection_cell_to_callsigns = defaultdict(set)

    for convection_cell_id in convection_cell_ids:
        convection_cell = session.query(ConvectionCell).filter(
            ConvectionCell.id == convection_cell_id).first()

        intersections = check_for_intersections(
            departure_airport, destination_airport, convection_cell)
        if not intersections:
            continue 

        for weather_obstacle in convection_cell.obstacles:
            flight = weather_obstacle.flight_location.flight
            callsign = flight.flight_plan.callsign
            convection_cell_to_callsigns[convection_cell].add(callsign)

        max_intersection = intersections[0]
        max_likelihood = len(max_intersection.flight_ids)/len(max_intersection.all_flight_ids)
        for intersection in intersections[1:]:
            likelihood = len(intersection.flight_ids)/len(intersection.all_flight_ids)
            if likelihood > max_likelihood:
                max_intersection, max_likelihood = intersection, likelihood
        
        convection_cell_to_partition_likelihood[convection_cell] = (
            max_intersection.partition, max_likelihood)

    # log result
    print('convection_cell', 'partition', 'likelihood')
    for convection_cell, (partition, likelihood) in convection_cell_to_partition_likelihood.items():
        print(convection_cell, partition, likelihood)
        print(convection_cell_to_callsigns[convection_cell])

def plot_flights_vs_convection_cells(session, convection_cell_ids):
    flight_key_to_convection_cells = defaultdict(set)
    flight_key_to_flights = defaultdict(set)

    for convection_cell_id in convection_cell_ids:
        convection_cell = session.query(ConvectionCell).filter(
            ConvectionCell.id == convection_cell_id).first()

        for weather_obstacle in convection_cell.obstacles:
            flight = weather_obstacle.flight_location.flight
            key = flight.airplane.icao_code
            flight_key_to_convection_cells[key].add(convection_cell)
            flight_key_to_flights[key].add(flight)

    for flight_key in flight_key_to_convection_cells:
        flight_locations = []
        for flight in flight_key_to_flights[flight_key]:
            flight_locations += flight.flight_locations
        flight_locations.sort(key=lambda x: x.timestamp)
        plot_flight_locations_vs_convection_cells(
            flight_locations, flight_key_to_convection_cells[flight_key])
        
def plot_flight_locations_vs_convection_cells(flight_locations, convection_cells):
    plot_flight_trajectory_and_convection_cells(flight_locations, convection_cells)    
    # plot_flight_location_params(flight_locations)

def plot_flight_trajectory_and_convection_cells(flight_locations, convection_cells):
    latitudes = [float(fl.latitude) for fl in flight_locations]
    longitudes = [float(fl.longitude) for fl in flight_locations]
    _, axes = plt.subplots(figsize=(12, 4))

    # plot flight path
    axes.scatter(latitudes, longitudes)
    
    # plot convection cells
    x = [cc.latitude for cc in convection_cells]
    y = [cc.longitude for cc in convection_cells]
    axes.scatter(x, y)

    for i, txt in enumerate([cc.id for cc in convection_cells]):
        axes.annotate(txt, (x[i], y[i]))

    # plot airports
    flight = flight_locations[0].flight
    departure_airport = flight.flight_plan.departure_airport
    destination_airport = flight.flight_plan.destination_airport

    x = [airport.latitude for airport in (departure_airport, destination_airport)]
    y = [airport.longitude for airport in (departure_airport, destination_airport)]
    axes.scatter(x, y)
    axes.scatter(x, y, c=('green', 'red'))

    for i, txt in enumerate([airport.icao_code 
                            for airport in (departure_airport, destination_airport)]):
        axes.annotate(txt, (x[i], y[i]))
    
    axes.set_title('Flight Trajectory of ' + str(flight) + 
        ' from ' + str(departure_airport) + 
        ' to ' + str(destination_airport))
    axes.set_xlabel('Latitude')
    axes.set_ylabel('Longitude')

    plt.show()

def plot_flight_location_params(flight_locations):
    '''Plot flight locations parameters'''
    _, axes = plt.subplots(nrows=2, ncols=1)
    axis_altitude, axis_speed = axes

    # plot flight location params
    plot_flight_location_altitudes(flight_locations, axis_altitude)
    plot_flight_location_speeds(flight_locations, axis_speed)
    
    plt.show()

def plot_flight_location_speeds(flight_locations, axis):
    speeds = [float(flight_location.speed) for flight_location in flight_locations]
    axis.plot(speeds)
    axis.set_title('Cruising Speed')

def plot_flight_location_altitudes(flight_locations, axis):
    altitudes = [float(flight_location.altitude) for flight_location in flight_locations]
    axis.plot(altitudes)
    axis.set_title('Altitude')


def check_for_intersections(departure_airport, destination_airport, convection_cell):
    intersections = []
    
    sections = Section.sections_related_to_airports(
                    departure_airport, destination_airport)

    clusters_freq = [len(set(s.labels)) for s in sections]
    print ('clusters found')
    print (clusters_freq)

    longitude_based = Airport.should_be_longitude_based(
        departure_airport, destination_airport)
    follow_ascending_order = Airport.follow_ascending_order(
        departure_airport, destination_airport)

    cells = [convection_cell] # TODO: maybe use more than one cell
    iter_sections, iter_cells = iter(sections), iter(cells)
    section, cell = next(iter_sections), next(iter_cells)

    def move_section_iterator(section, cell):
        return ((follow_ascending_order and 
                section.section_point < reference_point(cell, longitude_based)) or
            (not follow_ascending_order and 
                section.section_point > reference_point(cell, longitude_based)))

    while True:
        try:
            distance = (ObstacleDetector.
                distance_between_section_and_cell(section, cell))
            
            if distance < cell.radius: 
                intersection = (
                    intersection_between_section_and_cell(section, cell))
                if intersection.flight_ids:
                    intersections.append(intersection)
                section = next(iter_sections)
            else: 
                if move_section_iterator(section, cell): 
                    # section is placed before cell
                    section = next(iter_sections)
                else:
                    cell = next(iter_cells)
        except StopIteration:
            break

    return intersections


def intersection_between_section_and_cell(section, cell):
        
        def has_intersection_between_record_and_cell(record, cell):
            distance = distance_two_dimensions_coordinates(
                (record.latitude, record.longitude), (cell.latitude, cell.longitude))
            return distance < cell.radius

        #### TODO: forcing update on section labels
        _ = section.labels 
        
        labels = []
        all_flight_ids = set()
        for label, records in section:
            for record in records:
                all_flight_ids.add(record.flight_id)
                if has_intersection_between_record_and_cell(record, cell):
                    labels.append(label)
                    # break

        flight_ids = {record.flight_id 
                        for label in labels 
                        for record in section.records_from_label(label)}
        return Intersection(cell, section, flight_ids, all_flight_ids)




if __name__ == '__main__':
    # mapping = convection_cells_stats(
    #     convection_cell_ids=[3, 4, 5, 9])

    # convection_cells_stats(list(range(2, 18)))
    convection_cells_stats([3, 4, 5, 8])