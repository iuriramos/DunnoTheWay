from collections import defaultdict


class Intersection:
    '''
    Class representing the intersection between a `convection cell` 
    and airways connecting `departure_airport` and `destination_airport`.
    '''

    def __init__(self, convection_cell, departure_airport, destination_airport, impact):
        self.convection_cell = convection_cell
        self.departure_airport = departure_airport
        self.destination_airport = destination_airport
        self.impact = impact

    def __iter__(self):
        yield self.convection_cell 
        yield self.departure_airport 
        yield self.destination_airport 
        yield self.impact
    

class IntersectionManager:
    '''
    Class responsible for organizing the intersection between a `convection cell` 
    and airways connecting `departure_airport` and `destination_airport`.
    '''

    def __init__(self):
        self.airports_to_intersections = defaultdict(list)
        # # convection cell might impact in more than one airway at the same time
        # self.convection_cells_to_airways = defaultdict(list)

    def __iter__(self):
        yield from self.airports_to_intersections

    def items(self):
        yield from self.airports_to_intersections.items()

    def set_default_airports(self, departure_airport, destination_airport):
        key = departure_airport, destination_airport
        if key not in self.airports_to_intersections:
            self.airports_to_intersections[key] = list()

    def set_intersection(self, intersection):
        key = intersection.departure_airport, intersection.destination_airport
        self.airports_to_intersections[key].append(intersection)

    def get_intersections(self, departure_airport, destination_airport):
        return self.airports_to_intersections[
            departure_airport, destination_airport]