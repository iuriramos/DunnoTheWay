from datetime import date

from tracker.models.base import Session, engine, Base
from tracker.models.airline import Airline
from tracker.models.airport import Airport
from tracker.models.flight_plan import FlightPlan

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
bsb_airport = Airport('BSB', 'Brasília International Airport', -15.869, -47.918, 'Brazil')
gru_airport = Airport('GRU', 'São Paulo-Guarulhos International Airport', -23.426, -46.468, 'Brazil')

# create flight plans (GRU >> BSB)
azul_2925 = FlightPlan('AZUL2925', gru_airport, bsb_airport)
azul_4276 = FlightPlan('AZU4276', gru_airport, bsb_airport)
azul_4446 = FlightPlan('AZU4446', gru_airport, bsb_airport)
azul_4014 = FlightPlan('AZU4014', gru_airport, bsb_airport)
azul_9076 = FlightPlan('AZU9076', gru_airport, bsb_airport)
gol_1404 = FlightPlan('GLO1404', gru_airport, bsb_airport)
gol_1408 = FlightPlan('GLO1408', gru_airport, bsb_airport)
gol_1412 = FlightPlan('GLO1412', gru_airport, bsb_airport)
gol_1414 = FlightPlan('GLO1414', gru_airport, bsb_airport)
gol_1418 = FlightPlan('GLO1418', gru_airport, bsb_airport)
gol_9556 = FlightPlan('GLO9556', gru_airport, bsb_airport)
gol_9620 = FlightPlan('GLO9620', gru_airport, bsb_airport)
tam_3368 = FlightPlan('TAM3368', gru_airport, bsb_airport)
tam_3562 = FlightPlan('TAM3562', gru_airport, bsb_airport)
tam_3579 = FlightPlan('TAM3579', gru_airport, bsb_airport)
tam_3582 = FlightPlan('TAM3582', gru_airport, bsb_airport)
tam_4508 = FlightPlan('TAM4508', gru_airport, bsb_airport)
tam_4600 = FlightPlan('TAM4600', gru_airport, bsb_airport)
tam_4602 = FlightPlan('TAM4602', gru_airport, bsb_airport)
tam_4617 = FlightPlan('TAM4617', gru_airport, bsb_airport)
tam_4726 = FlightPlan('TAM4726', gru_airport, bsb_airport)
avianca_6188 = FlightPlan('ONE6188', gru_airport, bsb_airport)
avianca_6192 = FlightPlan('ONE6192', gru_airport, bsb_airport)
avianca_6319 = FlightPlan('ONE6319', gru_airport, bsb_airport)
avianca_9582 = FlightPlan('ONE9582', gru_airport, bsb_airport)

# create flight plans (BSB >> GRU)
tam_3228 = FlightPlan('TAM3228', bsb_airport, gru_airport)
tam_3304 = FlightPlan('TAM3304', bsb_airport, gru_airport)
tam_3575 = FlightPlan('TAM3575', bsb_airport, gru_airport)
tam_3578 = FlightPlan('TAM3578', bsb_airport, gru_airport)
tam_3991 = FlightPlan('TAM3991', bsb_airport, gru_airport)
tam_4601 = FlightPlan('TAM4601', bsb_airport, gru_airport)
tam_4603 = FlightPlan('TAM4603', bsb_airport, gru_airport)
tam_4616 = FlightPlan('TAM4616', bsb_airport, gru_airport)
tam_4631 = FlightPlan('TAM4631', bsb_airport, gru_airport)
tam_9425 = FlightPlan('TAM9425', bsb_airport, gru_airport)
azul_2539 = FlightPlan('AZUL2539', bsb_airport, gru_airport)
azul_2926 = FlightPlan('AZUL2926', bsb_airport, gru_airport)
azul_4015 = FlightPlan('AZUL4015', bsb_airport, gru_airport)
azul_4277 = FlightPlan('AZUL4277', bsb_airport, gru_airport)
azul_4493 = FlightPlan('AZUL4493', bsb_airport, gru_airport)
gol_1409 = FlightPlan('GLO1409', bsb_airport, gru_airport)
gol_1411 = FlightPlan('GLO1411', bsb_airport, gru_airport)
gol_1415 = FlightPlan('GLO1415', bsb_airport, gru_airport)
gol_1417 = FlightPlan('GLO1417', bsb_airport, gru_airport)
gol_1419 = FlightPlan('GLO1419', bsb_airport, gru_airport)
avianca_6189 = FlightPlan('ONE6189', bsb_airport, gru_airport)
avianca_6193 = FlightPlan('ONE6193', bsb_airport, gru_airport)
avianca_6318 = FlightPlan('ONE6318', bsb_airport, gru_airport)


# persist data
session.add(bsb_airport)
session.add(gru_airport)

session.add(gol_airline)
session.add(avianca_airline)
session.add(tam_airline)
session.add(azul_airline)

# commit and close session
session.commit()
session.close()