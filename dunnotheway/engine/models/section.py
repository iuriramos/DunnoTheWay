from collections import defaultdict, namedtuple

from engine import normalizer
from common.log import logger
from common.db import open_database_session
from flight.models.airport import Airport

from engine.settings import NUMBER_ENTRIES_PER_SECTION


class Section:
    '''
    Section Wrapper Class
    
    Set of flight locations sharing the same latitude or longitude 
    represented by `section_point` depending on `longitude_based`.
    `label` attributes the cluster group for a specific flight location.
    '''

    # cache sections list based on 
    # (departure_airport, destination_airport, min_entries_per_section)
    cache = {} 

    def __init__(self, section_point, longitude_based, flight_locations):
        self.section_point = section_point
        self.longitude_based = longitude_based
        self.flight_locations = flight_locations

    def __repr__(self):
        return 'Section({sp})'.format(sp=self.section_point)

    def __iter__(self):
        yield from self.flight_locations

    def __len__(self):
        return len(self.flight_locations)
      
    @staticmethod
    def sections_from_airports(departure_airport, destination_airport, **kwargs):
        '''Return sections from flight locations'''
        min_entries_per_section = kwargs.get(
            'min_entries_per_section', NUMBER_ENTRIES_PER_SECTION)
            
        key = (
            departure_airport.icao_code, 
            destination_airport.icao_code, 
            min_entries_per_section,
        )

        if key not in Section.cache:
            with open_database_session() as session:
                flight_locations = normalizer.normalize_from_airports(
                    session, departure_airport, destination_airport)
            
            # section should be longitude based
            longitude_based = Airport.should_be_longitude_based(
                departure_airport, destination_airport)

            sections = []
            if not flight_locations:
                return sections
            
            prev_flight_location = flight_locations[0]
            section_flight_locations = [prev_flight_location]

            for curr_flight_location in flight_locations[1:]:
                if Section._flight_locations_are_part_of_the_same_section(
                    prev_flight_location, curr_flight_location, longitude_based):
                    section_flight_locations.append(curr_flight_location)
                else:
                    if len(section_flight_locations) >= min_entries_per_section:
                        section = Section.from_flight_locations(section_flight_locations)
                        sections.append(section)
                    section_flight_locations = [curr_flight_location]
                prev_flight_location = curr_flight_location

            Section.cache[key] = sections

        # return cached results
        return Section.cache[key]

    @staticmethod
    def from_flight_locations(flight_locations):
        '''Return a SINGLE section from flight locations'''
        fl1, fl2 = flight_locations[0], flight_locations[-1]
        longitude_based = (fl1.longitude == fl2.longitude)
        section_point = (fl1.longitude if longitude_based else fl1.latitude)
        
        return Section(
            section_point=section_point,
            longitude_based=longitude_based,
            flight_locations=flight_locations)

    @staticmethod
    def _flight_locations_are_part_of_the_same_section(this_fl, that_fl, longitude_based):
        return (this_fl.longitude == that_fl.longitude if longitude_based
            else this_fl.latitude == that_fl.latitude)