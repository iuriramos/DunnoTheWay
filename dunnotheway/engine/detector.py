from collections import defaultdict, namedtuple

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from engine.models._obstacle import Obstacle
from engine.algorithms.dbscan import DBSCAN
from common.db import open_database_session
from common.utils import distance_two_dimensions_coordinates
from flight.models.airport import Airport
from flight.models.flight import Flight
from flight.models.flight_location import FlightLocation
from weather.models.convection_cell import ConvectionCell
from engine.models.intersection import Intersection, IntersectionManager


matplotlib.use('Agg')

session = None


reference_point = (lambda x, longitude_based: 
    x.longitude if longitude_based else x.latitude)


# TODO: leverage IntersectionManager to handle intersections
def search_intersections_convection_cells(airport_tracking_list=None):
    global session
    intersections = []

    with open_database_session() as session:
        convection_cells = ConvectionCell.all_convection_cells(session)
        
        for departure_airport, destination_airport in (
            _gen_departure_destination_airports(airport_tracking_list)):
            intersections += _check_multiple_intersections(
                destination_airport, departure_airport, convection_cells)

    return [intersection.convection_cell for intersection in intersections]


def _gen_departure_destination_airports(airport_tracking_list):
    airport_tracking_list = airport_tracking_list or []

    for departure_airport_code, destination_airport_code in airport_tracking_list:
        departure_airport = Airport.airport_from_icao_code(session, departure_airport_code)
        destination_airport = Airport.airport_from_icao_code(session, destination_airport_code)
        yield departure_airport, destination_airport


def _check_multiple_intersections(
    departure_airport, destination_airport, convection_cells):
    intersections = []
    
    sections = DBSCAN.sections_from_airports(
                    departure_airport, destination_airport)
    
    longitude_based = Airport.should_be_longitude_based(
        departure_airport, destination_airport)
    follow_ascending_order = Airport.follow_ascending_order(
        departure_airport, destination_airport)

    convection_cells.sort(
        key=(lambda x: reference_point(x, longitude_based)), 
        reverse=(not follow_ascending_order))
    
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
                impact = _check_intersection_between_section_cell(section, cell)
                if impact:
                    intersection = Intersection(
                        cell, departure_airport, destination_airport, impact)
                    intersections.append(intersection)           
                section = next(iter_sections)
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
    if section.longitude_based:
        section_reference_point = (float(cell.latitude), float(section.section_point))
    else: 
        section_reference_point = (float(section.section_point), float(cell.longitude))
    
    cell_reference_point = (cell.latitude, cell.longitude) # already casted to float
    return distance_two_dimensions_coordinates(
        section_reference_point, cell_reference_point)


def _check_intersection_between_section_cell(section, cell):
        
        def has_intersection(flight_location, cell):
            distance = distance_two_dimensions_coordinates(
                (float(flight_location.latitude), float(flight_location.longitude)), 
                (cell.latitude, cell.longitude))
            return distance < cell.radius

        # run classifier first
        section.run_classifier()

        labels = set()
        all_flight_ids = set()
        for label, flight_locations in section:
            for flight_location in flight_locations:
                all_flight_ids.add(flight_location.flight.id)
                if has_intersection(flight_location, cell):
                    labels.add(label)

        flight_ids = {flight_location.flight.id 
                        for label in labels 
                        for flight_location in section.get_flight_locations(label)}
        
        impact = None
        if len(all_flight_ids) > 0 and len(flight_ids) > 0:
            impact = len(flight_ids) / len(all_flight_ids)
        return impact
