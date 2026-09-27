"""Validação opcional do caminho pagamento -> indicadores com PostgreSQL real."""
import os
import unittest
from datetime import datetime
from unittest.mock import patch

from postgresql_base import PostgreSQLBase
from modulo_vendas.controller.venda_controller import VendaController
from modulo_data_analysis.controller.analytics_controller import AnalyticsController
from web import create_app


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "Configure TEST_DATABASE_URL para PostgreSQL dedicado *_test.")
class AnalyticsPostgreSQLTest(PostgreSQLBase):
    def test_pagamento_reflete_nos_indicadores_e_paginas(self):
        with self.Session() as session:
            vendas = VendaController(session)
            venda = vendas.criar_venda()
            vendas.adicionar_item(venda, self.produto_id, 2)
            vendas.confirmar_itens(venda)
            analytics = AnalyticsController(session)
            self.assertEqual(analytics.obter_indicadores().faturamento_total, 0)
            vendas.confirmar_pagamento(venda)
            venda.data = datetime(2026, 9, 20, 23, 59, 59, 999999)
            session.commit()
            self.assertEqual(analytics.obter_indicadores().faturamento_total, 100)
            self.assertEqual(analytics.produtos_mais_vendidos()[0].quantidade_vendida, 2)
            self.assertEqual(analytics.estoque_baixo()[0].estoque, 3)
        with patch.dict(os.environ, {"SECRET_KEY": "chave-exclusiva-testes"}):
            app = create_app()
        app.config["TESTING"] = True
        with patch("web.db.SessionLocal", self.Session):
            client = app.test_client()
            for path in ("/", "/analytics/", "/analytics/?data_inicio=2026-09-20&data_fim=2026-09-20"):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("R$ 100,00", response.get_data(as_text=True))
            html = client.get("/analytics/?data_inicio=2026-09-21&data_fim=2026-09-21").get_data(as_text=True)
            self.assertIn("0 venda(s)", html)
