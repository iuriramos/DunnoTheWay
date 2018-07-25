import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from .settings import logger

# global variables
SIZES = [200, 300, 400, 500, 600]
COLORS = ['red', 'blue', 'green', 'black']

def plot_flight_section(section):
    '''Plot flight section (set of flight locations)'''

    if not section:
        raise ValueError('section should not be empty')
    
    flight_locations, flight_location = section, section[0]
    longitude_based = flight_location.flight.longitude_based
    
    if longitude_based:
        x_axis = [float(flight_location.latitude) for flight_location in flight_locations]
    else:
        x_axis = [float(flight_location.longitude) for flight_location in flight_locations]

    y_axis = [float(flight_location.altitude) for flight_location in flight_locations]
    _, axes = plt.subplots()
    
    # x_axis, y_axis = StandardScaler().fit_transform([x_axis, y_axis])

    # plot flight path
    axes.scatter(x_axis, y_axis, c=COLORS, s=SIZES, alpha=0.5)
    axes.set_title('Longitude: ' + str(flight_location.longitude) if longitude_based else 'Latitude: ' + str(flight_location.latitude))
    axes.set_xlabel('Longitude' if longitude_based else 'Latitude')
    axes.set_ylabel('Altitude')

    plt.show()
