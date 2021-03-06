import fire 
import flight.models.fixtures
import flight.opensky.tracker as flight_tracker
import weather.stsc.tracker as weather_tracker
from engine import detector


if __name__ == '__main__':
    fire.Fire({
        # offline methods
        'track-en-route-flights': flight_tracker.track_en_route_flights,
        'track-airports': flight_tracker.track_en_route_flights_by_airports,
        'track-convection-cells': weather_tracker.track_convection_cells,
        
        # online methods
        'search-intersections-convection-cells': detector.search_intersections_convection_cells,
        # 'search-flight-deviations': flight_tracker.search_flight_deviations,
    })

    # flight_tracker.track_en_route_flights_by_airports('SBBR', 'SBGR', 
    #     round_trip_mode=True, tracking_mode=True)
    