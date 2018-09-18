import fire 
import tracker.models.fixtures
import tracker.opensky.agent as tracker
import analyser.sections_plot as builder

if __name__ == '__main__':
    fire.Fire({
        'track-en-route-flights': tracker.track_en_route_flights,
        'track-en-route-flight': tracker.track_en_route_flight_by_callsign,
        'track-airports': tracker.track_en_route_flights_by_airports,
        'build-airways': builder.build_airways_related_to_airports,
    })

    # tracker.track_en_route_flights_by_airports('SBBR', 'SBGR', 
    #     round_trip_mode=True, tracking_mode=True)
    # # builder.build_airways_related_to_airports('SBGR', 'SBBR')