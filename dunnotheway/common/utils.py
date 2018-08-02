import os
import math

import numpy as np
from sqlalchemy import create_engine

# global variable
RADIUS_EARTH = 6371e3

def get_env_variable(var_name):
    '''Get the environment variable or return exception.'''
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = 'Set the {} environment variable'.format(var_name)
        raise KeyError(error_msg)

def create_db_engine(user, password, host, port, db):
    '''Return database engine from user, password, db, host and port'''
    url_pattern = 'postgresql://{user}:{password}@{host}:{port}/{db}'
    url = url_pattern.format(
        user=user, 
        password=password, 
        host=host, 
        port=port, 
        db=db)
    return create_engine(url, client_encoding='utf8')


def distance_two_dimensions_coordinates(this_coordinate, that_coordinate):
    '''Measure distance in meters between two 2-d points (latitude, longitude).
    For variables naming refer to: https://www.movable-type.co.uk/scripts/latlong.html'''
    lat1, lon1 = this_coordinate
    lat2, lon2 = that_coordinate
    l1, l2 = np.radians(lat1), np.radians(lat2)
    dlat, dlon = np.radians(lat2-lat1), np.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(l1) * math.cos(l2) * (math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = RADIUS_EARTH * c
    return distance

def distance_three_dimensions_coordinates(this_coordinate, that_coordinate):
    '''Measure distance in meters between two 3-d points (latitude, longitude, altitude).
    For variables naming refer to: https://www.movable-type.co.uk/scripts/latlong.html'''
    this_rect_coordinate = get_rect_coordinates(this_coordinate)
    that_rect_coordinate = get_rect_coordinates(that_coordinate)
    distance = np.linalg.norm(
        np.array(this_rect_coordinate)-np.array(that_rect_coordinate))
    return distance

def get_rect_coordinates(coordinate):
    '''Convert polar coordinates to rectagular'''
    lat, lon, alt = coordinate
    lat, lon = np.radians(lat), np.radians(lon)
    alt += RADIUS_EARTH
    x = alt * math.sin(lon) * math.cos(lat) 
    y = alt * math.cos(lon) * math.cos(lat)
    z = alt * math.sin(lat)
    return x, y, z