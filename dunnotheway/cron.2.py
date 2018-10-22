import tracker.models.fixtures
import tracker.opensky.agent as tracker
import analyser.sections_plot as builder


if __name__ == '__main__':
    tracker.track_en_route_flights(tracking_mode=False)