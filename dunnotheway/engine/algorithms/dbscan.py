from collections import defaultdict, namedtuple

from sklearn.cluster import DBSCAN as _DBSCAN

from common.utils import distance_three_dimensions_coordinates
from engine.models.section import Section
from engine.settings import (MAXIMUM_DISTANCE_BETWEEN_SAMPLES,  # TODO: Include eps
                             MIN_NUMBER_SAMPLES,
                             NUMBER_ENTRIES_PER_SECTION)


class DBSCAN:
    '''Section wrapper class implementing DBSCAN to delimit the points in the airways'''

    def __init__(self, section, **kwargs):
        eps = kwargs.get(
            'max_distance_between_samples', MAXIMUM_DISTANCE_BETWEEN_SAMPLES)
        min_samples = kwargs.get(
            'min_number_samples', MIN_NUMBER_SAMPLES)
        self.section = section
        self._label_to_flight_locations = defaultdict(list)
        self.classifier = _DBSCAN(
            eps=eps, 
            min_samples=min_samples, 
            metric=distance_three_dimensions_coordinates,
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
        return [DBSCAN(section, **kwargs) 
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