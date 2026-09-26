import os
import unittest
from sqlalchemy import event
from postgresql_base import PostgreSQLBase
from modulo_vendas.model import Produto, Categoria, Marca, Fornecedor
from modulo_vendas.controller.produto_controller import ProdutoController
from modulo_vendas.controller.categoria_controller import CategoriaController
from modulo_vendas.controller.marca_controller import MarcaController
from modulo_vendas.controller.fornecedor_controller import FornecedorController
from modulo_vendas.controller.venda_controller import VendaController


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "Configure TEST_DATABASE_URL para PostgreSQL dedicado *_test.")
class PostgreSQLCatalogosTest(PostgreSQLBase):
    def dados(self, session, **alteracoes):
        produto = session.get(Produto, self.produto_id)
        dados = dict(descricao="Blusa", preco=70, tamanho="P", estoque=3,
                     categoria_id=produto.categoria_id, marca_id=produto.marca_id,
                     fornecedor_id=produto.fornecedor_id)
        dados.update(alteracoes)
        return dados

    def test_crud_produto_e_referencias(self):
        with self.Session() as session:
            c = ProdutoController(session)
            dados = self.dados(session)
            produto = c.cadastrar(**dados)
            produto_id = produto.id
            c.editar(produto_id, **dict(dados, descricao="Blusa nova", estoque=4), estoque_anterior=3)
            session.expire_all()
            self.assertEqual(c.buscar_por_id(produto_id).descricao, "Blusa nova")
            self.assertEqual(c.buscar_por_id(produto_id).estoque, 4)
            with self.assertRaises(ValueError):
                c.editar(produto_id, **dict(dados, marca_id=999999))
            self.assertEqual(c.buscar_por_id(produto_id).estoque, 4)
            c.excluir(produto_id)
            self.assertIsNone(c.buscar_por_id(produto_id))

    def test_produto_vinculado_a_venda_cancelada_nao_pode_ser_excluido(self):
        with self.Session() as session:
            venda_controller = VendaController(session)
            venda = venda_controller.criar_venda()
            venda_controller.adicionar_item(venda, self.produto_id, 1)
            venda_controller.cancelar(venda)
            with self.assertRaisesRegex(ValueError, "item de venda"):
                ProdutoController(session).excluir(self.produto_id)
            self.assertIsNotNone(session.get(Produto, self.produto_id))

    def test_cruds_auxiliares_e_exclusao_com_vinculos(self):
        with self.Session() as session:
            produto = session.get(Produto, self.produto_id)
            for classe, campo in ((CategoriaController, "categoria_id"),
                                  (MarcaController, "marca_id"),
                                  (FornecedorController, "fornecedor_id")):
                c = classe(session)
                registro = c.cadastrar(" Novo ")
                registro_id = registro.id
                c.editar(registro_id, "Editado")
                session.expire_all()
                self.assertEqual(c.buscar_por_id(registro_id).nome, "Editado")
                c.excluir(registro_id)
                self.assertIsNone(c.buscar_por_id(registro_id))
                with self.assertRaisesRegex(ValueError, "produtos vinculados"):
                    c.excluir(getattr(produto, campo))

    def test_filtros_e_busca_literal(self):
        with self.Session() as session:
            c = ProdutoController(session)
            dados = self.dados(session)
            normal = c.cadastrar(**dict(dados, descricao="Camisa 100%", estoque=8))
            sem = c.cadastrar(**dict(dados, descricao="Calça", estoque=0))
            normal_id, sem_id = normal.id, sem.id
            self.assertEqual([p.id for p in c.listar(descricao="100%")], [normal_id])
            self.assertEqual([p.id for p in c.listar(estoque="sem")], [sem_id])
            self.assertEqual([p.id for p in c.listar(estoque="normal")], [normal_id])
            self.assertEqual([p.id for p in c.listar(descricao="CAMISA", estoque="baixo",
                                                    categoria_id=dados["categoria_id"], marca_id=dados["marca_id"])], [self.produto_id])
            self.assertEqual(c.listar(categoria_id=999999), [])
            with self.assertRaises(ValueError):
                c.listar(estoque="invalido")

    def test_listagem_nao_executa_consultas_por_relacionamento(self):
        with self.Session() as session:
            c = ProdutoController(session)
            dados = self.dados(session)
            for numero in range(3):
                c.cadastrar(**dict(dados, descricao=f"Produto {numero}"))
        consultas = []
        def contar(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith("SELECT"):
                consultas.append(statement)
        event.listen(self.engine, "before_cursor_execute", contar)
        try:
            with self.Session() as session:
                produtos = ProdutoController(session).listar()
                for produto in produtos:
                    _ = (produto.categoria.nome, produto.marca.nome, produto.fornecedor.nome)
                self.assertEqual(len(produtos), 4)
                self.assertEqual(len(consultas), 1)
        finally:
            event.remove(self.engine, "before_cursor_execute", contar)

    def test_edicao_aberta_antes_de_baixa_nao_sobrescreve_estoque(self):
        with self.Session() as primeira, self.Session() as segunda:
            dados = self.dados(primeira, estoque=5)
            c = VendaController(segunda)
            venda = c.criar_venda()
            c.adicionar_item(venda, self.produto_id, 2)
            c.confirmar_itens(venda)
            c.confirmar_pagamento(venda)
            with self.assertRaisesRegex(ValueError, "estoque mudou"):
                ProdutoController(primeira).editar(self.produto_id, **dados, estoque_anterior=5)
            self.assertEqual(primeira.get(Produto, self.produto_id).estoque, 3)
