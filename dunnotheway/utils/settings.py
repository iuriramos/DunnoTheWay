import os
from sqlalchemy import create_engine

def get_env_variable(var_name):
    '''Get the environment variable or return exception.'''
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = 'Set the {} environment variable'.format(var_name)
        raise KeyError(error_msg)

# DunnoTheWay environment variables
POSTGRES_DATABASE_USER = get_env_variable('DUNNO_POSTGRES_DATABASE_USER')
POSTGRES_DATABASE_PASSWORD = get_env_variable('DUNNO_POSTGRES_DATABASE_PASSWORD')
POSTGRES_DATABASE_NAME = get_env_variable('DUNNO_POSTGRES_DATABASE_NAME')
POSTGRES_DATABASE_HOST = get_env_variable('DUNNO_POSTGRES_DATABASE_HOST')
POSTGRES_DATABASE_PORT = get_env_variable('DUNNO_POSTGRES_DATABASE_PORT')

def create_db_engine():
    '''Return database engine from user, password, db, host and port'''
    url_pattern = 'postgresql://{user}:{password}@{host}:{port}/{db}'
    url = url_pattern.format(
        user=POSTGRES_DATABASE_USER, 
        password=POSTGRES_DATABASE_PASSWORD, 
        host=POSTGRES_DATABASE_HOST, 
        port=POSTGRES_DATABASE_PORT, 
        db=POSTGRES_DATABASE_NAME)
    return create_engine(url, client_encoding='utf8')
    

    