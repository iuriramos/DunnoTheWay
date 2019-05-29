import numpy as np

from collections import defaultdict, namedtuple

from sklearn.cluster import DBSCAN as _DBSCAN

from common.utils import (distance_three_dimensions_coordinates,
                          get_cartesian_coordinates, get_spherical_coordinates)
from engine.models.section import Section
from engine.settings import (MAXIMUM_DISTANCE_BETWEEN_SAMPLES,
                             MIN_NUMBER_SAMPLES, NUMBER_ENTRIES_PER_SECTION)


class DBSCAN:
    '''Section wrapper class implementing DBSCAN to delimit the points in the airways'''

    # cache dbscan sections list based on 
    # (
    #   departure_airport, destination_airport, min_entries_per_section, 
    #   min_number_samples, max_distance_between_samples, distance_measure
    # )
    cache = {}

    def __init__(self, section, min_samples, eps, metric):
        self.section = section
        self._label_to_flight_locations = defaultdict(list)
        self.classifier = _DBSCAN(
            min_samples=min_samples, 
            eps=eps, 
            metric=metric,
            n_jobs=-2)
        # IMPORTANT! run classifier first
        self.run_classifier() 

    def __repr__(self):
        return 'DBSCAN(Section({sp}))'.format(sp=self.section.section_point)
    
    def __iter__(self):
        '''Return CLUSTERIZED flight locations'''
        for flight_locations in self._label_to_flight_locations.values():
            yield from flight_locations
    
    def __len__(self):
        return sum(len(flight_locations) for flight_locations in self._label_to_flight_locations.values())

    @property
    def section_point(self):
        return self.section.section_point

    @property
    def longitude_based(self):
        return self.section.longitude_based
      
    @staticmethod
    def sections_from_airports(
        departure_airport, destination_airport, **kwargs):
        '''Return sections from flight locations'''
        min_entries_per_section = kwargs.get(
            'min_entries_per_section', NUMBER_ENTRIES_PER_SECTION)
        min_samples = kwargs.get(
            'min_number_samples', MIN_NUMBER_SAMPLES)
        eps = kwargs.get(
            'max_distance_between_samples', MAXIMUM_DISTANCE_BETWEEN_SAMPLES)
        metric = kwargs.get(
            'distance_measure', distance_three_dimensions_coordinates)

        key = (
            departure_airport.icao_code, 
            destination_airport.icao_code, 
            min_entries_per_section,
            min_samples,
            eps,
            metric.__name__,
        )
        
        if key not in DBSCAN.cache:
            DBSCAN.cache[key] = [DBSCAN(section, min_samples, eps, metric) 
                for section in Section.sections_from_airports(
                    departure_airport, destination_airport, **kwargs)]
        return DBSCAN.cache[key]

    def run_classifier(self):
        train_set = [
            flight_location.coordinates
            for flight_location in self.flight_locations]
        self.classifier.fit(train_set)
        self._build_label_to_flight_locations()

    def _build_label_to_flight_locations(self):
        for flight_location, label in zip(self.flight_locations, self.labels):
            if label != -1: # unclassified flight_locations
                self._label_to_flight_locations[label].append(flight_location)
    
    @property
    def flight_locations(self):
        '''Return ALL (normalized) flight locations'''
        return self.section.flight_locations

    @property
    def labels(self):
        return self.classifier.labels_

    def clusters(self):
        clusters = []
        for label, flight_locations in self._label_to_flight_locations.items():
            if label != -1 and flight_locations: # unclassified flight_locations
                clusters += self._find_cluster_from_light_locations(flight_locations),
        return sorted(clusters)

    def _find_cluster_from_light_locations(self, flight_locations):
        arr_xyz = np.array([
            get_cartesian_coordinates(
                flight_location.coordinates) 
            for flight_location in flight_locations])
        length = arr_xyz.shape[0]
        sum_x, sum_y, sum_z = (
            np.sum(arr_xyz[:, 0]), 
            np.sum(arr_xyz[:, 1]), 
            np.sum(arr_xyz[:, 2]))
        coordinate_xyz = sum_x/length, sum_y/length, sum_z/length
        return get_spherical_coordinates(coordinate_xyz)