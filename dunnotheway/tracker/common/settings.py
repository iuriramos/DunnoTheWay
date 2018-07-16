import os
from sqlalchemy import create_engine
from common import settings

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