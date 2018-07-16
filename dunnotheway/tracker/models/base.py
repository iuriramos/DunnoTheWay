from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tracker.common.settings import create_db_engine

engine = create_db_engine()
Session = sessionmaker(bind=engine)
Base = declarative_base()