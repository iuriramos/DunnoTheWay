import fire 
import tracker.models.fixtures
import tracker.opensky.agent as tracker
import detector.sections_plot as builder

if __name__ == '__main__':
    fire.Fire({
        'track-en-route-flights': tracker.track_en_route_flights,
        'track-en-route-flight': tracker.track_en_route_flight_by_callsign,
        'track-airports': tracker.track_en_route_flights_by_airports,
        'build-airways': builder.build_airways_related_to_airports,
    })

    # tracker.track_flights_from_airports('BSB', 'GRU', True)
    # builder.build_airways_related_to_airports('GRU', 'BSB')