from datetime import date
from sqlalchemy import inspect

from tracker.models.base import Session, engine, Base
from tracker.models.airline import Airline
from tracker.models.airport import Airport
from tracker.models.airplane import Airplane
from tracker.models.flight import Flight
from tracker.models.flight_plan import FlightPlan
from tracker.models.flight_location import FlightLocation


def setup_environment():
    '''Setup database environment'''

    # all tables are deleted
    Base.metadata.drop_all(engine)   

    # generate database schema
    Base.metadata.create_all(engine)

    # create a new session
    session = Session()

    # crete airlines
    gol_airline = Airline('GLO', 'Gol Transportes Aéreos', 'Brazil')
    avianca_airline = Airline('ONE', 'Avianca Brazil', 'Brazil')
    tam_airline = Airline('TAM', 'TAM', 'Brazil')
    azul_airline = Airline('AZU', 'Azul Linhas Aéreas Brasileiras', 'Brazil')

    # create airports
    BSB_airport = Airport('BSB', 'Brasília International Airport', -15.869, -47.918, 'Brazil')
    GRU_airport = Airport('GRU', 'São Paulo-Guarulhos International Airport', -23.426, -46.468, 'Brazil')
    SDU_airport = Airport('SDU', 'Santos Dumont Airport', -22.906,  -43.158, 'Brazil')
    CGH_airport = Airport('CGH', 'São Paulo-Congonhas Airport', -23.623, -46.652, 'Brazil')

    # create flight plans (GRU >> BSB)
    azul_2925 = FlightPlan('AZUL2925', GRU_airport, BSB_airport)
    azul_4276 = FlightPlan('AZU4276', GRU_airport, BSB_airport)
    azul_4446 = FlightPlan('AZU4446', GRU_airport, BSB_airport)
    azul_4014 = FlightPlan('AZU4014', GRU_airport, BSB_airport)
    azul_9076 = FlightPlan('AZU9076', GRU_airport, BSB_airport)
    gol_1404 = FlightPlan('GLO1404', GRU_airport, BSB_airport)
    gol_1408 = FlightPlan('GLO1408', GRU_airport, BSB_airport)
    gol_1412 = FlightPlan('GLO1412', GRU_airport, BSB_airport)
    gol_1414 = FlightPlan('GLO1414', GRU_airport, BSB_airport)
    gol_1418 = FlightPlan('GLO1418', GRU_airport, BSB_airport)
    gol_9556 = FlightPlan('GLO9556', GRU_airport, BSB_airport)
    gol_9620 = FlightPlan('GLO9620', GRU_airport, BSB_airport)
    tam_3368 = FlightPlan('TAM3368', GRU_airport, BSB_airport)
    tam_3562 = FlightPlan('TAM3562', GRU_airport, BSB_airport)
    tam_3579 = FlightPlan('TAM3579', GRU_airport, BSB_airport)
    tam_3582 = FlightPlan('TAM3582', GRU_airport, BSB_airport)
    tam_4508 = FlightPlan('TAM4508', GRU_airport, BSB_airport)
    tam_4600 = FlightPlan('TAM4600', GRU_airport, BSB_airport)
    tam_4602 = FlightPlan('TAM4602', GRU_airport, BSB_airport)
    tam_4617 = FlightPlan('TAM4617', GRU_airport, BSB_airport)
    tam_4726 = FlightPlan('TAM4726', GRU_airport, BSB_airport)
    avianca_6188 = FlightPlan('ONE6188', GRU_airport, BSB_airport)
    avianca_6192 = FlightPlan('ONE6192', GRU_airport, BSB_airport)
    avianca_6319 = FlightPlan('ONE6319', GRU_airport, BSB_airport)
    avianca_9582 = FlightPlan('ONE9582', GRU_airport, BSB_airport)

    # create flight plans (BSB >> GRU)
    tam_3228 = FlightPlan('TAM3228', BSB_airport, GRU_airport)
    tam_3304 = FlightPlan('TAM3304', BSB_airport, GRU_airport)
    tam_3575 = FlightPlan('TAM3575', BSB_airport, GRU_airport)
    tam_3578 = FlightPlan('TAM3578', BSB_airport, GRU_airport)
    tam_3991 = FlightPlan('TAM3991', BSB_airport, GRU_airport)
    tam_4601 = FlightPlan('TAM4601', BSB_airport, GRU_airport)
    tam_4603 = FlightPlan('TAM4603', BSB_airport, GRU_airport)
    tam_4616 = FlightPlan('TAM4616', BSB_airport, GRU_airport)
    tam_4631 = FlightPlan('TAM4631', BSB_airport, GRU_airport)
    tam_9425 = FlightPlan('TAM9425', BSB_airport, GRU_airport)
    azul_2539 = FlightPlan('AZUL2539', BSB_airport, GRU_airport)
    azul_2926 = FlightPlan('AZUL2926', BSB_airport, GRU_airport)
    azul_4015 = FlightPlan('AZUL4015', BSB_airport, GRU_airport)
    azul_4277 = FlightPlan('AZUL4277', BSB_airport, GRU_airport)
    azul_4493 = FlightPlan('AZUL4493', BSB_airport, GRU_airport)
    gol_1409 = FlightPlan('GLO1409', BSB_airport, GRU_airport)
    gol_1411 = FlightPlan('GLO1411', BSB_airport, GRU_airport)
    gol_1415 = FlightPlan('GLO1415', BSB_airport, GRU_airport)
    gol_1417 = FlightPlan('GLO1417', BSB_airport, GRU_airport)
    gol_1419 = FlightPlan('GLO1419', BSB_airport, GRU_airport)
    avianca_6189 = FlightPlan('ONE6189', BSB_airport, GRU_airport)
    avianca_6193 = FlightPlan('ONE6193', BSB_airport, GRU_airport)
    avianca_6318 = FlightPlan('ONE6318', BSB_airport, GRU_airport)

    # create flight plans (BSB >> SDU)
    avianca_6235 = FlightPlan('ONE6235', BSB_airport, SDU_airport)

    # create flight plans (BSB >> CGH)
    gol_1595 = FlightPlan('GLO1595', BSB_airport, CGH_airport) 

    # create flight plans (CGH >> SDU)
    TAM_3944 = FlightPlan('TAM3944', CGH_airport, SDU_airport) 


    # persist data
    session.add(BSB_airport)
    session.add(GRU_airport)
    session.add(SDU_airport)
    session.add(CGH_airport)

    session.add(gol_airline)
    session.add(avianca_airline)
    session.add(tam_airline)
    session.add(azul_airline)

    # commit and close session
    session.commit()
    session.close()


# check if table names exists via inspect
ins = inspect(engine)
if not ins.get_table_names():
    setup_environment()
