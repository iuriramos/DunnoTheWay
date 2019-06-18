import os
import random
from datetime import datetime
import itertools
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import StandardScaler

from common.db import open_database_session
from engine.models.section import Section
from flight.models.airport import Airport


COLORS = ['red', 'blue', 'green', 'purple', 'black']
ALPHAS = [.8, .6, .4, 1., 1.]


def plot_sections(filepath, sections, step=1):
    '''Build cruising paths from departure airport to destination airport'''
    for section in sections[::step]:
        plot_section(filepath, section)


def plot_section(filepath, section):
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
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    
    if longitude_based:
        filename = str(first_fl.longitude)
    else:
        filename = str(first_fl.latitude)
    
    filepath = os.path.join(filepath, filename + '.pdf')
    plt.savefig(filepath)


def plot_from_flight_locations(filepath, flight_locations, **kwargs):
    '''Plot flight locations (longitude, latitude) path from departure airport to destination airport'''
    plot_from_multiple_flight_locations(filepath, [flight_locations], **kwargs)


def plot_from_multiple_flight_locations(filepath, multiple_flight_locations, **kwargs):
    _, axis = plt.subplots()
    axis.set_title('Longitudes x Latitudes')
    axis.set_xlabel('Longitude')
    axis.set_ylabel('Latitude')

    for i, flight_locations in enumerate(multiple_flight_locations):
        lons = [float(lon) for lat, lon, _ in flight_locations]
        lats = [float(lat) for lat, lon, _ in flight_locations]
        axis.scatter(
            lons, lats, c=COLORS[i], alpha=ALPHAS[i])

    departure_airport, destination_airport = (
        kwargs.get('departure_airport', None), kwargs.get('destination_airport', None))
    if departure_airport and destination_airport:
        axis.scatter(
            [float(departure_airport.longitude)], [float(departure_airport.latitude)], 
            marker='>', s=100, c=COLORS[-1], alpha=ALPHAS[-1])
        axis.scatter(
            [float(destination_airport.longitude)], [float(destination_airport.latitude)], 
            marker='<', s=100, c=COLORS[-1], alpha=ALPHAS[-1])

    airports = kwargs.get('airports', [])
    axis.scatter(
        [float(airport.longitude) for airport in airports], 
        [float(airport.latitude) for airport in airports], 
        marker='>', s=100, c=COLORS[-1], alpha=ALPHAS[-1])
    
    airways_locations = kwargs.get('airways_locations', None)
    if airways_locations:
        lons = [float(lon) for lat, lon, _ in airways_locations]
        lats = [float(lat) for lat, lon, _ in airways_locations]
        axis.scatter(
            lons, lats, c=COLORS[-1], alpha=ALPHAS[-1])

    # save flight paths figure
    plt.savefig(filepath)

def plot_flight_locations_params(filepath, flight_locations):
    '''Plot flight locations parameters'''
    plot_multiple_flight_locations_params(filepath, [flight_locations])

def plot_multiple_flight_locations_params(filepath, multiple_flight_locations):
    '''Plot flight locations parameters'''
    _, axes = plt.subplots(nrows=2, ncols=1, figsize=(10, 14))
    axis_altitude, axis_speed = axes
    
    axis_altitude.set_ylabel('Altitude')
    axis_altitude.set_title('Altitudes (em metros)')
    axis_altitude.get_xaxis().set_ticks([])
    axis_speed.set_title('Velocidades (em km/h)')
    axis_speed.set_ylabel('Velocidade')
    axis_speed.get_xaxis().set_ticks([])

    min_xlim_altitude, max_xlim_altitude = datetime.max, datetime.min
    min_xlim_speed, max_xlim_speed = datetime.max, datetime.min

    for index, flight_locations in enumerate(multiple_flight_locations):
        # plot flight location params
        curr_min_xlim_altitude, curr_max_xlim_altitude = (
            plot_flight_location_altitudes(flight_locations, axis_altitude, index=index))
        min_xlim_altitude, max_xlim_altitude = (
            min(min_xlim_altitude, curr_min_xlim_altitude), 
            max(max_xlim_altitude, curr_max_xlim_altitude))
        curr_min_xlim_speed, curr_max_xlim_speed = (
            plot_flight_location_speeds(flight_locations, axis_speed, index=index))
        min_xlim_speed, max_xlim_speed = (
            min(min_xlim_speed, curr_min_xlim_speed), 
            max(max_xlim_speed, curr_max_xlim_speed))
        
    axis_altitude.set_xlim((min_xlim_altitude, max_xlim_altitude))
    axis_speed.set_xlim((min_xlim_speed, max_xlim_speed))
    
    plt.savefig(filepath)

def plot_flight_location_altitudes(flight_locations, axis, index=0):
    timestamps = [flight_location.timestamp for flight_location in flight_locations]
    altitudes = [float(flight_location.altitude) for flight_location in flight_locations]
    axis.scatter(timestamps, altitudes, c=COLORS[index], alpha=ALPHAS[index])
    return min(timestamps), max(timestamps)

def plot_flight_location_speeds(flight_locations, axis, index=0):
    timestamps = [flight_location.timestamp for flight_location in flight_locations]
    speeds = [float(flight_location.speed) for flight_location in flight_locations]
    axis.scatter(timestamps, speeds, c=COLORS[index], alpha=ALPHAS[index])
    return min(timestamps, default=datetime.max), max(timestamps, default=datetime.min)