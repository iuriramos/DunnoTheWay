import os
import sqlalchemy

def get_env_variable(var_name):
    """Get the environment variable or return exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = 'Set the {} environment variable'.format(var_name)
        raise KeyError(error_msg)

def connect_db(user, password, db, host='localhost', port=5432):
    '''Returns a connection and a metadata object'''
    # We connect with the help of the PostgreSQL URL
    url_pattern = 'postgresql://{}:{}@{}:{}/{}'
    # postgresql://federer:grandestslam@localhost:5432/tennis
    url = url_pattern.format(user, password, host, port, db)

    # The return value of create_engine() is our connection object
    con = sqlalchemy.create_engine(url, client_encoding='utf8')
    # We then bind the connection to MetaData()
    meta = sqlalchemy.MetaData(bind=con, reflect=True)

    return con, meta

# DunnoTheWay environment variables
POSTGRES_USER = get_env_variable('DUNNO_POSTGRES_USER')
POSTGRES_PASSWORD = get_env_variable('DUNNO_POSTGRES_PASSWORD')
POSTGRES_DATABASE = get_env_variable('DUNNO_POSTGRES_DATABASE')

connection, meta = connect_db(POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DATABASE)
