from datetime import date
from sqlalchemy import inspect

from common.db import Base, Session, engine
from flight.models.airline import Airline
from flight.models.airplane import Airplane
from flight.models.airport import Airport
from flight.models.flight import Flight
from flight.models.flight_location import FlightLocation
from flight.models.flight_plan import FlightPlan
from weather.models.convection_cell import ConvectionCell

from flight.crawlers._openflights.airports import fetch_airports_information
from flight.crawlers._flightaware.flight_plans import fetch_flight_plans


def setup_environment():
    '''Setup database environment'''
    fetch_airline_companies()
    fetch_airports_information()
    fetch_flight_plans()

def fetch_airline_companies():
    session = Session()
    # crete airlines
    gol_airline = Airline('GLO', 'Gol Transportes Aéreos', 'Brazil')
    avianca_airline = Airline('ONE', 'Avianca Brazil', 'Brazil')
    tam_airline = Airline('TAM', 'TAM', 'Brazil')
    azul_airline = Airline('AZU', 'Azul Linhas Aéreas Brasileiras', 'Brazil')
    # persist data
    session.add(gol_airline)
    session.add(avianca_airline)
    session.add(tam_airline)
    session.add(azul_airline)
    # commit and close session
    session.commit()
    session.close()


# create database tables
Base.metadata.create_all(engine)

# TODO (notworking): check if table names exists via inspect
ins = inspect(engine)
if not ins.get_table_names():
    setup_environment()