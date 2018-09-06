from common.log import logger
from common.utils import from_datetime_to_timestamp, from_timestamp_to_datetime
from tracker.models.flight_location import FlightLocation


def normalize_flight_locations_into_sections(flight):
    section_points = get_flight_trajectory_section_points(flight)
    flight_locations = filter_normalized_flight_locations(flight, section_points)
    return flight_locations


def filter_normalized_flight_locations(flight, section_points):
    '''Filter flight locations for specific section points'''
    flight_locations = flight.flight_locations
    if len(flight_locations) < 2:
        return []
    
    normalized_flight_locations = []
    longitude_based = flight.longitude_based
    follow_increasing_order = section_points[-1] > section_points[0] 
    section_points_iterator = iter(section_points)
    mid_point = next(section_points_iterator)

    for prev_location, curr_location in zip(flight_locations, flight_locations[1:]):
        try:
            while check_mid_point_before_location(mid_point, prev_location, longitude_based, follow_increasing_order): 
                mid_point = next(section_points_iterator) # might raise StopIteration Exception
        except StopIteration:
            logger.error('Invalid set of flight locations {0!r} and {1!r} of flight {2!r}'.format(prev_location, curr_location, flight))
            break # leave for outer loop
     
        if check_mid_point_within_flight_locations(mid_point, prev_location, curr_location, longitude_based):
            normalized_flight_location = get_normalized_flight_location(mid_point, prev_location, curr_location, longitude_based)
            normalized_flight_locations.append(normalized_flight_location)
    
    logger.debug('Reduce {0} flight locations to {1} normalized flight locations'.format(
        len(flight_locations), len(normalized_flight_locations)))
    return normalized_flight_locations

def check_mid_point_before_location(mid_point, location, longitude_based, follow_increasing_order):
    '''Check if mid point comes before location.'''
    if longitude_based:
        base_point = float(location.longitude)
    else: # latitude based
        base_point = float(location.latitude)
    logger.debug('Check if mid_point {0} before location {1} following {2} order'.format(mid_point, base_point, ('decreasing', 'increasing')[follow_increasing_order]))
    return mid_point < base_point if follow_increasing_order else mid_point > base_point

def check_mid_point_within_flight_locations(mid_point, prev_location, curr_location, longitude_based):
    '''Check if mid point is within two flight locations (`prev_location` and `curr_location`)
    comparing either to the longitude or to the latitude of points.'''
    if longitude_based:
        start_interval, end_interval = (
            float(prev_location.longitude), float(curr_location.longitude))
    else: # latitude based
        start_interval, end_interval = (
            float(prev_location.latitude), float(curr_location.latitude))
    logger.debug('Check if mid_point {0} within interval [{1}, {2}]'.format(mid_point, start_interval, end_interval))
    return start_interval <= mid_point < end_interval or end_interval <= mid_point < start_interval

def get_normalized_flight_location(mid_point, prev_location, curr_location, longitude_based):
    '''Return normalized flight location within two flight locations (`prev_location` and `curr_location`)
    comparing either to the longitude or to the latitude of points.'''
    
    def find_mid_value(alpha, start, end):
        return start + alpha * (end-start)
    
    if longitude_based:
        longitude = mid_point
        start_interval, end_interval = float(prev_location.longitude), float(curr_location.longitude)
        alpha = (mid_point-start_interval)/(end_interval-start_interval) # DivisionByZeroError not possible 
        latitude = find_mid_value(alpha, float(prev_location.latitude), float(curr_location.latitude))
    else: # latitude based
        latitude = mid_point
        start_interval, end_interval = float(prev_location.latitude), float(curr_location.latitude)
        alpha = (mid_point-start_interval)/(end_interval-start_interval) # DivisionByZeroError not possible 
        longitude = find_mid_value(alpha, float(prev_location.longitude), float(curr_location.longitude))
    
    # altitude, speed and timestamp operations
    altitude = find_mid_value(alpha, float(prev_location.altitude), float(curr_location.altitude))
    speed = find_mid_value(alpha, float(prev_location.speed), float(curr_location.speed))
    timestamp = from_timestamp_to_datetime(
        find_mid_value(alpha, 
            from_datetime_to_timestamp(prev_location.timestamp), 
            from_datetime_to_timestamp(curr_location.timestamp)
        )
    )     
    return FlightLocation(
        timestamp=timestamp, # as datetime object
        longitude=longitude,
        latitude=latitude,
        speed=speed,
        altitude=altitude,
        flight=prev_location.flight
    )

def get_flight_trajectory_section_points(flight):
    '''Return section points related to flight trajectory'''

    def split_interval_in_section_partitions(start_interval, end_interval, partition_interval):
        points = []
        curr_interval = start_interval
        while curr_interval <= end_interval:
            points.append(curr_interval)
            curr_interval = round(curr_interval + partition_interval, 3)
        return points

    if flight.longitude_based:
        start_interval, end_interval = (
            float(flight.flight_plan.departure_airport.longitude), 
            float(flight.flight_plan.destination_airport.longitude))
    else:
        start_interval, end_interval = (
            float(flight.flight_plan.departure_airport.latitude), 
            float(flight.flight_plan.destination_airport.latitude))
    
    follow_increasing_order = start_interval < end_interval
    partition_interval = float(flight.partition_interval)
    start_interval, end_interval = sorted([start_interval, end_interval])
    partitions = split_interval_in_section_partitions(start_interval, end_interval, partition_interval)
    return partitions if follow_increasing_order else partitions[::-1]

