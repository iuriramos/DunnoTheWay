import time

from common.db import open_database_session
from common.log import logger
from weather.stsc.api import STSC
from weather.stsc.settings import (ITERATIONS_LIMIT_TO_SEARCH_CONVECTION_CELLS,
                                   SLEEP_TIME_TO_GET_CONVECTION_CELLS_IN_SECS)

# global variables
session = None


def track_convection_cells():
    '''Keep track of ALL convection cells'''
    global session 
    
    client = STSC()
    count_iterations = 0
    prev_cells = set()

    with open_database_session() as session:
        while count_iterations < ITERATIONS_LIMIT_TO_SEARCH_CONVECTION_CELLS:
            time.sleep(SLEEP_TIME_TO_GET_CONVECTION_CELLS_IN_SECS)
            if client.has_changed:
                curr_cells = client.cells
                save_convection_cells(new_cells=curr_cells-prev_cells)
                prev_cells = curr_cells
            count_iterations += 1


def save_convection_cells(new_cells):
    for cell in new_cells:
        logger.info('Save convection cell {0!r}'.format(cell))
        session.add(cell)
    session.commit()

