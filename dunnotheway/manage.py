import fire 
# import tracker.models.fixtures
import tracker.opensky.api as opensky_api

if __name__ == '__main__':
    # fire.Fire({
    #     'track-airplane': opensky_api.track_flight_from_callsign,
    #     'track-airports': opensky_api.track_flights_from_airports
    # })

    opensky_api.track_flights_from_airports('BSB', 'GRU', True)
    