"""Integração opcional: TEST_DATABASE_URL deve apontar para banco dedicado *_test."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

os.environ.setdefault("DB_PORT", "5432")

from postgresql_base import PostgreSQLBase
from modulo_vendas.model import Categoria, Marca, Fornecedor, Produto, Venda, ItemVenda
from modulo_vendas.model.venda import StatusVenda
from modulo_vendas.controller.venda_controller import VendaController


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "Configure TEST_DATABASE_URL para PostgreSQL dedicado *_test.")
class PostgreSQLVendaTest(PostgreSQLBase):
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

    def test_historico_periodo_status_e_detalhes(self):
        from datetime import datetime
        with self.Session() as session:
            c = VendaController(session)
            venda = c.criar_venda()
            c.adicionar_item(venda, self.produto_id, 2)
            venda.data = datetime(2026, 9, 26, 23, 59, 59, 999999)
            session.commit()
            venda_id = venda.id
            outra = c.criar_venda()
            outra.data = datetime(2026, 9, 27)
            session.commit()
            resultado = c.listar(datetime(2026, 9, 26), datetime(2026, 9, 27), StatusVenda.EM_LANCAMENTO.value)
            self.assertEqual([v.id for v in resultado], [venda_id])
            detalhe = c.obter_detalhes(venda_id)
            self.assertEqual(sum(item.quantidade for item in detalhe.itens), 2)
            session.get(Produto, self.produto_id).preco = 99
            session.commit()
            self.assertEqual(c.obter_detalhes(venda_id).itens[0].valor, 50)

    def test_fluxo_web_com_controller_e_postgresql_reais(self):
        from unittest.mock import patch
        from web import create_app
        with patch.dict(os.environ, {"SECRET_KEY": "chave-exclusiva-de-testes"}):
            app = create_app()
        app.config["TESTING"] = True
        with patch("web.db.SessionLocal", self.Session):
            client = app.test_client()
            with client.session_transaction() as cookie:
                cookie["csrf_token"] = "csrf-test"
            def post(url, **dados):
                return client.post(url, data=dict(csrf_token="csrf-test", **dados))
            resposta = post("/vendas/nova")
            self.assertEqual(resposta.status_code, 303)
            with self.Session() as session:
                venda_id = session.query(Venda.id).scalar()
            base = f"/vendas/{venda_id}"
            post(base + "/confirmar-itens")  # Venda vazia deve continuar aberta.
            with self.Session() as session:
                self.assertEqual(session.get(Venda, venda_id).status, StatusVenda.EM_LANCAMENTO.value)
            post(base + "/itens", produto_id=self.produto_id, quantidade=2, valor=0.01)
            with self.Session() as session:
                item_id = session.query(ItemVenda.id).scalar()
            post(base + f"/itens/{item_id}/quantidade", acao="aumentar", quantidade=999)
            post(base + f"/itens/{item_id}/quantidade", acao="diminuir")
            post(base + "/confirmar-itens")
            with self.Session() as session:
                self.assertEqual(session.get(Produto, self.produto_id).estoque, 5)
            post(base + "/confirmar-pagamento")
            post(base + "/confirmar-pagamento")  # Não pode baixar novamente.
            with self.Session() as session:
                self.assertEqual(session.get(Produto, self.produto_id).estoque, 3)
                self.assertEqual(session.get(Venda, venda_id).total, 100)
                self.assertEqual(session.get(Venda, venda_id).status, StatusVenda.FINALIZADA.value)
            self.assertEqual(client.get(base).status_code, 200)
            self.assertEqual(client.get("/vendas/").status_code, 200)
