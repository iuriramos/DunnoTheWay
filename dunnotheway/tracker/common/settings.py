import os
import logging
from datetime import datetime

from common.settings import BASE_DIR
from sqlalchemy import create_engine
from common import settings

# Define logger object
LOGS_DIR = os.path.join(BASE_DIR, 'tracker', 'logs')
filename = datetime.today().strftime(r'%d-%m-%Y') # day-month-year
filepath = os.path.join(LOGS_DIR, filename)
LOG_FORMAT = '%(levelname)s %(asctime)s - %(message)s'
logging.basicConfig(filename=filepath, filemode='a', level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger()
    
# DunnoTheWay environment variables
POSTGRES_DATABASE_USER = settings.get_env_variable('DUNNO_POSTGRES_DATABASE_USER')
POSTGRES_DATABASE_PASSWORD = settings.get_env_variable('DUNNO_POSTGRES_DATABASE_PASSWORD')
POSTGRES_DATABASE_HOST = settings.get_env_variable('DUNNO_POSTGRES_DATABASE_HOST')
POSTGRES_DATABASE_PORT = settings.get_env_variable('DUNNO_POSTGRES_DATABASE_PORT')
POSTGRES_DATABASE_NAME = settings.get_env_variable('DUNNO_POSTGRES_DATABASE_NAME')

def create_db_engine():
    '''Return tracker database engine'''
    return settings.create_db_engine(
        POSTGRES_DATABASE_USER, 
        POSTGRES_DATABASE_PASSWORD, 
        POSTGRES_DATABASE_HOST, 
        POSTGRES_DATABASE_PORT, 
        POSTGRES_DATABASE_NAME)