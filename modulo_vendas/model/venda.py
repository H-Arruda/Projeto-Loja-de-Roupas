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

        self.calcular_total()
        self.status = StatusVenda.AGUARDANDO_PAGAMENTO.value

    def confirmar_pagamento(self):
        if self.status != StatusVenda.AGUARDANDO_PAGAMENTO.value:
            raise ValueError(
            "A venda não está aguardando pagamento."
        )

        for item in self.itens:
            if item.quantidade > item.produto.estoque:
                raise ValueError(
                    f"Estoque insuficiente para "
                    f"{item.produto.descricao}."
                )

        for item in self.itens:
            item.produto.alterar_estoque(
                -item.quantidade
        )

        self.status = StatusVenda.FINALIZADA.value

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