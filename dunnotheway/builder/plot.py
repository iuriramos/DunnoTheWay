import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from .settings import logger

# global variables
SIZES = [200, 300, 400, 500, 600]
COLORS = ['red', 'blue', 'green', 'orange', 'purple', 'black']


def plot_flight_records(records, labels):
    '''Plot flight records, which is set of flight locations represented by (longitude, latitude, altitude).'''

    if not records:
        raise ValueError('records should not be empty')
    
    first_record, last_record = records[0], records[-1]
    longitude_based = first_record.longitude == last_record.longitude
    
    if longitude_based:
        x_axis = [float(record.latitude) for record in records]
    else:
        x_axis = [float(record.longitude) for record in records]

    y_axis = [float(record.altitude) for record in records]
    _, axes = plt.subplots()
    
    # plot flight path
    axes.scatter(x_axis, y_axis, c=labels, alpha=0.5)
    axes.set_title(('Longitude: ' + str(first_record.longitude)) if longitude_based else ('Latitude: ' + str(first_record.latitude)))
    axes.set_xlabel('Longitude' if longitude_based else 'Latitude')
    axes.set_ylabel('Altitude')

    plt.show()
