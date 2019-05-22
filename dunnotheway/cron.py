import flight.models.fixtures
import flight.opensky.tracker as flight_tracker
from engine.detector import search_intersections_convection_cells 


if __name__ == '__main__':
    # flight_tracker.track_en_route_flights()
    airport_tracking_list = [
        ('SBBR', 'SBGL'),
        ('SBBR', 'SBRJ'),
        ('SBBR', 'SBSP'),
        ('SBBR', 'SBGR'),
        
        ('SBGL', 'SBBR'),
        ('SBRJ', 'SBBR'),
        ('SBSP', 'SBBR'),
        ('SBGR', 'SBBR'),
        
        ('SBGL', 'SBSP'),
        ('SBGL', 'SBGR'),
        ('SBSP', 'SBGL'),
        ('SBGR', 'SBGL'),

        ('SBRJ', 'SBSP'),
        ('SBRJ', 'SBGR'),
        ('SBSP', 'SBRJ'),
        ('SBGR', 'SBRJ'),
    ]
    search_intersections_convection_cells(
        airport_tracking_list=airport_tracking_list,
        min_entries_per_section=20, 
        min_number_samples=1, 
        max_distance_between_samples=1000)
    # # flight_tracker.track_en_route_flights_by_airports('SBBR', 'SBGR', round_trip_mode=True)