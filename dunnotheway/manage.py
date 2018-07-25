import fire 
import tracker.models.fixtures
import tracker.opensky.agent as tracker
import builder.agent as builder

if __name__ == '__main__':
    fire.Fire({
        'track-airplane': tracker.track_flight_from_callsign,
        'track-airports': tracker.track_flights_from_airports,
        'build-airways': builder.build_airways_from_airports,
    })

    # tracker.track_flights_from_airports('BSB', 'GRU', True)
    # builder.build_airways_from_airports('GRU', 'BSB')