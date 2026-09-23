from math import isfinite

from modulo_vendas.model.categoria import Categoria
from modulo_vendas.model.marca import Marca
from modulo_vendas.model.fornecedor import Fornecedor
from modulo_vendas.model.produto import Produto


class ProdutoController:
    def __init__(self, session):
        self.session = session

    def cadastrar(
        self,
        descricao,
        preco,
        tamanho,
        estoque,
        categoria_id,
        marca_id,
        fornecedor_id
    ):
        descricao = descricao.strip()
        tamanho = tamanho.strip()
        if not descricao or len(descricao) > 180:
            raise ValueError("Informe uma descrição de até 180 caracteres.")
        if not tamanho or len(tamanho) > 20:
            raise ValueError("Informe um tamanho de até 20 caracteres.")
        if not isfinite(preco) or preco < 0:
            raise ValueError("O preço deve ser um número não negativo.")
        if type(estoque) is not int or estoque < 0:
            raise ValueError("O estoque deve ser um inteiro não negativo.")
        for model, registro_id, nome in (
            (Categoria, categoria_id, "Categoria"),
            (Marca, marca_id, "Marca"),
            (Fornecedor, fornecedor_id, "Fornecedor"),
        ):
            if self.session.get(model, registro_id) is None:
                raise ValueError(f"{nome} não encontrado(a).")

        produto = Produto(
            descricao=descricao,
            preco=preco,
            tamanho=tamanho,
            estoque=estoque,
            categoria_id=categoria_id,
            marca_id=marca_id,
            fornecedor_id=fornecedor_id
        )

        self.session.add(produto)
        self.session.commit()

        return produto

    def buscar_por_id(self, produto_id):
        return self.session.get(Produto, produto_id)

    def listar(self):
        return self.session.query(Produto).all()

    def opcoes_cadastro(self):
        return {
            "categorias": self.session.query(Categoria).order_by(Categoria.nome).all(),
            "marcas": self.session.query(Marca).order_by(Marca.nome).all(),
            "fornecedores": self.session.query(Fornecedor).order_by(Fornecedor.nome).all(),
        }
