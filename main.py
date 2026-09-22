
#from modulo_vendas.controller.venda_controller import VendaController

from modulo_data_analysis.controller.analytics_controller import (
    AnalyticsController
)

from database.connection import Base, engine, SessionLocal


Base.metadata.create_all(bind=engine)

session = SessionLocal()

analytics = AnalyticsController(session)

indicadores = analytics.obter_indicadores()

print(
    "Faturamento total:",
    indicadores.faturamento_total
)

print(
    "Quantidade de vendas:",
    indicadores.quantidade_vendas
)

print(
    "Ticket médio:",
    indicadores.ticket_medio
)

session.close()