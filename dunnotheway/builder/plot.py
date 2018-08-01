import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from .settings import logger

# global variables
SIZES = [200, 300, 400, 500, 600]
COLORS = ['red', 'blue', 'green', 'orange', 'purple', 'black']


def plot_flight_records(records, labels, centroids):
    '''Plot flight records, which is set of flight locations represented by (longitude, latitude, altitude).'''

    if not records:
        raise ValueError('records should not be empty')
    
    first_record, last_record = records[0], records[-1]
    longitude_based = first_record.longitude == last_record.longitude
    
    if longitude_based:
        longitutes_or_altitudes = [float(record.latitude) for record in records]
    else:
        longitutes_or_altitudes = [float(record.longitude) for record in records]

    altitudes = [float(record.altitude) for record in records]
    _, axis = plt.subplots()
    
    axis.set_title(
        ('Longitude: ' + str(first_record.longitude)) if longitude_based 
        else ('Latitude: ' + str(first_record.latitude)))
    axis.set_xlabel('Latitude' if longitude_based else 'Longitude')
    axis.set_ylabel('Altitude')

    # plot flight path
    axis.scatter(longitutes_or_altitudes, altitudes, c=labels, alpha=0.5)

    # plot centroids
    centroids = np.array(centroids, dtype=np.float)
    if centroids.size: # not empty
        if longitude_based:
            axis.scatter(centroids[:,1], centroids[:,2], marker='x')
        else: # latitude based
            axis.scatter(centroids[:,0], centroids[:,2], marker='x')
    
    # show figure
    plt.show()
