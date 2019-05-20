import numpy as np

from common.db import open_database_session
from engine.detector import search_intersections_convection_cells, ALGORITHM_MAP
from engine.models.section import Section
from flight.models.flight_plan import FlightPlan
from flight.models.flight_location import FlightLocation


# TODO: change airport tracking list for performance reasons
AIRPORT_TRACKING_LIST = None
ALGORITHM_NAMES = ['DBSCAN', 'HDBSCAN']
MIN_ENTRIES_PER_SECTION_VALS = [10, 100, 1000]
MIN_NUMBER_SAMPLES_VALS = [5, 25, 125]
MAX_DISTANCE_BETWEEN_SAMPLES_VALS = [1000, 100, 10]


def main():
    for (algorithm_name, 
        min_entries_per_section, 
        min_number_samples, 
        max_distance_between_samples) in gen_params():
        manager = search_intersections_convection_cells(
            airport_tracking_list=AIRPORT_TRACKING_LIST,
            algorithm_name=algorithm_name,
            min_entries_per_section=min_entries_per_section, 
            min_number_samples=min_number_samples, 
            max_distance_between_samples=max_distance_between_samples)

        # normalization results
        get_normalization_results(manager, min_entries_per_section)

        # delimitation results
        get_delimitation_results(
            manager, 
            algorithm_name=algorithm_name,
            min_entries_per_section=min_entries_per_section, 
            min_number_samples=min_number_samples, 
            max_distance_between_samples=max_distance_between_samples)

        # intersection results
        get_intersection_results(manager)


def gen_params():
    for algorithm_name in ALGORITHM_NAMES:
        for min_entries_per_section in MIN_ENTRIES_PER_SECTION_VALS:
            for min_number_samples in MIN_NUMBER_SAMPLES_VALS:
                if min_number_samples > min_entries_per_section:
                    continue # prunning
                for max_distance_between_samples in MAX_DISTANCE_BETWEEN_SAMPLES_VALS:
                    yield algorithm_name, min_entries_per_section, min_number_samples, max_distance_between_samples



def get_normalization_results(manager, min_entries_per_section):
    with open_database_session() as session:
        for departure_airport, destination_airport in manager:
            print ('#', departure_airport, destination_airport)
            print ('-' * 50)
            
            for flight_plan in (FlightPlan.
                flight_plans_from_airports(session, departure_airport, destination_airport)):

                len_flight_positions = len(
                    session.query(FlightLocation).filter(
                        FlightLocation.flight.flight_plan == flight_plan))
                
                # (# positions) - (# positions')
                sections = Section.sections_from_airports(
                        departure_airport, 
                        destination_airport, 
                        min_entries_per_section=min_entries_per_section)
                len_flight_positions_prime = sum(
                    len(section) for section in sections)

                # loss of information: positions -> positions'
                print ('Loss', len_flight_positions_prime // len_flight_positions)

                # TODO(maybe) - PLOT airways in 3D
                sections

def get_delimitation_results(
    manager, algorithm_name, min_entries_per_section, 
    min_number_samples, max_distance_between_samples):
    algorithm = ALGORITHM_MAP[algorithm_name]

    for departure_airport, destination_airport in manager:
        print ('#', departure_airport, destination_airport)
        print ('-' * 50)

        wrapper_sections = algorithm.sections_from_airports(
            departure_airport, 
            destination_airport, 
            min_entries_per_section=min_entries_per_section, 
            min_number_samples=min_number_samples, 
            max_distance_between_samples=max_distance_between_samples)
        
        # (# positions') - (# positions'')
        len_flight_positions = np.array(
            len(wrapper_section.section) for wrapper_section in wrapper_sections)
        len_flight_positions_prime = np.array(
            len(wrapper_section) for wrapper_section in wrapper_sections)

        # TODO(maybe) - PLOT diff distribution
        diff_flight_positions = len_flight_positions - len_flight_positions_prime
        print (diff_flight_positions)

        # average diff positions
        print (diff_flight_positions.average())

        # TODO(maybe) - PLOT noise distribution
        noise_flight_positions = diff_flight_positions / len_flight_positions
        print (noise_flight_positions)

        # average diff positions
        print (noise_flight_positions.average())

        # TODO(maybe) - PLOT sections and clusters


def get_intersection_results(manager):
    for (departure_airport, destination_airport), intersections in manager.items():
        print ('#', departure_airport, destination_airport)
        print ('-' * 50)

        print ('Cell', '    Impact')
        for cell, _, _, impact in intersections:
            print (cell, '->', impact)

        impact, cell = max((impact, cell) for cell, _, _, impact in intersections)
        print ('Most impactful convection cell', cell, '->', impact)


if __name__ == "__main__":
    main()
