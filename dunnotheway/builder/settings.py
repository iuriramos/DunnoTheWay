import os
import json
import logging
import time
from datetime import datetime

from common.settings import BASE_DIR

# load config file
CONFIG_PATH = os.path.join(BASE_DIR, 'builder', 'config.json')
with open(CONFIG_PATH) as f:
    config = json.load(f)

NUMBER_ENTRIES_PER_GROUP = config['NUMBER_ENTRIES_PER_GROUP'] # NUMBER OF POINTS PER GROUPS 
NUMBER_GROUPS = config['NUMBER_GROUPS'] # NUMBER OF GROUPS TO BUILD REPORT

DBSCAN_NUMBER_SAMPLES_CLUSTER = config['DBSCAN']["NUMBER_SAMPLES_CLUSTER"]
DBSCAN_MAXIMUM_DISTANCE = config['DBSCAN']["MAXIMUM_DISTANCE"]
DBSCAN_PERCENTAGE_NOISE = config['DBSCAN']["PERCENTAGE_NOISE"]

# logging
LOGS_DIR = os.path.join(BASE_DIR, 'builder', 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

filename = datetime.today().strftime(r'%d-%m-%Y') # day-month-year
filepath = os.path.join(LOGS_DIR, filename)
LOG_FORMAT = '%(levelname)s %(asctime)s - %(message)s'

logging.basicConfig(filename=filepath, filemode='a', level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger()