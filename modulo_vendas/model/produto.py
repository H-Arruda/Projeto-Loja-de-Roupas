from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database.connection import Base

class Produto(Base):
    __tablename__= "produto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String(180), nullable=False)
    preco = Column(Float, nullable=False)
    tamanho = Column(String(20), nullable=False)
    estoque = Column(Integer, nullable=False)

    categoria_id = Column(
        Integer,
        ForeignKey("categoria.id"),
        nullable=False
    )

    marca_id = Column(
        Integer,
        ForeignKey("marca.id"),
        nullable=False
    )
    
    fornecedor_id = Column(
        Integer,
        ForeignKey("fornecedor.id"),
        nullable=False
    )

    categoria = relationship("Categoria")
    marca = relationship("Marca")
    fornecedor = relationship("Fornecedor") 

    def alterar_estoque(self, qtd):
        self.estoque += qtd