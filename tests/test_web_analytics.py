import json
import os
import re
import unittest
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace as Row
from unittest.mock import MagicMock, patch

os.environ.setdefault("DB_PORT", "5432")
from web import create_app


class AnalyticsWebTest(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {"SECRET_KEY": "somente-testes"}):
            self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.db = MagicMock()
        p = patch("web.db.SessionLocal", return_value=self.db)
        p.start()
        self.addCleanup(p.stop)
        self.controller = MagicMock()
        for modulo in ("dashboard", "analytics"):
            p = patch(f"web.routes.{modulo}.AnalyticsController", return_value=self.controller)
            p.start()
            self.addCleanup(p.stop)
        self.vazio()

    def vazio(self):
        c = self.controller
        c.obter_indicadores.return_value = Row(faturamento_total=0, quantidade_vendas=0, ticket_medio=0)
        for metodo in ("vendas_por_dia", "produtos_mais_vendidos", "faturamento_por_categoria",
                       "faturamento_por_marca", "faturamento_por_produto", "vendas_por_categoria",
                       "vendas_por_marca", "estoque_baixo", "produtos_sem_estoque", "vendas_por_periodo"):
            getattr(c, metodo).return_value = []
        c.faturamento_por_periodo.return_value = 0

    def dados(self):
        c = self.controller
        c.obter_indicadores.return_value = Row(faturamento_total=Decimal("123.45"), quantidade_vendas=1, ticket_medio=Decimal("123.45"))
        c.vendas_por_dia.return_value = [Row(data=date(2026, 9, 20), quantidade_vendas=1, faturamento=Decimal("123.45"))]
        c.produtos_mais_vendidos.return_value = [Row(descricao="Camisa", quantidade_vendida=2)]
        for m in ("faturamento_por_categoria", "faturamento_por_marca"):
            getattr(c, m).return_value = [Row(nome="Essencial", faturamento=Decimal("123.45"))]
        c.faturamento_por_produto.return_value = [Row(descricao="Camisa", faturamento=Decimal("123.45"))]
        for m in ("vendas_por_categoria", "vendas_por_marca"):
            getattr(c, m).return_value = [Row(nome="Essencial", quantidade_vendida=2)]
        c.estoque_baixo.return_value = [Row(descricao="Camisa", tamanho="M", estoque=2)]
        c.produtos_sem_estoque.return_value = [Row(descricao="Calça", tamanho="G", estoque=0)]
        c.vendas_por_periodo.return_value = [Row(id=10, data=datetime(2026,9,20,23,59,59,999999), status="Finalizada", total=Decimal("123.45"))]
        c.faturamento_por_periodo.return_value = Decimal("123.45")

    def figuras(self, html):
        return [json.loads(s) for s in re.findall(r'<script type="application/json" data-chart="[^"]+">(.*?)</script>', html, re.S)]

    def test_dashboard_e_analytics_com_dados(self):
        self.dados()
        for path in ("/", "/analytics/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn("R$ 123,45", html)
                figures = self.figuras(html)
                self.assertEqual(len(figures), 4)
                self.assertEqual(figures[0]["data"][0]["x"], ["2026-09-20"])
                self.assertEqual(figures[0]["data"][0]["y"], [123.45])
                self.assertEqual(figures[0]["data"][0]["customdata"], [1])
                self.assertEqual(figures[1]["data"][0]["x"], [2.0])
                self.assertEqual(figures[1]["data"][0]["orientation"], "h")
        self.db.close.assert_called()
        self.db.rollback.assert_called()

    def test_dashboard_e_analytics_sem_dados(self):
        for path in ("/", "/analytics/"):
            html = self.client.get(path).get_data(as_text=True)
            self.assertEqual(self.figuras(html), [])
            self.assertEqual(html.count("Ainda não há dados suficientes para este gráfico."), 4)
            self.assertIn("R$ 0,00", html)
        self.controller.vendas_por_periodo.assert_not_called()

    def test_periodo_valido_inclui_ultimo_dia_completo(self):
        self.dados()
        r = self.client.get("/analytics/?data_inicio=2026-09-01&data_fim=2026-09-20")
        self.assertEqual(r.status_code, 200)
        limites = (datetime(2026,9,1), datetime(2026,9,20,23,59,59,999999))
        self.controller.vendas_por_periodo.assert_called_once_with(*limites)
        self.controller.faturamento_por_periodo.assert_called_once_with(*limites)
        self.controller.vendas_por_dia.assert_called_once_with()
        self.controller.obter_indicadores.assert_called_once_with()
        html = r.get_data(as_text=True)
        self.assertIn('href="/vendas/10"', html)
        self.assertIn("Todo o histórico", html)
        self.assertIn("Posição atual".upper(), html)
        self.assertIn("somente o faturamento e a lista de vendas deste bloco", html)

    def test_datas_invalidas_incompletas_e_invertidas(self):
        for query, mensagem in (("data_inicio=abc&data_fim=2026-09-01", "datas válidas"),
                                ("data_inicio=2026-02-30&data_fim=2026-09-01", "datas válidas"),
                                ("data_inicio=20260901&data_fim=2026-09-01", "datas válidas"),
                                ("data_inicio=2026-09-20&data_fim=2026-09-01", "posterior"),
                                ("data_inicio=2026-09-01", "data inicial e a data final")):
            with self.subTest(query=query):
                r = self.client.get("/analytics/?" + query)
                self.assertEqual(r.status_code, 400)
                self.assertIn(mensagem, r.get_data(as_text=True))
        self.controller.vendas_por_periodo.assert_not_called()
        self.controller.faturamento_por_periodo.assert_not_called()

    def test_periodo_vazio_e_limpar(self):
        html = self.client.get("/analytics/?data_inicio=2026-09-01&data_fim=2026-09-01").get_data(as_text=True)
        self.assertIn("0 venda(s)", html)
        self.assertIn('href="/analytics/#periodo"', html)
        self.controller.reset_mock()
        self.client.get("/analytics/")
        self.controller.vendas_por_periodo.assert_not_called()

    def test_recursos_locais_sem_cdn(self):
        self.dados()
        for path in ("/", "/analytics/"):
            html = self.client.get(path).get_data(as_text=True)
            for src in re.findall(r'(?:src|href)="([^"]+)"', html):
                self.assertFalse(src.startswith(("http:", "https:", "//")), src)
            for src in re.findall(r'<script src="([^"]+)"', html):
                r = self.client.get(src)
                self.assertEqual(r.status_code, 200)
                r.close()
        license_response = self.client.get("/static/vendor/plotly/LICENSE")
        self.assertIn("MIT License", license_response.get_data(as_text=True))
        license_response.close()

    def test_rotulos_serializados_sem_injetar_html(self):
        self.dados()
        self.controller.produtos_mais_vendidos.return_value = [Row(descricao='</script><script>alert(1)</script>', quantidade_vendida=2)]
        html = self.client.get("/").get_data(as_text=True)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn("&lt;/script&gt;", self.figuras(html)[1]["data"][0]["customdata"][0])

    def test_produtos_homonimos_nao_sao_agrupados_pelo_grafico(self):
        self.dados()
        self.controller.produtos_mais_vendidos.return_value = [Row(descricao="Camisa", quantidade_vendida=2), Row(descricao="Camisa", quantidade_vendida=3)]
        bars = self.figuras(self.client.get("/").get_data(as_text=True))[1]["data"][0]
        self.assertEqual(bars["y"], ["0", "1"])
        self.assertEqual(bars["x"], [2.0, 3.0])
