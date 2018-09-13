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