"""Banco exclusivo e schema descartável para testes de integração PostgreSQL."""
import os
import unittest
import uuid

os.environ.setdefault("DB_PORT", "5432")
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from database.connection import Base, engine as app_engine
from modulo_vendas.model import Categoria, Marca, Fornecedor, Produto


class PostgreSQLBase(unittest.TestCase):
    def setUp(self):
        url = make_url(os.environ["TEST_DATABASE_URL"])
        if url.get_backend_name() != "postgresql" or not (url.database or "").endswith("_test"):
            raise RuntimeError("Use somente um banco PostgreSQL dedicado com nome terminado em _test.")
        if url.database == app_engine.url.database:
            raise RuntimeError("O banco de testes não pode ter o nome do banco da aplicação.")
        # Schema exclusivo, aleatório e descartável; nunca usa tabelas existentes.
        self.schema = "vendas_test_" + uuid.uuid4().hex
        self.admin = create_engine(url, connect_args={"connect_timeout": 5})
        self.addCleanup(self.admin.dispose)
        with self.admin.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{self.schema}"'))
        self.addCleanup(self._limpar_schema)
        self.engine = create_engine(url, connect_args={
            "connect_timeout": 5,
            "options": f"-c search_path={self.schema} -c lock_timeout=5000 -c statement_timeout=10000",
        })
        self.addCleanup(self.engine.dispose)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, autoflush=False)
        with self.Session() as session:
            categoria, marca, fornecedor = Categoria(nome="Teste"), Marca(nome="Teste"), Fornecedor(nome="Teste")
            session.add_all([categoria, marca, fornecedor])
            session.flush()
            produto = Produto(descricao="Camisa", tamanho="M", preco=50, estoque=5,
                              categoria_id=categoria.id, marca_id=marca.id, fornecedor_id=fornecedor.id)
            session.add(produto)
            session.commit()
            self.produto_id = produto.id

    def _limpar_schema(self):
        with self.admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{self.schema}" CASCADE'))
