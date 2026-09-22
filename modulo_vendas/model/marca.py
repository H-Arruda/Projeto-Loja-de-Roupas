from sqlalchemy import Column, Integer, String

from database.connection import Base


class Marca(Base):
    __tablename__ = "marca"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)