from collections import namedtuple
from tracker.opensky.settings import (MAX_LATITUDE_BRAZILIAN_AIRSPACE,
                                      MAX_LONGITUDE_BRAZILIAN_AIRSPACE,
                                      MIN_LATITUDE_BRAZILIAN_AIRSPACE,
                                      MIN_LONGITUDE_BRAZILIAN_AIRSPACE)


BoundingBox = namedtuple(
    'BoundingBox', ['min_latitude', 'max_latitude', 'min_longitude', 'max_longitude'])


def brazilian_airspace_bounding_box():
    bbox = BoundingBox(
        MIN_LATITUDE_BRAZILIAN_AIRSPACE,
        MAX_LATITUDE_BRAZILIAN_AIRSPACE,
        MIN_LONGITUDE_BRAZILIAN_AIRSPACE,
        MAX_LONGITUDE_BRAZILIAN_AIRSPACE)
    return bbox

def bounding_box_related_to_airports(departure_airport, destination_airport):
    '''
    Return bounding box (min latitude, max latitude, min longitude, max longitude)
    from departure airport to destination airport
    '''
    return BoundingBox(
        float(min(departure_airport.latitude, destination_airport.latitude)), 
        float(max(departure_airport.latitude, destination_airport.latitude)),
        float(min(departure_airport.longitude, destination_airport.longitude)), 
        float(max(departure_airport.longitude, destination_airport.longitude)))