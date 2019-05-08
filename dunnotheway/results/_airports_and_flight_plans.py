from collections import Counter
from common.db import open_database_session
from flight.models.airport import Airport
from flight.models.flight_plan import FlightPlan

def main():

    def transform_to_portuguese(airport_name):
        if airport_name.endswith('International Airport'):
            return 'Aeroporto Internacional {}'.format(
                    airport_name.strip(' International Airport'))
        if airport_name.endswith('Airport'):
            return 'Aeroporto {}'.format(
                    airport_name.strip(' Airport'))

    with open_database_session() as session:
        airports = session.query(Airport).all()
        airports_str = ', '.join(['{} ({})'.format(
                transform_to_portuguese(a.name), a.icao_code) for a in airports])
        print (airports_str)
        print (len(airports))
        print ('-' * 100)

        flight_plans = session.query(FlightPlan).all()
        counter = Counter()
        for flight_plan in flight_plans:
            company = flight_plan.callsign[:3]
            counter[company] += 1
        
        print (counter.most_common())
        print (len(flight_plans))


if __name__ == '__main__':
    main()