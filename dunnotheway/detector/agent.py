from collections import namedtuple

from common.utils import distance_two_dimensions_coordinates
from weather.stsc import STSC
from tracker.models.airport import Airport
from tracker.models.flight_location import FlightLocation
from detector.flight_location_status import FlightLocationStatus

from .section import Section, FlightLocationRecord
from .obstacle import Obstacle

Intersection = namedtuple(
    'Intersection', ['convection_cell', 'flight_ids'])

reference_point = (lambda x, longitude_based: 
    x.longitude if longitude_based else x.latitude)

class ObstacleDetector:
    DepartureAndDestinationAirports = namedtuple(
        'DepartureAndDestinationAirports', ['departure_airport', 'destination_airport'])

    def __init__(self):
        self._airports_to_sections = {}
        self._stsc = STSC()
        self._airports_to_intersections = {}


    def check_obstacles_related_to_flight_location(
        self, prev_flight_location, curr_flight_location):
        '''Check for obstacles in current flight location'''
        flight = prev_flight_location.flight
        flight_plan = flight.flight_plan

        airports = ObstacleDetector.DepartureAndDestinationAirports(
            flight_plan.departure_airport, flight_plan.destination_airport)
        longitude_based = Airport.should_be_longitude_based(*airports)
        follow_ascending_order = Airport.follow_ascending_order(*airports)
        intersections = self.check_intersections_related_to_airports(*airports)
        
        normalized_flight_location = FlightLocation.normalize_flight_locations(
            [prev_flight_location, curr_flight_location])
        curr_flight_ids = self.flight_ids_in_the_same_airway_of_normalized_flight_location(
            normalized_flight_location, airports)
        
        intersection_index = 0
        
        def move_intersection_iterator(flight_location, intersection):
            return ((follow_ascending_order and 
                    reference_point(flight_location, longitude_based) > 
                    reference_point(intersection.cell, longitude_based)) or 
                (not follow_ascending_order and 
                    reference_point(flight_location, longitude_based) < 
                    reference_point(intersection.cell, longitude_based)))
                
        while intersection_index < len(intersections):
                intersection = intersections[intersection_index]
                if not move_intersection_iterator(
                    normalized_flight_location, intersection):
                    break
                intersection_index += 1
            
        obstacles = []
        for index in range(intersection_index, len(intersections)):
            cell, next_flight_ids = intersections[index]
            how_likely = ObstacleDetector.likelihood_of_encounter_obstacle(
                curr_flight_ids, next_flight_ids)
            obstacle = Obstacle(curr_flight_location, cell, how_likely)
            obstacles.append(obstacle)

        return obstacles

    def flight_ids_in_the_same_airway_of_normalized_flight_location(
        self, normalized_flight_location, airports):
        section = self._section_of_normalized_flight_location(
            normalized_flight_location, *airports)
        fl = normalized_flight_location
        record = FlightLocationRecord(
            fl.altitude, fl.longitude, fl.altitude, fl.flight_id)
        label = section.predict_label(record)
        records = section.records_from_label(labels=label)
        return {record.flight_id for record in records}


    def check_intersections_related_to_airports(self, departure_airport, destination_airport):
        airports = self.DepartureAndDestinationAirports(
            departure_airport, destination_airport)
            
        if self._stsc.has_changed:
            self._airports_to_intersections = {}

        if airports not in self._airports_to_intersections:
            intersections = self._check_intersections_related_to_airports(*airports)
            self._airports_to_intersections[airports] = intersections
        return self._airports_to_intersections[airports]
    

    def _check_intersections_related_to_airports(self, departure_airport, destination_airport):
        intersections = []
        
        sections = self._sections_from_airports(departure_airport, destination_airport)
        longitude_based = Airport.should_be_longitude_based(
            departure_airport, destination_airport)
        follow_ascending_order = Airport.follow_ascending_order(
            departure_airport, destination_airport)

        bbox = Airport.bounding_box_related_to_airports(departure_airport, destination_airport)
        sorting_key = (lambda x: reference_point(x, longitude_based))
        sorting_reverse = (not follow_ascending_order)
        cells = self._stsc.cells_within_bounding_box(
            bbox, sorting_key=sorting_key, sorting_reverse=sorting_reverse)
        
        if not cells:
            return intersections

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
                    intersection = (ObstacleDetector.
                        _intersection_between_section_and_cell(section, cell))
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

        return self.merge_intersections_with_the_same_convection_cell(intersections)

    def merge_intersections_with_the_same_convection_cell(self, intersections):
        merged_intersections = []
        if not intersections:
            return merged_intersections
        
        prev = intersections[0]
        flight_ids = prev.flight_ids
        for curr in intersections[1:]:
            if prev.convection_cell is curr.convection_cell:
                flight_ids.update(curr.flight_ids)
            else:
                merged_intersection = Intersection(prev.convection_cell, flight_ids)
                merged_intersections.append(merged_intersection)
                flight_ids = curr.flight_ids
            prev = curr
        # include the last entry as well
        merged_intersection = Intersection(prev.convection_cell, flight_ids)
        merged_intersections.append(merged_intersection)

        return merged_intersections   

    @staticmethod
    def distance_between_section_and_cell(section, cell):
        if section.longitude_based:
            section_reference_point = (cell.latitude, section.section_point)
        else: 
            section_reference_point = (section.section_point, cell.longitude)
        
        cell_reference_point = (cell.latitude, cell.longitude)
        return distance_two_dimensions_coordinates(
            section_reference_point, cell_reference_point
        )

    def _section_of_normalized_flight_location(
        self, normalized_flight_location, departure_airport, destination_airport):
        sections = self._sections_from_airports(departure_airport, destination_airport)
        longitude_based = normalized_flight_location.flight.longitude_based

        for section in sections:
            if (section.section_point == 
                reference_point(normalized_flight_location, longitude_based)):
                return section
        return None
    
    def _sections_from_airports(self, departure_airport, destination_airport):
        airports = self.DepartureAndDestinationAirports(
            departure_airport, destination_airport)
        
        if airports not in self._airports_to_sections:
            self._airports_to_sections[airports] = (Section.
                sections_related_to_airports(departure_airport, destination_airport))

        return self._airports_to_sections[airports]
        
    @staticmethod
    def likelihood_of_encounter_obstacle(curr_flight_ids, next_flight_ids):
        if len(curr_flight_ids) == 0:
            return 0.0
        return (
            len(curr_flight_ids.intersection(next_flight_ids)) / 
            len(curr_flight_ids))
        
    @staticmethod
    def _intersection_between_section_and_cell(section, cell):
        
        def has_intersection_between_record_and_cell(record, cell):
            distance = distance_two_dimensions_coordinates(
                (record.latitude, record.longitude), (cell.latitude, cell.longitude))
            return distance < cell.radius

        labels = []
        for label, records in section:
            for record in records:
                if has_intersection_between_record_and_cell(record, cell):
                    labels.append(label)
                    break

        flight_ids = {record.flight_id 
                        for label in labels 
                        for record in section.records_from_label(label)}
        return Intersection(cell, flight_ids)
        