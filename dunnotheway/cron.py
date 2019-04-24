import flight.models.fixtures
import flight.opensky.tracker as flight_tracker


if __name__ == '__main__':
    flight_tracker.track_en_route_flights()
    # flight_tracker.track_en_route_flights_by_airports('SBBR', 'SBGR', round_trip_mode=True)