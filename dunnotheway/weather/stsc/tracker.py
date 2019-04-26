import time

from common.db import open_database_session
from common.log import logger

from weather.stsc.settings import SLEEP_TIME_TO_GET_CONVECTION_CELLS_IN_SECS

from weather.stsc.api import STSC
# global variables
session = None


def track_convection_cells():
    '''Keep track of ALL convection cells'''
    global session 

    client = STSC()
    with open_database_session() as session:
        time.sleep(SLEEP_TIME_TO_GET_CONVECTION_CELLS_IN_SECS)
        if client.has_changed:
            cells = client.cells
            save_convection_cells(cells)


def save_convection_cells(cells):
    for cell in cells:
        logger.info('Save convection cell {0!r}'.format(cell))
        session.add(cell)
    session.commit()

def search_intersections_convection_cells():
    # TODO: move to analyser folder, construct method
    pass