from collections import defaultdict, namedtuple

import hdbscan
import numpy as np

from common.utils import (distance_three_dimensions_coordinates,
                          get_cartesian_coordinates, get_spherical_coordinates)
from engine.models.section import Section
from engine.settings import MIN_NUMBER_SAMPLES, NUMBER_ENTRIES_PER_SECTION


class HDBSCAN:
    '''Section wrapper class implementing HDBSCAN to delimit the points in the airways'''

    def __init__(self, section, **kwargs):
        min_number_samples = kwargs.get(
            'min_number_samples', MIN_NUMBER_SAMPLES)
        metric = kwargs.get(
            'distance_measure', distance_three_dimensions_coordinates)
        
        self.section = section
        self._label_to_flight_locations = defaultdict(list)
        self.classifier = hdbscan.HDBSCAN(
            min_samples=min_number_samples,
            metric=metric)
        # IMPORTANT! run classifier first
        self.run_classifier() 

    def __repr__(self):
        return 'HDBSCAN(Section({sp}))'.format(sp=self.section.section_point)
    
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
        return [HDBSCAN(section, **kwargs) 
            for section in Section.sections_from_airports(
                departure_airport, destination_airport, **kwargs)]

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
