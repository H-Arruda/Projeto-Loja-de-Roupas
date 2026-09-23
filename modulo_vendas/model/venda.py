from enum import Enum
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from database.connection import Base


class StatusVenda(Enum):
    EM_LANCAMENTO = "Em Lançamento"
    AGUARDANDO_PAGAMENTO = "Aguardando Pagamento"
    FINALIZADA = "Finalizada"
    CANCELADA = "Cancelada"


class Venda(Base):
    __tablename__ = "venda"

    id = Column(Integer, primary_key=True, autoincrement=True)

    total = Column(
        Float,
        nullable=False,
        default=0
    )

    status = Column(
        String(50),
        nullable=False,
        default=StatusVenda.EM_LANCAMENTO.value
    )

    data = Column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    itens = relationship(
        "ItemVenda",
        back_populates="venda"
    )

    def calcular_total(self):
        self.total = sum(
            item.calcular_subtotal()
            for item in self.itens
        )

        return self.total

    def confirmar_itens(self):
        if self.status != StatusVenda.EM_LANCAMENTO.value:
            raise ValueError("A venda não está em lançamento.")

        self._validar_itens()
        self.calcular_total()
        self.status = StatusVenda.AGUARDANDO_PAGAMENTO.value

    def confirmar_pagamento(self):
        if self.status != StatusVenda.AGUARDANDO_PAGAMENTO.value:
            raise ValueError(
            "A venda não está aguardando pagamento."
        )

        self._validar_itens()
        quantidades = {}
        for item in self.itens:
            quantidades[item.produto_id] = (
                quantidades.get(item.produto_id, 0) + item.quantidade
            )

        for item in self.itens:
            if quantidades[item.produto_id] > item.produto.estoque:
                raise ValueError(
                    f"Estoque insuficiente para "
                    f"{item.produto.descricao}."
                )

        for item in self.itens:
            item.produto.alterar_estoque(
                -item.quantidade
        )

        self.status = StatusVenda.FINALIZADA.value

    def _validar_itens(self):
        if not self.itens:
            raise ValueError("A venda deve conter pelo menos um item.")
        if any(type(item.quantidade) is not int or item.quantidade <= 0
               for item in self.itens):
            raise ValueError("A quantidade deve ser um inteiro positivo.")

    def cancelar(self):
        if self.status in [
            StatusVenda.EM_LANCAMENTO.value,
            StatusVenda.AGUARDANDO_PAGAMENTO.value
        ]:
            self.status = StatusVenda.CANCELADA.value
        else:
            raise ValueError(
                "A venda não pode ser cancelada nesse estado."
            )
