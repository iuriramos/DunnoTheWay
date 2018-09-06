from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from common import utils


# DunnoTheWay environment variables
POSTGRES_DATABASE_USER = utils.get_env_variable('DUNNO_POSTGRES_DATABASE_USER')
POSTGRES_DATABASE_PASSWORD = utils.get_env_variable('DUNNO_POSTGRES_DATABASE_PASSWORD')
POSTGRES_DATABASE_HOST = utils.get_env_variable('DUNNO_POSTGRES_DATABASE_HOST')
POSTGRES_DATABASE_PORT = utils.get_env_variable('DUNNO_POSTGRES_DATABASE_PORT')
POSTGRES_DATABASE_NAME = utils.get_env_variable('DUNNO_POSTGRES_DATABASE_NAME')

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
Base = declarative_base()