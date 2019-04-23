import tracker.models.fixtures
import tracker.opensky.agent as tracker
import analyser.sections_plot as builder


if __name__ == '__main__':
    # tracker.track_en_route_flights_by_airports('SBBR', 'SBGR', 
    #     round_trip_mode=True, tracking_mode=True)
    tracker.track_en_route_flights(tracking_mode=False)