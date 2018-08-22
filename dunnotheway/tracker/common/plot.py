import os
import random
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

from common.settings import BASE_DIR
from tracker.common.settings import logger

    
def create_report(flight): 
    '''Create report from flight (flight location, speed, vertical_rate)'''
    logger.info('Create report for flight {0!r}'.format(flight))
    plot_flight_path(flight)    
    plot_flight_location_params(flight)

def plot_flight_path(flight):
    '''Plot flight locations (longitude, latitude) path from departure airport to destination airport'''
    flight_locations = flight.flight_locations
    longitudes = [float(flight_location.longitude) for flight_location in flight_locations]
    latitudes = [float(flight_location.latitude) for flight_location in flight_locations]
    _, axes = plt.subplots()
    
    # plot flight path
    axes.scatter(longitudes, latitudes)
    axes.set_title('Longitudes vs Latitudes')
    axes.set_xlabel('Longitude')
    axes.set_ylabel('Latitude')

    filepath = get_reports_filepath(flight) + '_path.pdf'
    plt.savefig(filepath)

def plot_flight_location_params(flight):
    '''Plot flight locations parameters'''
    flight_locations = flight.flight_locations
    _, axes = plt.subplots(nrows=2, ncols=1)
    axis_altitude, axis_speed = axes

    # plot flight location params
    plot_flight_location_altitudes(flight_locations, axis_altitude)
    plot_flight_location_speeds(flight_locations, axis_speed)
    
    filepath = get_reports_filepath(flight) + '_params.pdf'
    plt.savefig(filepath)

def get_reports_filepath(flight):
    '''Return file path of the flight report'''
    REPORTS_DIR = os.path.join(BASE_DIR, 'tracker', 'reports')
    subdir_name = flight.flight_plan.departure_airport.icao_code + '-' + flight.flight_plan.destination_airport.icao_code
    REPORTS_SUBDIR = os.path.join(REPORTS_DIR, subdir_name)
    if not os.path.exists(REPORTS_SUBDIR):
        os.makedirs(REPORTS_SUBDIR)
    filename = str(flight.id)
    return os.path.join(REPORTS_SUBDIR, filename)

def plot_flight_location_speeds(flight_locations, axis):
    speeds = [float(flight_location.speed) for flight_location in flight_locations]
    axis.plot(speeds)
    axis.set_title('Cruising Speed')

def plot_flight_location_altitudes(flight_locations, axis):
    altitudes = [float(flight_location.altitude) for flight_location in flight_locations]
    axis.plot(altitudes)
    axis.set_title('Barometric Altitudes')

