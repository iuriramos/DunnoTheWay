import logging
import os
from datetime import datetime

from common.settings import BASE_DIR


# logging
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

filename = datetime.today().strftime(r'%d-%m-%Y') # day-month-year
filepath = os.path.join(LOGS_DIR, filename)
LOG_FORMAT = '%(levelname)s %(asctime)s - %(message)s'

logging.basicConfig(filename=filepath, filemode='a', level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger('sqlalchemy.engine')