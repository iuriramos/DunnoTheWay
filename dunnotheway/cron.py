import flight.models.fixtures
import flight.opensky.agent as flight_tracker
import analyser.sections_plot as builder


if __name__ == '__main__':
    # flight_tracker.track_en_route_flights_by_airports('SBBR', 'SBGR', 
    #     round_trip_mode=True, tracking_mode=True)
    flight_tracker.track_en_route_flights(tracking_mode=False)