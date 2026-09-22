from sqlalchemy import Column, Integer, String

from database.connection import Base

class Categoria(Base):
    __tablename__="categoria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)