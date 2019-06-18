import sys
sys.path.append('/home/iuri/workspace/dunnotheway/dunnotheway')

import functools
import itertools
import operator
import os

import numpy as np
import pandas as pd
from scipy import stats

from common.db import open_database_session
from common.settings import BASE_DIR
from common.utils import (distance_three_dimensions_coordinates,
                          distance_two_dimensions_coordinates)
from engine.detector import (ALGORITHM_MAP,
                             search_intersections_convection_cells)
from engine.models.section import Section
from engine.normalizer import normalize_from_flight_locations
from engine.plot import (plot_flight_locations_params,
                         plot_from_flight_locations,
                         plot_from_multiple_flight_locations,
                         plot_multiple_flight_locations_params)
from flight.models.airport import Airport
from flight.models.flight import Flight
from flight.models.flight_location import FlightLocation
from flight.models.flight_plan import FlightPlan
from weather.models.convection_cell import ConvectionCell












REPORTS_DIR = os.path.join(BASE_DIR, 'results', 'reports')

AIRPORT_TRACKING_LIST = [
     ('SBRJ', 'SBSP'),
     ('SBSP', 'SBRJ'),
     ('SBBR', 'SBSP'),
     ('SBSP', 'SBBR'),
     ('SBFZ', 'SBGR'),
     ('SBGR', 'SBFZ'),
]
ALGORITHM_NAMES = ['HDBSCAN', 'DBSCAN', ]
DISTANCE_MEASURES = [
    distance_two_dimensions_coordinates, 
    distance_three_dimensions_coordinates,
]
MIN_ENTRIES_PER_SECTION_VALS = [0]
MIN_NUMBER_SAMPLES_VALS = [5, 25, 125]
MAX_DISTANCE_BETWEEN_SAMPLES_VALS = [1000, 100, 10]


def main():

    for departure_destination_airports in AIRPORT_TRACKING_LIST:
        
        for (algorithm_name, 
            distance_measure,
            min_entries_per_section, 
            min_number_samples, 
            max_distance_between_samples) in gen_params():
            
            run(algorithm_name,
                distance_measure, 
                min_entries_per_section, 
                min_number_samples, 
                max_distance_between_samples, 
                departure_destination_airports)

    for (algorithm_name, 
        distance_measure,
        min_entries_per_section, 
        min_number_samples, 
        max_distance_between_samples) in gen_params():
    
        plot_params_scenario(
            algorithm_name,
            distance_measure, 
            min_entries_per_section, 
            min_number_samples, 
            max_distance_between_samples,
            airport_tracking_list=AIRPORT_TRACKING_LIST,
        )

def plot_params_scenario(
    algorithm_name,
    distance_measure, 
    min_entries_per_section, 
    min_number_samples, 
    max_distance_between_samples, 
    airport_tracking_list
):
    airways, cells, airports = [], set(), set()
    
    for departure_destination_airports in airport_tracking_list:
        departure_airport, destination_airport = (
            get_airports_from_icao_code(*departure_destination_airports))

        base_filepath = os.path.join(
            REPORTS_DIR, 
            str(departure_destination_airports))

        # build flepath airways 
        filepath = build_filepath_from_params(
            base_filepath,
            algorithm_name, 
            distance_measure,
            min_entries_per_section, 
            min_number_samples, 
            max_distance_between_samples)
        
        # Run in case folder does not exist 
        if not os.path.exists(filepath):
            os.makedirs(filepath)

        airways_locations, _ = plot_airways(
            filepath,
            departure_airport, 
            destination_airport,
            algorithm_name, 
            distance_measure, 
            min_entries_per_section, 
            min_number_samples, 
            max_distance_between_samples
        )
        
        cells_locations = get_convection_cells(
            departure_airport, destination_airport)

        airports.add(departure_airport) 
        airports.add(destination_airport)
        airways += airways_locations
        cells |= cells_locations

    base_filepath = os.path.join(
        REPORTS_DIR, 'airways')
        
    # build flepath airways 
    filepath = build_filepath_from_params(
        base_filepath,
        algorithm_name, 
        distance_measure,
        min_entries_per_section, 
        min_number_samples, 
        max_distance_between_samples)
    
    # Run in case folder does not exist 
    if not os.path.exists(filepath):
        os.makedirs(filepath)
        # plot
        plot_from_multiple_flight_locations(
            filepath, 
            multiple_flight_locations=[cells, airways], 
            airports=airports) 



def get_convection_cells(departure_airport, destination_airport):
    # convection cells within departure and destination airports
    with open_database_session() as session:
        return {cell for cell in ConvectionCell.all_convection_cells(session) 
            if cell.is_convection_cells_between_airports(departure_airport, destination_airport)}


def run(
    algorithm_name,
    distance_measure, 
    min_entries_per_section, 
    min_number_samples, 
    max_distance_between_samples, 
    departure_destination_airports
):
    base_filepath = os.path.join(
        REPORTS_DIR, 
        str(departure_destination_airports))

    departure_airport, destination_airport = (
        get_airports_from_icao_code(*departure_destination_airports))

    # build flight paths
    filepath = os.path.join(
        base_filepath, 'flightpaths')
    if not os.path.exists(filepath):
        os.makedirs(filepath)
        plot_most_descriptive_flight_paths(
            filepath, 
            departure_airport,
            destination_airport,
        )

    # build flepath airways 
    filepath = build_filepath_from_params(
        base_filepath,
        algorithm_name, 
        distance_measure,
        min_entries_per_section, 
        min_number_samples, 
        max_distance_between_samples)
    
    # Run in case folder does not exist 
    if not os.path.exists(filepath):
        os.makedirs(filepath)

    _ = plot_airways(
        filepath,
        departure_airport, 
        destination_airport,
        algorithm_name, 
        distance_measure, 
        min_entries_per_section, 
        min_number_samples, 
        max_distance_between_samples
    )

def get_airports_from_icao_code(departure_airport_icao_code, destination_airport_icao_code):
    with open_database_session() as session:
        departure_airport = Airport.airport_from_icao_code(
            session, departure_airport_icao_code)
        destination_airport = Airport.airport_from_icao_code(
            session, destination_airport_icao_code)
        return departure_airport, destination_airport

    
def gen_params():
    for algorithm_name in ALGORITHM_NAMES:
        for distance_measure in DISTANCE_MEASURES:
            for min_entries_per_section in MIN_ENTRIES_PER_SECTION_VALS:
                for min_number_samples in MIN_NUMBER_SAMPLES_VALS:
                    for max_distance_between_samples in MAX_DISTANCE_BETWEEN_SAMPLES_VALS:
                        yield algorithm_name, distance_measure, min_entries_per_section, min_number_samples, max_distance_between_samples
                        if algorithm_name == 'HDBSCAN':
                            break # skip the inner loop


def build_filepath_from_params(
    filepath,
    algorithm_name, 
    distance_measure,
    min_entries_per_section, 
    min_number_samples, 
    max_distance_between_samples
):
    return os.path.join(
        filepath, 
        algorithm_name,
        distance_measure.__name__,
        'min_entries_per_section_' + str(min_entries_per_section) +
        '_min_number_samples_' + str(min_number_samples) +
        '_max_distance_between_samples_' + str(max_distance_between_samples),
    )

def build_filename_from_flight(flight):
    # id_ = str(flight.id)
    callsign = flight.flight_plan.callsign
    date_str = flight.created_date.strftime(r'(%d-%m-%Y %H:%M)')
    return callsign + date_str

def plot_airways(
    filepath,
    departure_airport,
    destination_airport,
    algorithm_name, 
    distance_measure, 
    min_entries_per_section, 
    min_number_samples, 
    max_distance_between_samples,
):
    filepath_airways = os.path.join(filepath, 'airways.pdf')
    # if os.path.exists(filepath_airways):
    #     return None, None
        
    algorithm = ALGORITHM_MAP[algorithm_name]

    wrapper_sections = algorithm.sections_from_airports(
        departure_airport, 
        destination_airport, 
        min_entries_per_section=min_entries_per_section,
        distance_measure=distance_measure, 
        min_number_samples=min_number_samples, 
        max_distance_between_samples=max_distance_between_samples)
    
    airways_locations = list(itertools.chain.from_iterable(
        [wp.clusters for wp in wrapper_sections]))

    plot_from_flight_locations(
        filepath=filepath_airways, 
        flight_locations=airways_locations,
        departure_airport=departure_airport,
        destination_airport=destination_airport,
    )
    
    # opposite direction as well
    pairwise_wrapper_sections = algorithm.sections_from_airports(
        destination_airport, 
        departure_airport, 
        min_entries_per_section=min_entries_per_section,
        distance_measure=distance_measure, 
        min_number_samples=min_number_samples, 
        max_distance_between_samples=max_distance_between_samples)
    
    pairwise_airways_locations = list(itertools.chain.from_iterable(
        [wp.clusters for wp in pairwise_wrapper_sections]))

    plot_from_multiple_flight_locations(
        filepath=os.path.join(filepath, 'airways_pairwise.pdf'), 
        multiple_flight_locations=[
            airways_locations,
            pairwise_airways_locations],
        departure_airport=departure_airport,
        destination_airport=destination_airport,
    )

    return airways_locations, pairwise_airways_locations


def plot_most_descriptive_flight_paths(filepath, departure_airport, destination_airport):    
    with open_database_session() as session:
    
        top_flights = sorted([
            flight 
            for flight_plan in (FlightPlan.
                flight_plans_from_airports(session, departure_airport, destination_airport))
                for flight in session.query(Flight).filter(Flight.flight_plan == flight_plan)], 
            key=lambda flight: len(flight.flight_locations),
            reverse=True,
        )[:10]

        for flight in top_flights:
            filename = build_filename_from_flight(flight)
            plot_from_flight_locations(
                filepath=os.path.join(filepath, filename + '.1.pdf'), 
                flight_locations=flight.flight_locations,
                departure_airport=departure_airport,
                destination_airport=destination_airport,
            )
            normalized_flight_locations = normalize_from_flight_locations(flight.flight_locations)
            plot_from_flight_locations(
                filepath=os.path.join(filepath, filename + '.2.norm.pdf'),
                flight_locations=normalized_flight_locations,
                departure_airport=departure_airport,
                destination_airport=destination_airport,
            )
            plot_from_multiple_flight_locations(
                filepath=os.path.join(filepath, filename + '.3.mult.pdf'),
                multiple_flight_locations=[
                    flight.flight_locations, 
                    normalized_flight_locations],
                departure_airport=departure_airport,
                destination_airport=destination_airport,
            )
            
            # plot flight path params
            plot_flight_locations_params(
                filepath=os.path.join(filepath, filename + '.4.params.pdf'), 
                flight_locations=flight.flight_locations,
            )
            normalized_flight_locations = normalize_from_flight_locations(flight.flight_locations)
            plot_flight_locations_params(
                filepath=os.path.join(filepath, filename + '.5.params.norm.pdf'),
                flight_locations=normalized_flight_locations,
            )
            plot_multiple_flight_locations_params(
                filepath=os.path.join(filepath, filename + '.6.params.mult.pdf'),
                multiple_flight_locations=[
                    flight.flight_locations, 
                    normalized_flight_locations],
            )


    
if __name__ == "__main__":
    # # main()
    # run(algorithm_name='DBSCAN',
    #     distance_measure=distance_two_dimensions_coordinates, 
    #     min_entries_per_section=0, 
    #     min_number_samples=25, 
    #     max_distance_between_samples=100, 
    #     departure_destination_airports=('SBGR', 'SBFZ'))

    plot_params_scenario(
        algorithm_name='DBSCAN',
        distance_measure=distance_two_dimensions_coordinates, 
        min_entries_per_section=0, 
        min_number_samples=25, 
        max_distance_between_samples=100, 
        airport_tracking_list=AIRPORT_TRACKING_LIST,
    )