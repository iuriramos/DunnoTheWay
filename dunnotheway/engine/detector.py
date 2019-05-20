from collections import defaultdict, namedtuple

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

# from engine.models._obstacle import Obstacle
from common.db import open_database_session
from common.utils import distance_two_dimensions_coordinates
from engine.algorithms import dbscan, hdbscan 
from flight.models.airport import Airport
from flight.models.flight import Flight
from flight.models.flight_location import FlightLocation
from weather.models.convection_cell import ConvectionCell
from engine.models.intersection import Intersection, IntersectionManager


matplotlib.use('Agg')

session = None

ALGORITHM_MAP = {
    None: dbscan.DBSCAN,
    'DBSCAN': dbscan.DBSCAN,
    'HDBSCAN': hdbscan.HDBSCAN,
    # 'OPTICS': optics.OPTICS,
}


reference_point = (lambda x, longitude_based: 
    x.longitude if longitude_based else x.latitude)



def search_intersections_convection_cells(
    airport_tracking_list=None, algorithm_name=None, **kwargs):
    global session

    manager = IntersectionManager()

    with open_database_session() as session:
        all_convection_cells = ConvectionCell.all_convection_cells(session)
        
        for departure_airport, destination_airport in (
            _gen_departure_destination_airports(airport_tracking_list)):
            # filter convection cells withing departure and destination airports
            convection_cells = [
                cell for cell in all_convection_cells 
                    if cell.is_convection_cells_between_airports(
                        departure_airport, destination_airport)]
            # find intersections
            intersections = _check_multiple_intersections(
                destination_airport, departure_airport, 
                convection_cells, algorithm_name, **kwargs)
            # record results
            for intersection in intersections:
                manager.set_intersection(intersection)

    return manager

def _gen_departure_destination_airports(airport_tracking_list):
    if airport_tracking_list is None:
        yield from _gen_default_airport_tracking_list()
    else:
        for departure_airport_code, destination_airport_code in airport_tracking_list:
            departure_airport = Airport.airport_from_icao_code(session, departure_airport_code)
            destination_airport = Airport.airport_from_icao_code(session, destination_airport_code)
            yield departure_airport, destination_airport


def _gen_default_airport_tracking_list():
    all_airports = session.query(Airport).all()
    for departure_airport in all_airports:
        for destination_airport in all_airports:
            if departure_airport != destination_airport:
                yield departure_airport, destination_airport


def _check_multiple_intersections(
    departure_airport, destination_airport, convection_cells, algorithm_name=None, **kwargs):
    intersections = []
    
    algorithm = ALGORITHM_MAP[algorithm_name]
    sections = algorithm.sections_from_airports(
        departure_airport, 
        destination_airport, 
        **kwargs,
    )
    
    longitude_based = Airport.should_be_longitude_based(
        departure_airport, destination_airport)
    follow_ascending_order = Airport.follow_ascending_order(
        departure_airport, destination_airport)

    convection_cells.sort(
        key=(lambda x: reference_point(x, longitude_based)), 
        reverse=(not follow_ascending_order))
    
    if not sections or not convection_cells:
        return intersections

    iter_sections, iter_cells = iter(sections), iter(convection_cells)
    section, cell = next(iter_sections), next(iter_cells)

    def should_move_section_iterator(section, cell):
        return ((follow_ascending_order and 
                section.section_point < reference_point(cell, longitude_based)) or
            (not follow_ascending_order and 
                section.section_point > reference_point(cell, longitude_based)))

    while True:
        try:
            distance = distance_between_section_and_cell(section, cell)
            
            if distance < cell.radius: 
                impact = measure_impact_convection_cell_on_section(section, cell)
                if impact:
                    intersection = Intersection(
                        cell, departure_airport, destination_airport, impact)
                    intersections.append(intersection)           
                cell = next(iter_cells)
            else: 
                if should_move_section_iterator(section, cell): 
                    # section is placed before cell, move cell
                    section = next(iter_sections)
                else:
                    cell = next(iter_cells)
        except StopIteration:
            break

    return intersections


def distance_between_section_and_cell(section, cell):
    min_distance = float('infinity')
    for flight_location in section:
        min_distance = min(
            min_distance, 
            distance_between_flight_location_and_cell(flight_location, cell))
    return min_distance


def distance_between_flight_location_and_cell(flight_location, cell):
    flight_location_2d = (float(flight_location.latitude), float(flight_location.longitude))
    cell_2d = (cell.latitude, cell.longitude)
    return distance_two_dimensions_coordinates(flight_location_2d, cell_2d)


def measure_impact_convection_cell_on_section(section, cell):
        
        def has_intersection(flight_location, cell):
            distance = distance_between_flight_location_and_cell(flight_location, cell)
            return distance < cell.radius

        # run classifier first
        section.run_classifier()

        all_flight_locations = set()
        intersected_flight_locations = set()
        for flight_location in section:
            all_flight_locations.add(flight_location.id)
            if has_intersection(flight_location, cell):
                intersected_flight_locations.add(flight_location.id)
        
        impact = None
        if len(all_flight_locations) > 0 and len(intersected_flight_locations) > 0:
            impact = len(intersected_flight_locations) / len(all_flight_locations)
        return impact
