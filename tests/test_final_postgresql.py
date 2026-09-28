"""Regressão de apresentação usando Flask, Controllers e PostgreSQL reais."""
import os
import re
import unittest
from datetime import date, datetime
from unittest.mock import patch
from urllib.parse import urlsplit

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from postgresql_base import PostgreSQLBase
from modulo_vendas.model import Categoria, Marca, Fornecedor, Produto, Venda, ItemVenda
from modulo_vendas.model.venda import StatusVenda
from modulo_data_analysis.controller.analytics_controller import AnalyticsController
from scripts.seed_demo import preencher
from web import create_app


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "Configure TEST_DATABASE_URL para PostgreSQL dedicado *_test.")
class FinalPostgreSQLTest(PostgreSQLBase):
    def cliente(self):
        with patch.dict(os.environ, {"SECRET_KEY": "somente-testes"}):
            app = create_app()
        app.config["TESTING"] = True
        p = patch("web.db.SessionLocal", self.Session)
        p.start()
        self.addCleanup(p.stop)
        client = app.test_client()
        with client.session_transaction() as cookie:
            cookie["csrf_token"] = "csrf-teste"
        return client

    def test_fluxo_catalogo_pdv_analytics_e_bloqueios(self):
        client = self.cliente()
        def post(path, **dados):
            return client.post(path, data=dict(csrf_token="csrf-teste", **dados))
        ids = {}
        for modulo, model in (("categorias", Categoria), ("marcas", Marca), ("fornecedores", Fornecedor)):
            self.assertEqual(post(f"/{modulo}/novo", nome="Apresentação").status_code, 303)
            with self.Session() as session:
                ids[modulo] = session.query(model).filter_by(nome="Apresentação").one().id
        dados = dict(descricao="Camisa demonstração", preco="89,90", tamanho="M", estoque="8",
                     categoria_id=ids["categorias"], marca_id=ids["marcas"], fornecedor_id=ids["fornecedores"])
        self.assertEqual(post("/produtos/novo", **dados).status_code, 303)
        with self.Session() as session:
            produto_id = session.query(Produto).filter_by(descricao=dados["descricao"]).one().id
        html = client.get(f"/produtos/{produto_id}/editar").get_data(as_text=True)
        token = re.search(r'name="estoque_token" value="([^"]+)"', html).group(1)
        dados["preco"] = "99,90"
        self.assertEqual(post(f"/produtos/{produto_id}/editar", estoque_token=token, **dados).status_code, 303)
        for modulo in ids:
            r = post(f"/{modulo}/{ids[modulo]}/excluir")
            self.assertEqual(r.status_code, 409)
            self.assertIn("vinculado", r.get_data(as_text=True))
        base = urlsplit(post("/vendas/nova").location).path.removesuffix("/pdv")
        post(base + "/confirmar-itens")
        with self.Session() as session:
            self.assertEqual(session.query(Venda).one().status, "Em Lançamento")
            self.assertEqual(session.query(ItemVenda).count(), 0)
        post(base + "/itens", produto_id=produto_id, quantidade=100)
        with self.Session() as session:
            self.assertEqual(session.query(ItemVenda).count(), 0)
        post(base + "/itens", produto_id=produto_id, quantidade=2, valor="0,01")
        with self.Session() as session:
            item_id = session.query(ItemVenda).one().id
        post(base + f"/itens/{item_id}/quantidade", acao="aumentar")
        post(base + f"/itens/{item_id}/quantidade", acao="diminuir")
        post(base + f"/itens/{item_id}/remover")
        with self.Session() as session:
            self.assertEqual(session.query(ItemVenda).count(), 0)
        post(base + "/itens", produto_id=produto_id, quantidade=2)
        post(base + "/confirmar-itens")
        with self.Session() as session:
            self.assertEqual(session.get(Produto, produto_id).estoque, 8)
        post(base + "/confirmar-pagamento")
        post(base + "/confirmar-pagamento")
        with self.Session() as session:
            self.assertEqual(session.get(Produto, produto_id).estoque, 6)
            venda = session.query(Venda).one()
            self.assertEqual(venda.status, StatusVenda.FINALIZADA.value)
            self.assertAlmostEqual(venda.total, 199.8)
            indicadores = AnalyticsController(session).obter_indicadores()
            self.assertEqual(indicadores.quantidade_vendas, 1)
            self.assertAlmostEqual(indicadores.faturamento_total, 199.8)
            self.assertAlmostEqual(indicadores.ticket_medio, 199.8)
        self.assertEqual(post(f"/produtos/{produto_id}/excluir").status_code, 409)
        for path in (base, "/vendas/", "/", "/analytics/"):
            r = client.get(path)
            self.assertEqual(r.status_code, 200)
            self.assertIn("199,80", r.get_data(as_text=True))
        self.assertIn("Camisa demonstração", client.get(f"/produtos/?descricao=demonstração&categoria_id={ids['categorias']}&marca_id={ids['marcas']}&estoque=normal").get_data(as_text=True))
        vazio = client.get("/produtos/?descricao=produto-inexistente").get_data(as_text=True)
        self.assertNotIn('class="product-name">Camisa', vazio)
        cancelada = urlsplit(post("/vendas/nova").location).path.removesuffix("/pdv")
        post(cancelada + "/itens", produto_id=produto_id, quantidade=1)
        post(cancelada + "/cancelar")
        with self.Session() as session:
            self.assertEqual(session.get(Produto, produto_id).estoque, 6)
            self.assertEqual(session.query(Venda).filter_by(status="Cancelada").count(), 1)

    def limpar_fixture(self):
        # Exclusivamente o schema descartável criado pelo PostgreSQLBase.
        with self.Session() as session:
            for model in (Produto, Categoria, Marca, Fornecedor):
                session.execute(delete(model))
            session.commit()

    def test_seed_atomico_metricas_e_reexecucao_bloqueada(self):
        self.limpar_fixture()
        with self.engine.begin() as conn:
            with Session(bind=conn, join_transaction_mode="create_savepoint", autoflush=False) as session:
                resumo = preencher(session, date(2026, 9, 27))
        with self.Session() as session:
            c = AnalyticsController(session)
            i = c.obter_indicadores()
            self.assertEqual(i.quantidade_vendas, 12)
            self.assertAlmostEqual(i.faturamento_total, resumo["faturamento"])
            self.assertAlmostEqual(i.ticket_medio, resumo["faturamento"] / 12)
            self.assertEqual(session.query(Produto).count(), 15)
            self.assertTrue(c.produtos_sem_estoque())
            self.assertEqual(len(c.estoque_baixo()), session.query(Produto).filter(Produto.estoque <= 5).count())
            for linhas in (c.faturamento_por_categoria(), c.faturamento_por_marca(), c.faturamento_por_produto(), c.vendas_por_dia()):
                self.assertAlmostEqual(sum(r.faturamento for r in linhas), resumo["faturamento"])
            self.assertEqual(c.produtos_mais_vendidos()[0].quantidade_vendida, 5)
            self.assertEqual(sum(r.quantidade_vendida for r in c.vendas_por_categoria()), session.query(func.sum(ItemVenda.quantidade)).scalar())
            self.assertEqual(len(c.vendas_por_periodo(datetime(2026,9,27), datetime(2026,9,27,23,59,59,999999))), 1)
            self.assertAlmostEqual(c.faturamento_por_periodo(datetime(2026,9,27), datetime(2026,9,27,23,59,59,999999)), 229.8)
            with self.assertRaisesRegex(ValueError, "já contém"):
                preencher(session)
            self.assertEqual(session.query(Venda).count(), 12)

    def test_seed_falha_reverte_carga_inteira(self):
        self.limpar_fixture()
        with self.assertRaisesRegex(RuntimeError, "falha controlada"):
            with self.engine.begin() as conn:
                with Session(bind=conn, join_transaction_mode="create_savepoint", autoflush=False) as session:
                    with patch("scripts.seed_demo.VendaController.confirmar_pagamento", side_effect=RuntimeError("falha controlada")):
                        preencher(session)
        with self.Session() as session:
            for model in (Categoria, Marca, Fornecedor, Produto, Venda, ItemVenda):
                self.assertEqual(session.query(model).count(), 0)
