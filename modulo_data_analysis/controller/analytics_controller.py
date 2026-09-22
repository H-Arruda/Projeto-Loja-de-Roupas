from sqlalchemy import func

from modulo_data_analysis.model.indicadores_vendas import IndicadoresVendas
from modulo_vendas.model.venda import Venda, StatusVenda


class AnalyticsController:
    def __init__(self, session):
        self.session = session

    def obter_indicadores(self):
        faturamento_total = (
            self.session.query(
                func.coalesce(func.sum(Venda.total), 0)
            )
            .filter(
                Venda.status == StatusVenda.FINALIZADA.value
            )
            .scalar()
        )

        quantidade_vendas = (
            self.session.query(Venda)
            .filter(
                Venda.status == StatusVenda.FINALIZADA.value
            )
            .count()
        )

        if quantidade_vendas > 0:
            ticket_medio = (
                faturamento_total / quantidade_vendas
            )
        else:
            ticket_medio = 0

        return IndicadoresVendas(
            faturamento_total=faturamento_total,
            quantidade_vendas=quantidade_vendas,
            ticket_medio=ticket_medio
        )