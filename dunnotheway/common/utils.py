import os
import math
import time
from datetime import datetime
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
    Also measure distance in meters between two 3-d points (latitude, longitude, altitude).
    For variables naming refer to: https://www.movable-type.co.uk/scripts/latlong.html'''
    lat1, lon1, *_rest = this_coordinate
    lat2, lon2, *_rest = that_coordinate
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    
    a = math.sin(dlat/2)**2 + (
        math.cos(lat1) * math.cos(lat2) * (math.sin(dlon/2)**2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = RADIUS_EARTH * c
    return d


def distance_three_dimensions_coordinates(this_coordinate, that_coordinate):
    '''Measure distance in meters between two 3-d points (latitude, longitude, altitude).
    For variables naming refer to: https://www.movable-type.co.uk/scripts/latlong.html'''
    this_rect_coordinate = get_cartesian_coordinates(this_coordinate)
    that_rect_coordinate = get_cartesian_coordinates(that_coordinate)
    distance = np.linalg.norm(
        np.array(this_rect_coordinate)-np.array(that_rect_coordinate))
    return distance

def get_cartesian_coordinates(coordinate):
    '''Convert spherical coordinates to cartesian coordinates'''
    lat, lon, alt = coordinate
    lat, lon = math.radians(lat), math.radians(lon)
    alt += RADIUS_EARTH
    x = alt * math.sin(lon) * math.cos(lat) 
    y = alt * math.cos(lon) * math.cos(lat)
    z = alt * math.sin(lat)
    return x, y, z

def get_spherical_coordinates(coordinate):
    '''Convert cartesian coordinates to spherical coordinates'''
    x, y, z = coordinate
    alt = np.linalg.norm([x, y, z])
    lat = math.acos(z/alt)
    lon = math.atan2(y, x)
    alt -= RADIUS_EARTH
    return lat, lon, alt

def from_datetime_to_timestamp(dt):
    '''Convert datetime object in timestamp'''
    return time.mktime(dt.timetuple())

def from_timestamp_to_datetime(ts):
    '''Convert timestamp in datetime object'''
    return datetime.fromtimestamp(ts)