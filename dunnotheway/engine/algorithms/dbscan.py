from collections import defaultdict, namedtuple

from sklearn.cluster import DBSCAN as _DBSCAN

from common.utils import distance_three_dimensions_coordinates
from engine.models.section import Section
from engine.settings import (MAXIMUM_DISTANCE_BETWEEN_SAMPLES,  # TODO: Include eps
                             MIN_NUMBER_SAMPLES,
                             NUMBER_ENTRIES_PER_SECTION)


def run_classifier_before(func):
    def wrapper(self, *args, **kwargs):
        self.run_classifier()
        return func(self, *args, **kwargs)
    return wrapper


class DBSCAN:
    '''Section wrapper class implementing DBSCAN to delimit the points in the airways'''

    def __init__(self, section, **kwargs):
        self.section = section
        self.eps = kwargs.get('max_distance_between_samples', MAXIMUM_DISTANCE_BETWEEN_SAMPLES)
        self.min_samples = kwargs.get('min_number_samples', MIN_NUMBER_SAMPLES)
        self.classifier = _DBSCAN(
            eps=self.eps, 
            min_samples=self.min_samples, 
            metric=distance_three_dimensions_coordinates)
        self._has_run_classifier = False
        self._label_to_flight_locations = defaultdict(list)

    def __repr__(self):
        return 'DBSCAN(Section({sp}))'.format(sp=self.section.section_point)
    
    def __iter__(self):
        for flight_locations in self._label_to_flight_locations.values():
            yield from flight_locations

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
        if not self._has_run_classifier:
            train_set = [
                (
                    float(flight_location.latitude), 
                    float(flight_location.longitude), 
                    float(flight_location.altitude),
                ) 
                for flight_location in self.section.flight_locations
            ]
            self.classifier.fit(train_set)
            self._has_run_classifier = True
            self._build_label_to_flight_locations()

    def _build_label_to_flight_locations(self):
        for flight_location, label in zip(
            self.section.flight_locations, self.classifier.labels_):
            if label != -1: # unclassified flight_locations
                self._label_to_flight_locations[label].append(flight_location)
    
    @run_classifier_before
    def get_flight_locations(self, label):
        return self._label_to_flight_locations[label]
    
    @property
    @run_classifier_before
    def labels(self):
        return self.classifier.labels_
