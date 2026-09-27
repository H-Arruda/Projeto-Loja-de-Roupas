import os
import unittest
from html.parser import HTMLParser
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DB_PORT", "5432")
from web import create_app


class LinksSidebar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.no_menu = False
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav" and attrs.get("aria-label") == "Navegação principal":
            self.no_menu = True
        if self.no_menu and tag == "a":
            self.links.append(attrs.get("href"))

    def handle_endtag(self, tag):
        if tag == "nav":
            self.no_menu = False


class InterfaceTest(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {"SECRET_KEY": "chave-exclusiva-de-testes"}):
            self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        db = patch("web.db.SessionLocal", return_value=MagicMock())
        db.start()
        self.addCleanup(db.stop)
        controller = patch("web.routes.dashboard.AnalyticsController", autospec=True)
        self.analytics = controller.start().return_value
        self.addCleanup(controller.stop)
        self.analytics.obter_indicadores.return_value = SimpleNamespace(faturamento_total=1234.5, quantidade_vendas=3, ticket_medio=411.5)
        self.analytics.produtos_mais_vendidos.return_value = []
        self.analytics.estoque_baixo.return_value = []
        self.analytics.vendas_por_dia.return_value = []
        self.analytics.faturamento_por_categoria.return_value = []
        self.analytics.faturamento_por_marca.return_value = []

    def test_dashboard_mantem_dados_do_controller(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("R$ 1.234,50", html)
        self.assertIn("R$ 411,50", html)
        self.assertIn("Estoque crítico", html)
        self.assertIn("Todo o histórico", html)
        self.assertIn("plotly", html.lower())
        self.analytics.obter_indicadores.assert_called_once()

    def test_todos_links_sidebar_tem_rota_get_valida(self):
        parser = LinksSidebar()
        parser.feed(self.client.get("/").get_data(as_text=True))
        self.assertEqual(len(parser.links), 8)
        adapter = self.app.url_map.bind("localhost")
        for link in parser.links:
            with self.subTest(link=link):
                endpoint, _ = adapter.match(link, method="GET")
                self.assertIn(endpoint, self.app.view_functions)
        self.assertIn("/analytics/", parser.links)

    def test_assets_locais_disponiveis(self):
        for path in ("css/app.css", "js/navegacao.js", "favicon.svg", "fonts/Inter-Variable.ttf", "fonts/Poppins-SemiBold.ttf"):
            with self.subTest(path=path):
                response = self.client.get("/static/" + path)
                self.assertEqual(response.status_code, 200)
                response.close()
