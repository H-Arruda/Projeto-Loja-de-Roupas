import os
import re
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DB_PORT", "5432")
from web import create_app


class WebCatalogosTest(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {"SECRET_KEY": "chave-exclusiva-de-testes"}):
            self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.session = MagicMock()
        db_patch = patch("web.db.SessionLocal", return_value=self.session)
        db_patch.start()
        self.addCleanup(db_patch.stop)
        self.controllers = {}
        for modulo, classe in (("produtos", "Produto"), ("categorias", "Categoria"),
                              ("marcas", "Marca"), ("fornecedores", "Fornecedor")):
            p = patch(f"web.routes.{modulo}.{classe}Controller", autospec=True)
            self.controllers[modulo] = p.start().return_value
            self.addCleanup(p.stop)
        opcao = SimpleNamespace(id=1, nome="Exemplo")
        self.produto = SimpleNamespace(id=1, descricao="Camisa", tamanho="M", preco=50,
                                      estoque=5, categoria_id=1, marca_id=1, fornecedor_id=1,
                                      categoria=opcao, marca=opcao, fornecedor=opcao)
        self.controllers["produtos"].opcoes_cadastro.return_value = dict(categorias=[opcao], marcas=[opcao], fornecedores=[opcao])
        for modulo, c in self.controllers.items():
            c.listar.return_value = [self.produto if modulo == "produtos" else opcao]
            c.buscar_por_id.return_value = self.produto if modulo == "produtos" else opcao

    def csrf(self):
        with self.client.session_transaction() as session:
            session["csrf_token"] = "teste-csrf"
        return "teste-csrf"

    def dados_produto(self):
        return dict(descricao="Camisa", preco="59,90", tamanho="M", estoque="5",
                    categoria_id="1", marca_id="1", fornecedor_id="1", csrf_token=self.csrf())

    def test_paginas_dos_quatro_cruds(self):
        for modulo in self.controllers:
            for caminho in (f"/{modulo}/", f"/{modulo}/novo", f"/{modulo}/1/editar", f"/{modulo}/1/excluir"):
                with self.subTest(caminho=caminho):
                    response = self.client.get(caminho)
                    self.assertEqual(response.status_code, 200)
        self.session.close.assert_called()
        self.session.rollback.assert_called()

    def test_filtros_encaminhados_ao_controller(self):
        r = self.client.get("/produtos/?descricao=Camisa&categoria_id=1&marca_id=2&estoque=baixo")
        self.assertEqual(r.status_code, 200)
        self.controllers["produtos"].listar.assert_called_once_with(descricao="Camisa", categoria_id=1, marca_id=2, estoque="baixo")
        self.assertEqual(self.client.get("/produtos/?categoria_id=abc").status_code, 400)

    def test_cadastro_e_edicao_de_produto(self):
        r = self.client.post("/produtos/novo", data=self.dados_produto())
        self.assertEqual(r.status_code, 303)
        self.assertEqual(self.controllers["produtos"].cadastrar.call_args.kwargs["preco"], 59.9)
        html = self.client.get("/produtos/1/editar").get_data(as_text=True)
        self.assertIn('value="Camisa"', html)
        token = re.search(r'name="estoque_token" value="([^"]+)"', html).group(1)
        r = self.client.post("/produtos/1/editar", data=dict(self.dados_produto(), estoque_token=token))
        self.assertEqual(r.status_code, 303)
        self.assertEqual(self.controllers["produtos"].editar.call_args.kwargs["estoque_anterior"], 5)

    def test_token_estoque_adulterado_e_rejeitado(self):
        r = self.client.post("/produtos/1/editar", data=dict(self.dados_produto(), estoque_token="adulterado"))
        self.assertEqual(r.status_code, 400)
        self.controllers["produtos"].editar.assert_not_called()

    def test_cadastro_e_edicao_auxiliares(self):
        for modulo in ("categorias", "marcas", "fornecedores"):
            for path in (f"/{modulo}/novo", f"/{modulo}/1/editar"):
                with self.subTest(path=path):
                    self.assertEqual(self.client.post(path, data=dict(nome="Novo", csrf_token=self.csrf())).status_code, 303)

    def test_excluir_get_nao_escreve_post_requer_csrf(self):
        for modulo, c in self.controllers.items():
            with self.subTest(modulo=modulo):
                self.client.get(f"/{modulo}/1/excluir")
                c.excluir.assert_not_called()
                self.assertEqual(self.client.post(f"/{modulo}/1/excluir").status_code, 400)
                c.excluir.assert_not_called()
                self.assertEqual(self.client.post(f"/{modulo}/1/excluir", data=dict(csrf_token=self.csrf())).status_code, 303)
                c.excluir.assert_called_once_with(1)

    def test_bloqueio_exclusao_exibe_motivo(self):
        for modulo, c in self.controllers.items():
            c.excluir.side_effect = ValueError("Há registros vinculados. Exclusão bloqueada.")
            r = self.client.post(f"/{modulo}/1/excluir", data=dict(csrf_token=self.csrf()))
            self.assertEqual(r.status_code, 409)
            self.assertIn("registros vinculados", r.get_data(as_text=True))

    def test_id_inexistente_retorna_404(self):
        for modulo, c in self.controllers.items():
            c.buscar_por_id.return_value = None
            self.assertEqual(self.client.get(f"/{modulo}/999/editar").status_code, 404)
            self.assertEqual(self.client.get(f"/{modulo}/999/excluir").status_code, 404)

    def test_erro_preserva_formulario_e_escapa_html(self):
        c = self.controllers["categorias"]
        c.cadastrar.side_effect = ValueError("Nome inválido")
        r = self.client.post("/categorias/novo", data=dict(nome="<script>alert(1)</script>", csrf_token=self.csrf()))
        self.assertEqual(r.status_code, 400)
        self.assertIn("&lt;script&gt;", r.get_data(as_text=True))
        self.assertIn("Nome inválido", r.get_data(as_text=True))
