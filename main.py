
#from modulo_vendas.controller.venda_controller import VendaController

from modulo_data_analysis.controller.analytics_controller import (
    AnalyticsController
)

from database.connection import Base, engine, SessionLocal
from datetime import datetime

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

produtos = analytics.produtos_mais_vendidos()

print("\nProdutos mais vendidos:")

for produto in produtos:
    print(
        produto.descricao,
        produto.quantidade_vendida
    )

faturamento_produtos = analytics.faturamento_por_produto()

print("\nFaturamento por produto:")

for produto in faturamento_produtos:
    print(
        produto.descricao,
        produto.faturamento
    )

categorias = analytics.vendas_por_categoria()

print("\nVendas por categoria:")

for categoria in categorias:
    print(
        categoria.nome,
        categoria.quantidade_vendida
    )

marcas = analytics.vendas_por_marca()

print("\nVendas por marca:")

for marca in marcas:
    print(
        marca.nome,
        marca.quantidade_vendida
    )
produtos_estoque_baixo = analytics.estoque_baixo()

print("\nProdutos com estoque baixo:")

for produto in produtos_estoque_baixo:
    print(
        produto.descricao,
        produto.estoque
    )

data_inicio = datetime(2026, 9, 1)
data_fim = datetime(2026, 9, 30, 23, 59, 59)

vendas_periodo = analytics.vendas_por_periodo(
    data_inicio,
    data_fim
)

print("\nVendas no período:")

for venda in vendas_periodo:
    print(
        venda.id,
        venda.total,
        venda.status,
        venda.data
    )

faturamento_periodo = analytics.faturamento_por_periodo(
    data_inicio,
    data_fim
)

print(
    "\nFaturamento no período:",
    faturamento_periodo
)

produtos_sem_estoque = analytics.produtos_sem_estoque()

print("\nProdutos sem estoque:")

if produtos_sem_estoque:
    for produto in produtos_sem_estoque:
        print(
            produto.descricao,
            produto.estoque
        )
else:
    print("Nenhum produto sem estoque.")

faturamento_categorias = analytics.faturamento_por_categoria()

print("\nFaturamento por categoria:")

for categoria in faturamento_categorias:
    print(
        categoria.nome,
        categoria.faturamento
    )

faturamento_marcas = analytics.faturamento_por_marca()

print("\nFaturamento por marca:")

for marca in faturamento_marcas:
    print(
        marca.nome,
        marca.faturamento
    )

vendas_dia = analytics.vendas_por_dia()

print("\nVendas por dia:")

for dia in vendas_dia:
    print(
        dia.data,
        dia.quantidade_vendas,
        dia.faturamento
    )

faturamento_marcas = analytics.faturamento_por_marca()

print("\nFaturamento por marca:")

for marca in faturamento_marcas:
    print(
        marca.nome,
        marca.faturamento
    )

vendas_dia = analytics.vendas_por_dia()

print("\nVendas por dia:")

for dia in vendas_dia:
    print(
        dia.data,
        dia.quantidade_vendas,
        dia.faturamento
    )

session.close()