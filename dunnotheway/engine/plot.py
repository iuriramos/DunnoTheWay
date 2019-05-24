import os
import random
from datetime import datetime
import itertools
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import StandardScaler

from common.settings import BASE_DIR
from common.db import open_database_session
from engine.models.section import Section
from flight.models.airport import Airport

from .settings import NUMBER_SECTIONS


DATETIME_DIR_NAME, DIR_NAME, REPORTS_DIR = None, None, None
SIZES = [200, 300, 400, 500, 600]
COLORS = ['red', 'blue', 'green', 'orange', 'purple', 'black']


def plot_sections(sections, number_sections=NUMBER_SECTIONS):
    '''Build cruising paths from departure airport to destination airport'''
    global DATETIME_DIR_NAME, DIR_NAME, REPORTS_DIR
    
    DATETIME_DIR_NAME = datetime.today().strftime(r'%d-%m-%Y')
    DIR_NAME = str(random.randrange(0, 100000))
    REPORTS_DIR = os.path.join(BASE_DIR, 'results', 'reports', 
            DATETIME_DIR_NAME, DIR_NAME)
    
    def sections_subset(sections):
        '''Return at most `NUMBER_SECTIONS` sections'''
        step = max(1, len(sections)//number_sections)
        return sections[::step]

    for section in sections_subset(sections):
        plot_section(section)


def plot_section(section):
    '''Plot flight records with their respective labels'''
    flight_locations, labels = section.flight_locations, section.labels
    
    if not flight_locations:
        raise ValueError('section should not be empty')
    
    first_fl, last_fl = flight_locations[0], flight_locations[-1]
    longitude_based = (first_fl.longitude == last_fl.longitude)
    
    if longitude_based:
        latitudes_longitudes = [
            float(flight_location.latitude) for flight_location in flight_locations]
    else:
        latitudes_longitudes = [
            float(flight_location.longitude) for flight_location in flight_locations]
    altitudes = [
        float(flight_location.altitude) for flight_location in flight_locations]
    
    _, axis = plt.subplots()
    axis.set_title(
        ('Longitude: ' + str(first_fl.longitude)) if longitude_based 
        else ('Latitude: ' + str(first_fl.latitude)))
    axis.set_xlabel('Latitude' if longitude_based else 'Longitude')
    axis.set_ylabel('Altitude')

    # plot flight path
    axis.scatter(latitudes_longitudes, altitudes, c=labels, alpha=0.5)

    # save results in a figure    
    filepath = _get_filepath_from_section(section)
    plt.savefig(filepath)

def _get_filepath_from_section(section):
    '''Return file path for section report'''
    first_fl, last_fl = section.flight_locations[0], section.flight_locations[-1]
    flight_plan = first_fl.flight.flight_plan
    subdir_name =  '-'.join([
        flight_plan.departure_airport.icao_code, 
        flight_plan.destination_airport.icao_code])
    subdir_path = os.path.join(REPORTS_DIR, subdir_name)
    if not os.path.exists(subdir_path):
        os.makedirs(subdir_path)
    filename = (str(first_fl.longitude) +'_lon' if first_fl.longitude == last_fl.longitude
        else str(first_fl.latitude) + '_lat') + '.pdf'
    return os.path.join(subdir_path, filename)
