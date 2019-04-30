from collections import defaultdict, namedtuple

import numpy as np
import hdbscan

from common.log import logger
from common.db import open_database_session
from common.utils import distance_three_dimensions_coordinates
from flight.models.airport import Airport

from analyser.settings import NUMBER_ENTRIES_PER_SECTION



# import hdbscan
# self.classifier = hdbscan.HDBSCAN(
#     min_samples=DBSCAN_NUMBER_SAMPLES_CLUSTER,
#     metric=distance_three_dimensions_coordinates)
from sklearn.cluster import DBSCAN
from .settings import DBSCAN_MAXIMUM_DISTANCE, DBSCAN_NUMBER_SAMPLES_CLUSTER,


FlightLocationRecord = namedtuple(
    'FlightLocationRecord', ['latitude', 'longitude', 'altitude', 'flight_id'])


def run_classifier_before(func):
    def wrapper(self, *args, **kwargs):
        if not self._has_run_classifier:
            self.run_classifier()
            self._has_run_classifier = True
        return func(self, *args, **kwargs)
    return wrapper


class Section:
    '''Section Wrapper Class
    
    Set of flight locations sharing the same latitude or longitude 
    represented by `section_point` depending on `longitude_based`.
    `label` attributes the cluster group for a specific flight location.
    '''

    def __init__(self, section_point, longitude_based, records, classifier):
        self.section_point = section_point
        self.longitude_based = longitude_based
        self.records = records # FlightLocationRecords
        self.classifier = DBSCAN(
            eps=DBSCAN_MAXIMUM_DISTANCE, 
            min_samples=DBSCAN_NUMBER_SAMPLES_CLUSTER, 
            metric=distance_three_dimensions_coordinates)
        self._has_run_classifier = False
        self._label_to_records = defaultdict(list)

    def __repr__(self):
        return 'Section({sp})'.format(sp=self.section_point)
      
    @staticmethod
    def sections_related_to_airports(departure_airport, destination_airport):
        '''Return sections from flight locations'''
        with open_database_session() as session:
            flight_locations = Airport.normalized_flight_locations_related_to_airports(
                session, departure_airport, destination_airport)
        
        longitude_based = Airport.should_be_longitude_based(
            departure_airport, destination_airport)

        sections = []
        if not flight_locations:
            return sections
        
        prev_flight_location = flight_locations[0]
        section_flight_locations = [prev_flight_location]

        for curr_flight_location in flight_locations[1:]:
            if Section._flight_locations_are_part_of_the_same_section(
                prev_flight_location, curr_flight_location, longitude_based):
                section_flight_locations.append(curr_flight_location)
            else:
                if len(section_flight_locations) >= NUMBER_ENTRIES_PER_SECTION:
                    sections.append(
                        Section._from_flight_locations(section_flight_locations))
                section_flight_locations = [curr_flight_location]
            prev_flight_location = curr_flight_location

        return sections

    def run_classifier(self):
        self.classifier.fit([(record.latitude, record.longitude, record.altitude) 
            for record in self.records])
        
        for record, label in zip(self.records, self.classifier.labels_):
            if label != -1: # unclassified records
                self._label_to_records[label].append(record)
    
    def __iter__(self):
        yield from self._label_to_records.items()

    @run_classifier_before
    def records_from_label(self, label):
        return self._label_to_records[label]

    @run_classifier_before
    def predict_label_from_record(self, record):
        try:
            # TODO: remove hdscan library
            labels, _ = hdbscan.approximate_predict(
                self.classifier, [record])
            label = labels[0]
        except AttributeError as e:
            logger.error(str(e))
            label = -1
        return label
    
    @property
    @run_classifier_before
    def labels(self):
        return self.classifier.labels_
    
    @staticmethod
    def _from_flight_locations(flight_locations):
        '''Return a SINGLE section from flight locations'''
        fl1, fl2 = flight_locations[0], flight_locations[-1]
        longitude_based = (fl1.longitude == fl2.longitude)
        section_point = (fl1.longitude if longitude_based else fl1.latitude)
        
        return Section(
            section_point=section_point,
            longitude_based=longitude_based,
            records=Section._records_from_flight_locations(flight_locations))

    @staticmethod
    def _records_from_flight_locations(flight_locations):
        '''Return flight location records (longitude, latitude, altitude)'''
        return [FlightLocationRecord(
                    float(fl.latitude), float(fl.longitude), float(fl.altitude), fl.flight_id) 
                    for fl in flight_locations]

    @staticmethod
    def _flight_locations_are_part_of_the_same_section(this_fl, that_fl, longitude_based):
        return (this_fl.longitude == that_fl.longitude if longitude_based
            else this_fl.latitude == that_fl.latitude)
    
    # @staticmethod
    # def centroid_from_records(records):
    #     '''Return centroid from records'''
    #     longitude = np.mean([rec.longitude for rec in records])
    #     latitude = np.mean([rec.latitude for rec in records])
    #     altitude = np.mean([rec.altitude for rec in records])
    #     return FlightLocationRecord(longitude, latitude, altitude, flight_id=None)