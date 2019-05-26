import sys
sys.path.append('/home/iuri/workspace/dunnotheway/dunnotheway')

import os
import functools
import operator
import numpy as np
import pandas as pd
from scipy import stats

from common.settings import BASE_DIR
from common.db import open_database_session
from engine.detector import search_intersections_convection_cells, ALGORITHM_MAP
from engine.plot import plot_sections
from engine.models.section import Section
from flight.models.flight import Flight
from flight.models.flight_plan import FlightPlan
from flight.models.flight_location import FlightLocation
from weather.models.convection_cell import ConvectionCell


REPORTS_DIR = os.path.join(BASE_DIR, 'results', 'reports')

AIRPORT_TRACKING_LIST = [
      ('SBRJ', 'SBSP'),
    # ('SBSP', 'SBRJ'),
    # ('SBBR', 'SBSP'),
    # ('SBSP', 'SBBR'),
    # ('SBFZ', 'SBGR'),
    # ('SBBR', 'SBFZ'),

     ('SBBR', 'SBRJ'),
]
ALGORITHM_NAMES = ['DBSCAN', 'HDBSCAN']
MIN_ENTRIES_PER_SECTION_VALS = [10, 50, 250]
MIN_NUMBER_SAMPLES_VALS = [5, 25, 125]
MAX_DISTANCE_BETWEEN_SAMPLES_VALS = [1000, 100, 10]


def main():
    for departure_destination_airports in AIRPORT_TRACKING_LIST:
        base_filepath = os.path.join(REPORTS_DIR, str(departure_destination_airports))

        for (algorithm_name, 
            min_entries_per_section, 
            min_number_samples, 
            max_distance_between_samples) in gen_params():

            filepath = build_filepath_from_params(
                base_filepath,
                algorithm_name, 
                min_entries_per_section, 
                min_number_samples, 
                max_distance_between_samples)
            if not os.path.exists(filepath):
                os.makedirs(filepath)
            
            manager = search_intersections_convection_cells(
                airport_tracking_list=[departure_destination_airports],
                algorithm_name=algorithm_name,
                min_entries_per_section=min_entries_per_section, 
                min_number_samples=min_number_samples, 
                max_distance_between_samples=max_distance_between_samples)

            # normalization results
            get_normalization_results(filepath, manager, min_entries_per_section)

            # delimitation results
            get_delimitation_results(
                filepath,
                manager, 
                algorithm_name=algorithm_name,
                min_entries_per_section=min_entries_per_section, 
                min_number_samples=min_number_samples, 
                max_distance_between_samples=max_distance_between_samples)

            # intersection results
            get_intersection_results(filepath, manager)


def gen_params():
    for algorithm_name in ALGORITHM_NAMES:
        for min_entries_per_section in MIN_ENTRIES_PER_SECTION_VALS:
            for min_number_samples in MIN_NUMBER_SAMPLES_VALS:
                if min_number_samples > min_entries_per_section:
                    continue # prunning
                for max_distance_between_samples in MAX_DISTANCE_BETWEEN_SAMPLES_VALS:
                    yield algorithm_name, min_entries_per_section, min_number_samples, max_distance_between_samples


def build_filepath_from_params(
    filepath,
    algorithm_name, 
    min_entries_per_section, 
    min_number_samples, 
    max_distance_between_samples
):
    return os.path.join(
        filepath, 
        algorithm_name,
        'min_entries_per_section_' + str(min_entries_per_section) +
        '_min_number_samples_' + str(min_number_samples) +
        '_max_distance_between_samples_' + str(max_distance_between_samples),
    )


def get_normalization_results(filepath, manager, min_entries_per_section):
    
    with open_database_session() as session:
        for departure_airport, destination_airport in manager:

            count_flight_positions = sum(1 
                for flight_plan in (FlightPlan.
                    flight_plans_from_airports(session, departure_airport, destination_airport))
                    for flight_location in session.query(FlightLocation).join(Flight)
                        .filter(Flight.flight_plan == flight_plan))
            
            # (# positions) - (# positions')
            sections = Section.sections_from_airports(
                    departure_airport, 
                    destination_airport, 
                    min_entries_per_section=min_entries_per_section)
            count_normalized_flight_positions = sum(
                len(section) for section in sections)

            # ratio: positions -> positions'
            ratio = float(format(count_normalized_flight_positions / count_flight_positions, '.3f'))

            df = pd.DataFrame(
                data={
                    'Posições de voo': [count_flight_positions], 
                    'Posições de voo normalizadas': [count_normalized_flight_positions],
                    'Proporção': [ratio],
                }
            )

            df.to_csv(path_or_buf=os.path.join(filepath, 'normalization.csv', index=False))
            a = 1


def get_delimitation_results(
    filepath,
    manager, algorithm_name, min_entries_per_section, 
    min_number_samples, max_distance_between_samples):
    algorithm = ALGORITHM_MAP[algorithm_name]

    for departure_airport, destination_airport in manager:
        
        wrapper_sections = algorithm.sections_from_airports(
            departure_airport, 
            destination_airport, 
            min_entries_per_section=min_entries_per_section, 
            min_number_samples=min_number_samples, 
            max_distance_between_samples=max_distance_between_samples)
        
        # (# positions') - (# positions'')
        count_normalized_flight_positions = np.array([
            len(wrapper_section.section) for wrapper_section in wrapper_sections])
        count_clusterized_flight_positions = np.array([
            len(wrapper_section) for wrapper_section in wrapper_sections])

        # diff: positions' -> positions''
        diff = count_normalized_flight_positions - count_clusterized_flight_positions

        df = pd.DataFrame(
            data={
                'Posições de voo normalizadas': count_normalized_flight_positions, 
                'Posições de voo pertencentes a clusters': count_clusterized_flight_positions,
                'Diferença': diff,
            }
        )

        # summary delimitation table
        (df.describe().transpose()
            .to_csv(path_or_buf=os.path.join(filepath, 'delimitation_summary.csv')))
        
        # full delimitation table
        df.loc['Total',:]= df.sum(axis=0)
        df.to_csv(path_or_buf=os.path.join(filepath, 'delimitation.csv'))

        # labels Metrics
        labels = np.array([
            len(set(wrapper_section.labels)) -1 for wrapper_section in wrapper_sections])
        
        # summary clusters table (regular metrics)
        df = pd.DataFrame(data={'Clusters': labels})
        (df.describe().transpose()
            .to_csv(path_or_buf=os.path.join(filepath, 'clusters_summary_1.csv')))
                
        mean = np.mean(labels)
        median = np.median(labels)
        mode = stats.mode(labels)
        range_ = (labels.max() - labels.min())
        iqr = stats.iqr(labels)
        variance = np.var(labels)
        standard_deviation = np.std(labels)

        # summary clusters table (chosen metrics)
        df = pd.DataFrame(
            data={
                'Média': [float(format(mean, '.3f'))], 
                'Mediana': [float(format(median, '.3f'))], 
                'Moda': [str(mode)], 
                'Variação': [float(format(range_, '.3f'))], 
                'IQR': [float(format(iqr, '.3f'))], 
                'Variância': [float(format(variance, '.3f'))], 
                'Desvio Padrão': [float(format(standard_deviation, '.3f'))], 
            }
        )
        df.to_csv(path_or_buf=os.path.join(filepath, 'clusters_summary_2.csv'))

        # PLOT sections 
        plot_sections(
            filepath=os.path.join(filepath, 'imgs'),
            sections=wrapper_sections, 
            number_sections=-1) # plot ALL sections


def get_intersection_results(filepath, manager):

    for (departure_airport, destination_airport), intersections in manager.items():

        # convection cells within departure and destination airports
        with open_database_session() as session:
            cells = [cell for cell in ConvectionCell.all_convection_cells(session) 
                if cell.is_convection_cells_between_airports(departure_airport, destination_airport)]

        intersected_cells = [cell for cell, _, _, impact in intersections]

        ratio = None
        if cells:
            ratio = len(intersected_cells) / len(cells)

        df = pd.DataFrame(
            data={
                'Células convectivas': [len(cells)], 
                'Células convectivas intersectadas': [len(intersected_cells)], 
                'Proporção': [ratio], 
            }
        )
        df.to_csv(path_or_buf=os.path.join(filepath, 'cells.csv'), index=False)

        impacts = [impact for cell, _, _, impact in intersections]
        latitudes = [lat for lat, _, _ in intersected_cells]
        longitudes = [lon for _, lon, _ in intersected_cells]
        radiuses = [rad for _, _, rad in intersected_cells]
        timestamps = [cell.timestamp.strftime(r'%d-%m-%Y %H:%M') for cell in intersected_cells]

        df = pd.DataFrame(
            data={
                'Impacto': impacts, 
                'Latitude': latitudes, 
                'Longitude': longitudes, 
                'Raio': radiuses, 
                'Timestamp': timestamps, 
            }
        )
        (df.sort_values(by=['Impacto'], ascending=False)
            .to_csv(path_or_buf=os.path.join(filepath, 'intersection.csv')))


if __name__ == "__main__":
    main()
