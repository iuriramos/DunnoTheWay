from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import StandardScaler

from common.db import open_database_session
from analyser.models.section import Section
from flight.models.airport import Airport

from .settings import NUMBER_SECTIONS


SIZES = [200, 300, 400, 500, 600]
COLORS = ['red', 'blue', 'green', 'orange', 'purple', 'black']


def build_airways_related_to_airports(
    departure_airport_code, destination_airport_code, number_sections=NUMBER_SECTIONS):
    '''Build cruising paths from departure airport to destination airport'''
    global session 

    def filter_sections(sections):
        '''Return at most `NUMBER_SECTIONS` sections'''
        step = max(1, len(sections)//number_sections)
        return sections[::step]
    
    with open_database_session() as session:
        departure_airport = Airport.airport_from_icao_code(
            session, departure_airport_code)
        destination_airport = Airport.airport_from_icao_code(
            session, destination_airport_code)
        sections = Section.sections_related_to_airports(
            departure_airport, destination_airport)
        
        for section in filter_sections(sections):
            _plot_flight_records(section.records, section.labels, centroids=[])


def _plot_flight_records(records, labels, centroids):
    '''Plot flight records, which is set of flight locations represented by (longitude, latitude, altitude).'''

    if not records:
        raise ValueError('records should not be empty')
    
    first_record, last_record = records[0], records[-1]
    longitude_based = (first_record.longitude == last_record.longitude)
    
    if longitude_based:
        longitutes_or_altitudes = [record.latitude for record in records]
    else:
        longitutes_or_altitudes = [record.longitude for record in records]

    altitudes = [record.altitude for record in records]
    _, axis = plt.subplots()
    
    axis.set_title(
        ('Longitude: ' + str(first_record.longitude)) if longitude_based 
        else ('Latitude: ' + str(first_record.latitude)))
    axis.set_xlabel('Latitude' if longitude_based else 'Longitude')
    axis.set_ylabel('Altitude')

    # plot flight path
    axis.scatter(longitutes_or_altitudes, altitudes, c=labels, alpha=0.5)

    # plot centroids
    centroids = np.array(centroids, dtype=np.float)
    if centroids.size: # not empty
        if longitude_based:
            axis.scatter(centroids[:,1], centroids[:,2], marker='x')
        else: # latitude based
            axis.scatter(centroids[:,0], centroids[:,2], marker='x')
    
    # show figure
    plt.show()
