from collections import defaultdict, namedtuple

import numpy as np
from hdbscan import HDBSCAN
from sklearn.cluster import DBSCAN

from common.utils import distance_three_dimensions_coordinates
from tracker.models.airport import Airport

from .settings import (DBSCAN_MAXIMUM_DISTANCE, DBSCAN_NUMBER_SAMPLES_CLUSTER,
                       DBSCAN_PERCENTAGE_NOISE, NUMBER_ENTRIES_PER_SECTION,
                       NUMBER_SECTIONS, logger)


FlightLocationRecord = namedtuple(
    'FlightLocationRecord', ['longitude', 'latitude', 'altitude', 'flight_id'])

class Section:
    '''Section Wrapper Class
    
    Set of flight locations sharing the same latitude or longitude 
    represented by `section_point` depending on `longitude_based`.
    `label` attributes the cluster group for a specific flight location.
    '''

    def __init__(self, section_point, longitude_based, records):
        self.section_point = section_point
        self.longitude_based = longitude_based
        self.records = records # FlightLocationRecords
        self.classifier = HDBSCAN(
            min_samples=DBSCAN_NUMBER_SAMPLES_CLUSTER,
            metric=Section._distance_between_records)
        # clf = DBSCAN(
            #     eps=DBSCAN_MAXIMUM_DISTANCE, 
            #     min_samples=DBSCAN_NUMBER_SAMPLES_CLUSTER, 
            #     metric=distance_between_self.records)
        self._has_run_classifier = False
        self._label_to_records = defaultdict(list)
      
    @staticmethod
    def sections_related_to_airports(departure_airport, destination_airport):
        '''Return sections from flight locations'''
        flight_locations = Airport.normalized_flight_locations_related_to_airports(
            departure_airport, destination_airport)
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

    def records_from_label(self, label):
        if not self._has_run_classifier:
            self.classifier.fit(self.records)
            self._has_run_classifier = True
        
            for record, label in zip(self.records, self.classifier.labels_):
                if label != -1: # unclassified records
                    self._label_to_records[label].append(record)

        return self._label_to_records[label]

    def predict_label_from_record(self, record):
        ##### TODO: implement method
        return -1
    
    def __iter__(self):
        yield from self._label_to_records.items()

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
                    fl.longitude, fl.latitude, fl.altitude, fl.flight_id) 
                    for fl in flight_locations]

    @staticmethod
    def _flight_locations_are_part_of_the_same_section(this_fl, that_fl, longitude_based):
        return (float(this_fl.longitude) == float(that_fl.longitude) if longitude_based
            else float(this_fl.latitude) == float(that_fl.latitude))

    @staticmethod
    def _distance_between_records(record1, record2):
        return distance_three_dimensions_coordinates(
            (record1.latitude, record1.longitude, record1.altitude),
            (record2.latitude, record2.longitude, record2.altitude)
        )
    
    # @staticmethod
    # def centroid_from_records(records):
    #     '''Return centroid from records'''
    #     longitude = np.mean([rec.longitude for rec in records])
    #     latitude = np.mean([rec.latitude for rec in records])
    #     altitude = np.mean([rec.altitude for rec in records])
    #     return FlightLocationRecord(longitude, latitude, altitude, flight_id=None)