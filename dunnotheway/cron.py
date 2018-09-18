import tracker.models.fixtures
import tracker.opensky.agent as tracker
import analyser.sections_plot as builder


if __name__ == '__main__':
    # builder.build_airways_related_to_airports('SBBR', 'SBGR')
    tracker.track_en_route_flights_by_airports('SBBR', 'SBGR', 
        round_trip_mode=True, tracking_mode=True)