"""Integração opcional: TEST_DATABASE_URL deve apontar para banco dedicado *_test."""
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

os.environ.setdefault("DB_PORT", "5432")

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from database.connection import Base, engine as app_engine
from modulo_vendas.model import Categoria, Marca, Fornecedor, Produto, Venda, ItemVenda
from modulo_vendas.model.venda import StatusVenda
from modulo_vendas.controller.venda_controller import VendaController


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "Configure TEST_DATABASE_URL para PostgreSQL dedicado *_test.")
class PostgreSQLVendaTest(unittest.TestCase):
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

    def preparar_venda(self, quantidade=3):
        with self.Session() as session:
            controller = VendaController(session)
            venda = controller.criar_venda()
            controller.adicionar_item(venda, self.produto_id, quantidade, valor=0.01)
            controller.confirmar_itens(venda)
            return venda.id

    def test_persistencia_carrinho_e_remocao_sem_fk_nula(self):
        with self.Session() as session:
            c = VendaController(session)
            venda = c.criar_venda()
            item = c.adicionar_item(venda, self.produto_id, 2, valor=0.01)
            self.assertEqual(item.valor, 50)
            self.assertEqual(venda.total, 100)
            c.alterar_quantidade(venda, item.id, 3)
            self.assertEqual(venda.total, 150)
            c.remover_item(venda, item.id)
            self.assertEqual(venda.total, 0)
            self.assertEqual(session.query(ItemVenda).count(), 0)
            with self.assertRaises(ValueError):
                c.confirmar_itens(venda)
            c.adicionar_item(venda, self.produto_id, 1)
            c.confirmar_itens(venda)
            c.confirmar_pagamento(venda)
            self.assertEqual(session.get(Produto, self.produto_id).estoque, 4)

    def test_objetos_carregados_antes_de_outra_operacao_sao_recarregados(self):
        with self.Session() as first, self.Session() as second:
            c1, c2 = VendaController(first), VendaController(second)
            venda = c1.criar_venda()
            item = c1.adicionar_item(venda, self.produto_id, 1)
            outra = c2.buscar_por_id(venda.id)
            self.assertEqual(outra.itens[0].quantidade, 1)
            c1.alterar_quantidade(venda, item.id, 3)
            c2.confirmar_itens(outra)
            self.assertEqual(outra.total, 150)
            self.assertEqual(outra.itens[0].quantidade, 3)

    def _pagamentos_simultaneos(self, ids):
        barreira = Barrier(2)
        def pagar(venda_id):
            with self.Session() as session:
                c = VendaController(session)
                venda = c.buscar_por_id(venda_id)
                # Carrega também relacionamentos antes da disputa, para verificar releitura.
                for item in venda.itens:
                    _ = item.produto.estoque
                barreira.wait(timeout=10)
                try:
                    c.confirmar_pagamento(venda)
                    return "ok"
                except ValueError:
                    return "bloqueada"
        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = list(pool.map(pagar, ids))
        self.assertCountEqual(resultados, ["ok", "bloqueada"])
        with self.Session() as session:
            self.assertEqual(session.get(Produto, self.produto_id).estoque, 2)

    def test_duas_vendas_disputando_estoque(self):
        ids = [self.preparar_venda(), self.preparar_venda()]
        self._pagamentos_simultaneos(ids)
        with self.Session() as session:
            self.assertEqual(session.query(Venda).filter_by(status=StatusVenda.FINALIZADA.value).count(), 1)

    def test_duas_confirmacoes_da_mesma_venda(self):
        venda_id = self.preparar_venda()
        self._pagamentos_simultaneos([venda_id, venda_id])
