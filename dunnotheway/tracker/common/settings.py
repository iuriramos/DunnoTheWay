import os
import json
import logging
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common.settings import BASE_DIR
from common import utils

# DunnoTheWay environment variables
POSTGRES_DATABASE_USER = utils.get_env_variable('DUNNO_POSTGRES_DATABASE_USER')
POSTGRES_DATABASE_PASSWORD = utils.get_env_variable('DUNNO_POSTGRES_DATABASE_PASSWORD')
POSTGRES_DATABASE_HOST = utils.get_env_variable('DUNNO_POSTGRES_DATABASE_HOST')
POSTGRES_DATABASE_PORT = utils.get_env_variable('DUNNO_POSTGRES_DATABASE_PORT')
POSTGRES_DATABASE_NAME = utils.get_env_variable('DUNNO_POSTGRES_DATABASE_NAME')

# load config file
CONFIG_PATH = os.path.join(BASE_DIR, 'tracker', 'common', 'config.json')
with open(CONFIG_PATH) as f:
    config = json.load(f)

# config variables
OPEN_SKY_URL = 'https://opensky-network.org/api/states/all'
SLEEP_TIME_GET_FLIGHT = config['DEFAULT']['SLEEP_TIME_GET_FLIGHT'] # SECONDS
SLEEP_TIME_SEARCH_FLIGHT = config['DEFAULT']['SLEEP_TIME_SEARCH_FLIGHT'] # SECONDS
ITERATIONS_LIMIT = config['DEFAULT']['ITERATIONS_LIMIT'] # INTEGER
FLIGHT_PATH_PARTITION_INTERVAL = config['DEFAULT']['FLIGHT_PATH_PARTITION_INTERVAL'] # DEGRES 
CRUISING_VERTICAL_RATE = config['DEFAULT']['CRUISING_VERTICAL_RATE'] # METERS / SECOND


# logging
LOGS_DIR = os.path.join(BASE_DIR, 'tracker', 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

filename = datetime.today().strftime(r'%d-%m-%Y') # day-month-year
filepath = os.path.join(LOGS_DIR, filename)
LOG_FORMAT = '%(levelname)s %(asctime)s - %(message)s'

logging.basicConfig(filename=filepath, filemode='a', level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger()

# database access
def create_db_engine():
    '''Return tracker database engine'''
    return utils.create_db_engine(
        POSTGRES_DATABASE_USER, 
        POSTGRES_DATABASE_PASSWORD, 
        POSTGRES_DATABASE_HOST, 
        POSTGRES_DATABASE_PORT, 
        POSTGRES_DATABASE_NAME)

@contextmanager
def open_database_session():
    '''Context manager to handle session related to db'''
    session = Session()
    yield session
    session.close()

engine = create_db_engine()
Session = sessionmaker(bind=engine)