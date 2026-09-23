from sqlalchemy import func

from modulo_data_analysis.model.indicadores_vendas import IndicadoresVendas
from modulo_vendas.model.venda import Venda, StatusVenda
from modulo_vendas.model.item_venda import ItemVenda
from modulo_vendas.model.produto import Produto
from modulo_vendas.model.categoria import Categoria
from modulo_vendas.model.marca import Marca

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
    def produtos_mais_vendidos(self, limite=5):
        resultados = (
            self.session.query(
                Produto.descricao,
                func.sum(ItemVenda.quantidade).label("quantidade_vendida")
            )
            .join(
                ItemVenda,
                ItemVenda.produto_id == Produto.id
            )
            .join(
                Venda,
                ItemVenda.venda_id == Venda.id
            )
            .filter(
                Venda.status == StatusVenda.FINALIZADA.value
            )
            .group_by(
                Produto.id,
                Produto.descricao
            )
            .order_by(
                func.sum(ItemVenda.quantidade).desc()
            )
            .limit(limite)
            .all()
        )

        return resultados

    def faturamento_por_produto(self):
        resultados = (
            self.session.query(
                Produto.descricao,
                func.sum(
                    ItemVenda.quantidade * ItemVenda.valor
                ).label("faturamento")
            )
            .join(
                ItemVenda,
                ItemVenda.produto_id == Produto.id
            )
            .join(
                Venda,
                ItemVenda.venda_id == Venda.id
            )
            .filter(
                Venda.status == StatusVenda.FINALIZADA.value
            )
            .group_by(
                Produto.id,
                Produto.descricao
            )
            .order_by(
                func.sum(
                    ItemVenda.quantidade * ItemVenda.valor
                ).desc()
            )
            .all()
        )

        return resultados

    def vendas_por_categoria(self):
        resultados = (
            self.session.query(
                Categoria.nome,
                func.sum(ItemVenda.quantidade).label(
                    "quantidade_vendida"
                )
            )
            .join(
                Produto,
                Produto.categoria_id == Categoria.id
            )
            .join(
                ItemVenda,
                ItemVenda.produto_id == Produto.id
            )
            .join(
                Venda,
                ItemVenda.venda_id == Venda.id
            )
            .filter(
                Venda.status == StatusVenda.FINALIZADA.value
            )
            .group_by(
                Categoria.id,
                Categoria.nome
            )
            .order_by(
                func.sum(ItemVenda.quantidade).desc()
            )
            .all()
        )

        return resultados

    def vendas_por_marca(self):
        resultados = (
            self.session.query(
                Marca.nome,
                func.sum(ItemVenda.quantidade).label(
                    "quantidade_vendida"
                )
            )
            .join(
                Produto,
                Produto.marca_id == Marca.id
            )
            .join(
                ItemVenda,
                ItemVenda.produto_id == Produto.id
            )
            .join(
                Venda,
                ItemVenda.venda_id == Venda.id
            )
            .filter(
                Venda.status == StatusVenda.FINALIZADA.value
            )
            .group_by(
                Marca.id,
                Marca.nome
            )
            .order_by(
                func.sum(ItemVenda.quantidade).desc()
            )
            .all()
        )

        return resultados

    def estoque_baixo(self, limite=5):
        resultados = (
            self.session.query(Produto)
            .filter(
                Produto.estoque <= limite
            )
            .order_by(
                Produto.estoque.asc()
            )
            .all()
        )

        return resultados

    def produtos_sem_estoque(self):
        return (
            self.session.query(Produto)
            .filter(Produto.estoque == 0)
            .all()
        )

    def vendas_por_periodo(self, data_inicio, data_fim):
        return (
            self.session.query(Venda)
            .filter(
                Venda.status == StatusVenda.FINALIZADA.value,
                Venda.data >= data_inicio,
                Venda.data <= data_fim
            )
            .order_by(Venda.data.asc())
            .all()
        )

    def faturamento_por_periodo(self, data_inicio, data_fim):
        return (
            self.session.query(
                func.coalesce(func.sum(Venda.total), 0)
            )
            .filter(
                Venda.status == StatusVenda.FINALIZADA.value,
                Venda.data >= data_inicio,
                Venda.data <= data_fim
            )
            .scalar()
        )

    def faturamento_por_categoria(self):
        resultados = (
            self.session.query(
                Categoria.nome,
                func.sum(
                    ItemVenda.quantidade * ItemVenda.valor
                ).label("faturamento")
            )
            .join(
                Produto,
                Produto.categoria_id == Categoria.id
            )
            .join(
                ItemVenda,
                ItemVenda.produto_id == Produto.id
            )
            .join(
                Venda,
                ItemVenda.venda_id == Venda.id
            )
            .filter(
                Venda.status == StatusVenda.FINALIZADA.value
            )
            .group_by(
                Categoria.id,
                Categoria.nome
            )
            .order_by(
                func.sum(
                    ItemVenda.quantidade * ItemVenda.valor
                ).desc()
            )
            .all()
        )

        return resultados 

    def faturamento_por_marca(self):
        resultados = (
            self.session.query(
                Marca.nome,
                func.sum(
                    ItemVenda.quantidade * ItemVenda.valor
                ).label("faturamento")
            )
            .join(
                Produto,
                Produto.marca_id == Marca.id
            )
            .join(
                ItemVenda,
                ItemVenda.produto_id == Produto.id
            )
            .join(
                Venda,
                ItemVenda.venda_id == Venda.id
            )
            .filter(
                Venda.status == StatusVenda.FINALIZADA.value
            )
            .group_by(
                Marca.id,
                Marca.nome
            )
            .order_by(
                func.sum(
                    ItemVenda.quantidade * ItemVenda.valor
                ).desc()
            )
            .all()
        )

        return resultados

    def vendas_por_dia(self):
        resultados = (
            self.session.query(
                func.date(Venda.data).label("data"),
                func.count(Venda.id).label("quantidade_vendas"),
                func.sum(Venda.total).label("faturamento")
            )
            .filter(
                Venda.status == StatusVenda.FINALIZADA.value
            )
            .group_by(
                func.date(Venda.data)
            )
            .order_by(
                func.date(Venda.data).asc()
            )
            .all()
        )

        return resultados