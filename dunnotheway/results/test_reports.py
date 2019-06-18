import sys
sys.path.append('/home/iuri/workspace/dunnotheway/dunnotheway')

import os
import re
import pandas as pd

from common.settings import BASE_DIR
from common.utils import (distance_three_dimensions_coordinates,
                          distance_two_dimensions_coordinates)

REPORTS_DIR = os.path.join(BASE_DIR, 'results', 'reports')

AIRPORT_TRACKING_LIST = [
     #('SBRJ', 'SBSP'),
     #('SBSP', 'SBRJ'),
     #('SBBR', 'SBSP'),
     #('SBSP', 'SBBR'),
     #('SBFZ', 'SBGR'),
     ('SBGR', 'SBFZ'),
]
ALGORITHM_NAMES = ['DBSCAN', 'HDBSCAN', ]
DISTANCE_MEASURES = [
    distance_two_dimensions_coordinates, 
    distance_three_dimensions_coordinates,
]
MIN_ENTRIES_PER_SECTION_VALS = [0]
MIN_NUMBER_SAMPLES_VALS = [5, 25, 125]
MAX_DISTANCE_BETWEEN_SAMPLES_VALS = [10, 100, 1000]


def main(
    include_delimitation=True, 
    include_intersection=False,
    experiments=list(range(100)),
):
    index = 0
    for departure_destination_airports in AIRPORT_TRACKING_LIST:

        for (algorithm_name, 
            distance_measure,
            min_entries_per_section, 
            min_number_samples, 
            max_distance_between_samples) in gen_params():

            base_filepath = os.path.join(
                REPORTS_DIR, 
                str(departure_destination_airports))
            base_filepath = build_filepath_from_params(
                base_filepath,
                algorithm_name, 
                distance_measure,
                min_entries_per_section, 
                min_number_samples, 
                max_distance_between_samples)

            if not os.path.exists(base_filepath):
                continue

            index += 1
            if include_delimitation:
                experiment_str = build_experiment_str(
                    index, 
                    algorithm_name, 
                    distance_measure,
                    min_entries_per_section, 
                    min_number_samples, 
                    max_distance_between_samples)
                line = [experiment_str]

                filepath = os.path.join(base_filepath, 'delimitation.csv')
                if not os.path.exists(filepath):
                    print(filepath)
                    continue

                df = pd.read_csv(filepath)
                NORM = df['Posições de voo normalizadas'].iloc[-1]
                NORM_ = df['Posições de voo pertencentes a clusters'].iloc[-1]
                P = round(NORM_ / NORM, 3)
                
                filepath = os.path.join(base_filepath, 'clusters_summary_2.csv')
                if not os.path.exists(filepath):
                    print(filepath)
                    continue

                df = pd.read_csv(filepath)
                mu = df.loc[0, 'Média']
                md = df.loc[0, 'Mediana']
                mo_ = df.loc[0, 'Moda']
                r = df.loc[0, 'Variação']
                sigma = df.loc[0, 'Desvio Padrão']
                mo = re.findall(r'\d+', mo_)[0]
                
                line += [str(int(NORM))]
                line += [str(int(NORM_))]
                line += [str(P).replace('.', ',')]
                line += [str(round(mu, 3)).replace('.', ',')]
                line += [str(int(md))]
                line += [str(mo)]
                line += [str((int(r)))]
                line += [str(round(sigma, 3)).replace('.', ',')]

                line_str = ' & '.join(line)
                print (line_str, end=' \\\\\\hline\n')

            if include_intersection and index in experiments:
                experiment_str = build_experiment_str(
                    index, 
                    algorithm_name, 
                    distance_measure,
                    min_entries_per_section, 
                    min_number_samples, 
                    max_distance_between_samples)
                line = [experiment_str]

                filepath = os.path.join(base_filepath, 'cells.csv')
                df = pd.read_csv(filepath)
                CC = df.loc[0, 'Células convectivas']
                CC_ = df.loc[0, 'Células convectivas intersectadas']
                P = df.loc[0, 'Proporção']
                
                line += [str(int(CC))]
                line += [str(int(CC_))]
                line += [str(P).replace('.', ',')]

                line_str = ' & '.join(line)
                print (line_str, end=' \\\\\\hline\n')
                

def build_experiment_str(
    index, 
    _algorithm_name, 
    distance_measure,
    _min_entries_per_section, 
    min_number_samples, 
    max_distance_between_samples):

    return '${index}.\\,\\, dist. = {dist}, pts. = {pts}, \\epsilon = {eps}$'.format(
        index=index, 
        dist='hav.' if distance_measure == distance_two_dimensions_coordinates else 'euc.',
        pts=min_number_samples, 
        eps=max_distance_between_samples,
    )


def gen_params():
    for algorithm_name in ALGORITHM_NAMES:
        for distance_measure in DISTANCE_MEASURES:
            for min_entries_per_section in MIN_ENTRIES_PER_SECTION_VALS:
                for min_number_samples in MIN_NUMBER_SAMPLES_VALS:
                    for max_distance_between_samples in MAX_DISTANCE_BETWEEN_SAMPLES_VALS:
                        yield algorithm_name, distance_measure, min_entries_per_section, min_number_samples, max_distance_between_samples


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


if __name__ == '__main__':
    # main()
    main(
        include_delimitation=False, 
        include_intersection=True, 
        experiments=[5, 6],
    )
