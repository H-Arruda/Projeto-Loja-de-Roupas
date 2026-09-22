from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from database.connection import Base


class ItemVenda(Base):
    __tablename__ = "item_venda"

    id = Column(Integer, primary_key=True, autoincrement=True)

    venda_id = Column(
        Integer,
        ForeignKey("venda.id"),
        nullable=False
    )

    produto_id = Column(
        Integer,
        ForeignKey("produto.id"),
        nullable=False
    )

    quantidade = Column(Integer, nullable=False)
    valor = Column(Float, nullable=False)

    venda = relationship(
        "Venda",
        back_populates="itens"
        )
    produto = relationship("Produto")

    def calcular_subtotal(self):
        return self.quantidade * self.valor