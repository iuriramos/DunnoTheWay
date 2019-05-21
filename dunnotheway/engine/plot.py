import itertools
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import StandardScaler

from common.db import open_database_session
from engine.models.section import Section
from flight.models.airport import Airport

from .settings import NUMBER_SECTIONS


SIZES = [200, 300, 400, 500, 600]
COLORS = ['red', 'blue', 'green', 'orange', 'purple', 'black']


def plot_sections(sections, number_sections=NUMBER_SECTIONS):
    '''Build cruising paths from departure airport to destination airport'''
    
    def sections_subset(sections):
        '''Return at most `NUMBER_SECTIONS` sections'''
        step = max(1, len(sections)//number_sections)
        return sections[::step]

    for section in sections_subset(sections):
        plot_section(section)


def plot_section(section):
    '''Plot flight records with their respective labels'''
    records, labels = section.flight_locations, section.labels
    
    if not records:
        raise ValueError('records should not be empty')
    
    first_record, last_record = records[0], records[-1]
    longitude_based = (first_record.longitude == last_record.longitude)
    
    if longitude_based:
        latitudes_longitudes = [latitude for latitude, _, __ in records]
    else:
        latitudes_longitudes = [longitude for _, longitude, __ in records]

    altitudes = [altitude for _, __, altitude in records]
    _, axis = plt.subplots()
    
    axis.set_title(
        ('Longitude: ' + str(first_record.longitude)) if longitude_based 
        else ('Latitude: ' + str(first_record.latitude)))
    axis.set_xlabel('Latitude' if longitude_based else 'Longitude')
    axis.set_ylabel('Altitude')

    # plot flight path
    axis.scatter(latitudes_longitudes, altitudes, c=labels, alpha=0.5)

    # show figure
    plt.show()
