import os
from sqlalchemy import create_engine

# DunnoTheWay environment variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_env_variable(var_name):
    '''Get the environment variable or return exception.'''
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = 'Set the {} environment variable'.format(var_name)
        raise KeyError(error_msg)

def create_db_engine(user, password, host, port, db):
    '''Return database engine from user, password, db, host and port'''
    url_pattern = 'postgresql://{user}:{password}@{host}:{port}/{db}'
    url = url_pattern.format(
        user=user, 
        password=password, 
        host=host, 
        port=port, 
        db=db)
    return create_engine(url, client_encoding='utf8')

    
    