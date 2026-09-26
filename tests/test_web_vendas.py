import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DB_PORT", "5432")
from web import create_app
from modulo_vendas.model import Produto, ItemVenda, Venda
from modulo_vendas.model.venda import StatusVenda


class WebVendasTest(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {"SECRET_KEY": "chave-exclusiva-de-testes"}):
            self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.session = MagicMock()
        for caminho, valor in (("web.db.SessionLocal", self.session),
                               ("web.routes.vendas.VendaController", MagicMock()),
                               ("web.routes.vendas.ProdutoController", MagicMock())):
            p = patch(caminho, return_value=valor)
            p.start()
            self.addCleanup(p.stop)
            if caminho.endswith("VendaController"):
                self.vendas = valor
            elif caminho.endswith("ProdutoController"):
                self.produtos = valor
        self.produto = Produto(id=1, descricao="Camisa", tamanho="M", preco=99, estoque=8)
        # Relacionamentos reais do ORM sem sessão ou conexão ao banco.
        from modulo_vendas.model import Categoria, Marca
        self.produto.categoria = Categoria(id=1, nome="Camisas")
        self.produto.marca = Marca(id=1, nome="Marca")
        self.venda = Venda(id=10, data=datetime(2026, 9, 26, 14, 30),
                           status=StatusVenda.EM_LANCAMENTO.value, total=100)
        self.item = ItemVenda(id=7, produto=self.produto, produto_id=1, quantidade=2, valor=50)
        self.venda.itens = [self.item]
        self.produtos.listar.return_value = [self.produto]
        self.vendas.obter_detalhes.return_value = self.venda
        self.vendas.criar_venda.return_value = self.venda
        self.vendas.listar.return_value = [self.venda]

    def post(self, caminho, **dados):
        with self.client.session_transaction() as session:
            session["csrf_token"] = "csrf-test"
        return self.client.post(caminho, data=dict(csrf_token="csrf-test", **dados))

    def test_paginas_renderizam_sem_escrita_por_get(self):
        for caminho in ("/vendas/nova", "/vendas/10/pdv", "/vendas/", "/vendas/10"):
            with self.subTest(caminho=caminho):
                self.assertEqual(self.client.get(caminho).status_code, 200)
        self.vendas.criar_venda.assert_not_called()
        self.vendas.confirmar_pagamento.assert_not_called()
        self.session.close.assert_called()

    def test_criacao_por_post_redireciona(self):
        resposta = self.post("/vendas/nova", q="Camisa")
        self.assertEqual(resposta.status_code, 303)
        self.assertIn("/vendas/10/pdv", resposta.location)
        self.vendas.criar_venda.assert_called_once()

    def test_preco_do_navegador_nao_e_encaminhado(self):
        resposta = self.post("/vendas/10/itens", produto_id="1", quantidade="2", valor="0.01", total="0.02")
        self.assertEqual(resposta.status_code, 303)
        self.vendas.adicionar_item.assert_called_once_with(self.venda, 1, 2)

    def test_busca_de_produtos(self):
        self.client.get("/vendas/10/pdv?q=Camisa")
        self.produtos.listar.assert_called_once_with(descricao="Camisa")

    def test_quantidade_invalida_retorna_mensagem(self):
        r = self.post("/vendas/10/itens", produto_id="1", quantidade="1.5")
        self.vendas.adicionar_item.assert_not_called()
        html = self.client.get(r.location).get_data(as_text=True)
        self.assertIn("quantidade inteira positiva", html)
        self.session.rollback.assert_called()

    def test_incrementar_diminuir_definir_e_remover(self):
        for acao, delta in (("aumentar", 1), ("diminuir", -1)):
            self.post("/vendas/10/itens/7/quantidade", acao=acao, quantidade="999")
            self.vendas.ajustar_quantidade.assert_called_with(self.venda, 7, delta)
        self.post("/vendas/10/itens/7/quantidade", acao="definir", quantidade="3")
        self.vendas.alterar_quantidade.assert_called_once_with(self.venda, 7, 3)
        self.post("/vendas/10/itens/7/remover")
        self.vendas.remover_item.assert_called_once_with(self.venda, 7)

    def test_confirmacoes_e_cancelamento_delegam_ao_controller(self):
        for rota, metodo in (("confirmar-itens", "confirmar_itens"),
                             ("confirmar-pagamento", "confirmar_pagamento"), ("cancelar", "cancelar")):
            self.assertEqual(self.post(f"/vendas/10/{rota}").status_code, 303)
            getattr(self.vendas, metodo).assert_called_once_with(self.venda)

    def test_erros_de_regra_aparecem_no_pdv(self):
        for metodo, rota, mensagem in (
            ("confirmar_itens", "confirmar-itens", "A venda deve conter pelo menos um item."),
            ("confirmar_pagamento", "confirmar-pagamento", "Estoque insuficiente para Camisa."),
            ("confirmar_pagamento", "confirmar-pagamento", "A venda não está aguardando pagamento.")):
            getattr(self.vendas, metodo).side_effect = ValueError(mensagem)
            r = self.post(f"/vendas/10/{rota}")
            self.assertIn(mensagem, self.client.get(r.location).get_data(as_text=True))

    def test_todas_acoes_exigem_csrf_e_nao_aceitam_get(self):
        for rota in ("itens", "itens/7/quantidade", "itens/7/remover", "confirmar-itens", "confirmar-pagamento", "cancelar"):
            with self.subTest(rota=rota):
                caminho = f"/vendas/10/{rota}"
                self.assertEqual(self.client.get(caminho).status_code, 405)
                self.assertEqual(self.client.post(caminho).status_code, 400)
        self.assertEqual(self.client.post("/vendas/nova").status_code, 400)

    def test_detalhes_usam_preco_registrado_e_unidades(self):
        html = self.client.get("/vendas/10").get_data(as_text=True)
        self.assertIn("R$ 50,00", html)
        self.assertNotIn("R$ 99,00", html)
        self.assertIn("R$ 100,00", html)
        self.assertIn("2 unidade(s)", html)

    def test_historico_periodo_inclui_dia_final(self):
        r = self.client.get("/vendas/?inicio=2026-09-01&fim=2026-09-26&status=Finalizada")
        self.assertEqual(r.status_code, 200)
        self.vendas.listar.assert_called_once_with(datetime(2026, 9, 1), datetime(2026, 9, 27), "Finalizada")

    def test_historico_data_invalida(self):
        for query in ("inicio=abc", "fim=2026-02-30", "fim=9999-12-31"):
            self.assertEqual(self.client.get("/vendas/?" + query).status_code, 400)
        self.vendas.listar.assert_not_called()

    def test_historico_erro_de_status(self):
        self.vendas.listar.side_effect = ValueError("Status de venda inválido.")
        r = self.client.get("/vendas/?status=Inexistente")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Status de venda inválido", r.get_data(as_text=True))

    def test_estados_vazios_e_404(self):
        self.produtos.listar.return_value = []
        self.vendas.listar.return_value = []
        self.assertIn("Seu catálogo está vazio", self.client.get("/vendas/nova").get_data(as_text=True))
        self.assertIn("primeira venda", self.client.get("/vendas/").get_data(as_text=True))
        self.vendas.obter_detalhes.return_value = None
        self.assertEqual(self.client.get("/vendas/999").status_code, 404)
        self.assertEqual(self.post("/vendas/999/confirmar-pagamento").status_code, 404)

    def test_acoes_visiveis_conforme_status(self):
        self.venda.status = StatusVenda.AGUARDANDO_PAGAMENTO.value
        html = self.client.get("/vendas/10/pdv").get_data(as_text=True)
        self.assertIn('action="/vendas/10/confirmar-pagamento"', html)
        self.assertNotIn('action="/vendas/10/itens"', html)
        for estado in (StatusVenda.FINALIZADA, StatusVenda.CANCELADA):
            self.venda.status = estado.value
            html = self.client.get("/vendas/10/pdv").get_data(as_text=True)
            self.assertNotIn('action="/vendas/10/confirmar-pagamento"', html)
            self.assertNotIn('action="/vendas/10/cancelar"', html)
            self.assertIn(estado.value, html)
