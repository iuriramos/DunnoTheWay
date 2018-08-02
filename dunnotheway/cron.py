import tracker.models.fixtures
import tracker.opensky.agent as tracker
import builder.agent as builder

if __name__ == '__main__':
    tracker.track_flights_from_airports('BSB', 'GRU', True)
    # builder.build_airways_from_airports('GRU', 'BSB')
