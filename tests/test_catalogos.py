import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from sqlalchemy.exc import IntegrityError

os.environ.setdefault("DB_PORT", "5432")
from modulo_vendas.controller.produto_controller import ProdutoController
from modulo_vendas.controller.categoria_controller import CategoriaController
from modulo_vendas.controller.marca_controller import MarcaController
from modulo_vendas.controller.fornecedor_controller import FornecedorController


class ProdutoCRUDTest(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.controller = ProdutoController(self.session)
        self.dados = dict(descricao=" Camisa ", preco=50, tamanho=" M ", estoque=5,
                          categoria_id=1, marca_id=1, fornecedor_id=1)
        self.produto = SimpleNamespace(id=1, estoque=5)
        self.session.query.return_value.filter.return_value.populate_existing.return_value.with_for_update.return_value.one_or_none.return_value = self.produto
        self.session.query.return_value.filter.return_value.first.return_value = None

    def test_cadastrar_normaliza_dados(self):
        produto = self.controller.cadastrar(**self.dados)
        self.assertEqual(produto.descricao, "Camisa")
        self.assertEqual(produto.tamanho, "M")
        self.session.commit.assert_called_once()

    def test_editar_reutiliza_validacoes(self):
        for campo, valor in (("descricao", " "), ("tamanho", "x" * 21),
                             ("preco", float("nan")), ("preco", float("inf")),
                             ("preco", -1), ("estoque", -1), ("estoque", True)):
            for acao in (self.controller.cadastrar, lambda **d: self.controller.editar(1, **d)):
                self.session.reset_mock()
                with self.subTest(campo=campo, valor=valor), self.assertRaises(ValueError):
                    acao(**dict(self.dados, **{campo: valor}))
                self.session.rollback.assert_called_once()
                self.session.commit.assert_not_called()

    def test_editar_salva_campos(self):
        produto = self.controller.editar(1, **dict(self.dados, preco=70), estoque_anterior=5)
        self.assertEqual(produto.preco, 70)
        self.assertEqual(produto.descricao, "Camisa")
        self.session.commit.assert_called_once()

    def test_edicao_com_estoque_desatualizado_e_bloqueada(self):
        with self.assertRaisesRegex(ValueError, "estoque mudou"):
            self.controller.editar(1, **self.dados, estoque_anterior=8)
        self.session.commit.assert_not_called()
        self.session.rollback.assert_called_once()

    def test_referencia_inexistente_rejeitada(self):
        self.session.get.return_value = None
        with self.assertRaisesRegex(ValueError, "Categoria"):
            self.controller.cadastrar(**self.dados)

    def test_exclusao_sem_vinculos(self):
        self.controller.excluir(1)
        self.session.delete.assert_called_once_with(self.produto)
        self.session.commit.assert_called_once()

    def test_exclusao_vinculada_preserva_historico(self):
        self.session.query.return_value.filter.return_value.first.return_value = (1,)
        with self.assertRaisesRegex(ValueError, "item de venda"):
            self.controller.excluir(1)
        self.session.delete.assert_not_called()
        self.session.rollback.assert_called_once()

    def test_conflito_fk_concorrente_traduzido(self):
        erro = Exception("FK")
        erro.pgcode = "23503"
        self.session.commit.side_effect = IntegrityError("DELETE", {}, erro)
        with self.assertRaisesRegex(ValueError, "histórico"):
            self.controller.excluir(1)
        self.session.rollback.assert_called_once()

    def test_produto_inexistente(self):
        self.session.query.return_value.filter.return_value.populate_existing.return_value.with_for_update.return_value.one_or_none.return_value = None
        with self.assertRaisesRegex(ValueError, "não encontrado"):
            self.controller.excluir(999)


class CadastrosAuxiliaresTest(unittest.TestCase):
    controllers = (CategoriaController, MarcaController, FornecedorController)

    def test_cadastro_edicao_e_exclusao(self):
        for classe in self.controllers:
            with self.subTest(controller=classe.__name__):
                session = MagicMock()
                registro = SimpleNamespace(id=1, nome="Original")
                session.query.return_value.filter.return_value.populate_existing.return_value.with_for_update.return_value.one_or_none.return_value = registro
                session.query.return_value.filter.return_value.first.return_value = None
                c = classe(session)
                self.assertEqual(c.cadastrar(" Novo ").nome, "Novo")
                self.assertEqual(c.editar(1, " Editado ").nome, "Editado")
                c.excluir(1)
                session.delete.assert_called_once_with(registro)
                self.assertEqual(session.commit.call_count, 3)

    def test_validacao_compartilhada(self):
        for classe in self.controllers:
            for nome in (" ", "x" * 101):
                for editar in (False, True):
                    with self.subTest(controller=classe.__name__, editar=editar):
                        session = MagicMock()
                        c = classe(session)
                        with self.assertRaises(ValueError):
                            c.editar(1, nome) if editar else c.cadastrar(nome)
                        session.rollback.assert_called_once()
                        session.commit.assert_not_called()

    def test_exclusao_com_produtos_bloqueada(self):
        for classe in self.controllers:
            with self.subTest(controller=classe.__name__):
                session = MagicMock()
                session.query.return_value.filter.return_value.first.return_value = (1,)
                with self.assertRaisesRegex(ValueError, "produtos vinculados"):
                    classe(session).excluir(1)
                session.delete.assert_not_called()
                session.rollback.assert_called_once()

    def test_conflito_fk_concorrente(self):
        for classe in self.controllers:
            session = MagicMock()
            session.query.return_value.filter.return_value.first.return_value = None
            erro = Exception("FK")
            erro.pgcode = "23503"
            session.commit.side_effect = IntegrityError("DELETE", {}, erro)
            with self.subTest(controller=classe.__name__), self.assertRaisesRegex(ValueError, "produtos vinculados"):
                classe(session).excluir(1)
            session.rollback.assert_called_once()
