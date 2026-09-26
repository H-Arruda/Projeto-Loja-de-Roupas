from math import isfinite

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from modulo_vendas.model.categoria import Categoria
from modulo_vendas.model.marca import Marca
from modulo_vendas.model.fornecedor import Fornecedor
from modulo_vendas.model.produto import Produto
from modulo_vendas.model.item_venda import ItemVenda


class ProdutoController:
    def __init__(self, session):
        self.session = session

    def _validar(self, descricao, preco, tamanho, estoque, categoria_id, marca_id, fornecedor_id):
        descricao = descricao.strip()
        tamanho = tamanho.strip()
        if not descricao or len(descricao) > 180:
            raise ValueError("Informe uma descrição de até 180 caracteres.")
        if not tamanho or len(tamanho) > 20:
            raise ValueError("Informe um tamanho de até 20 caracteres.")
        if not isfinite(preco) or preco < 0:
            raise ValueError("O preço deve ser um número não negativo.")
        if type(estoque) is not int or not 0 <= estoque <= 2147483647:
            raise ValueError("O estoque deve ser um inteiro entre 0 e 2147483647.")
        for model, registro_id, nome in (
            (Categoria, categoria_id, "Categoria"),
            (Marca, marca_id, "Marca"),
            (Fornecedor, fornecedor_id, "Fornecedor"),
        ):
            if type(registro_id) is not int or registro_id <= 0 or self.session.get(model, registro_id) is None:
                raise ValueError(f"{nome} não encontrado(a).")
        return dict(descricao=descricao, preco=preco, tamanho=tamanho, estoque=estoque,
                    categoria_id=categoria_id, marca_id=marca_id, fornecedor_id=fornecedor_id)

    def cadastrar(self, descricao, preco, tamanho, estoque, categoria_id, marca_id, fornecedor_id):
        try:
            dados = self._validar(descricao, preco, tamanho, estoque, categoria_id, marca_id, fornecedor_id)
            produto = Produto(**dados)
            self.session.add(produto)
            self.session.commit()
            return produto
        except IntegrityError as exc:
            self.session.rollback()
            if getattr(exc.orig, "pgcode", None) == "23503":
                raise ValueError("Categoria, marca ou fornecedor deixou de existir. Atualize as opções e tente novamente.") from exc
            raise
        except Exception:
            self.session.rollback()
            raise

    def editar(self, produto_id, descricao, preco, tamanho, estoque, categoria_id, marca_id,
               fornecedor_id, estoque_anterior=None):
        try:
            produto = self._buscar_bloqueado(produto_id)
            if estoque_anterior is not None and produto.estoque != estoque_anterior:
                raise ValueError("O estoque mudou desde a abertura do formulário. Reabra a edição para conferir o saldo atual.")
            dados = self._validar(descricao, preco, tamanho, estoque, categoria_id, marca_id, fornecedor_id)
            for campo, valor in dados.items():
                setattr(produto, campo, valor)
            self.session.commit()
            return produto
        except IntegrityError as exc:
            self.session.rollback()
            if getattr(exc.orig, "pgcode", None) == "23503":
                raise ValueError("Categoria, marca ou fornecedor deixou de existir. Atualize as opções e tente novamente.") from exc
            raise
        except Exception:
            self.session.rollback()
            raise

    def excluir(self, produto_id):
        mensagem = "Não é possível excluir este produto: ele está vinculado a item de venda. O histórico precisa ser preservado, inclusive em vendas canceladas."
        try:
            produto = self._buscar_bloqueado(produto_id)
            if self.session.query(ItemVenda.id).filter(ItemVenda.produto_id == produto_id).first():
                raise ValueError(mensagem)
            self.session.delete(produto)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            if getattr(exc.orig, "pgcode", None) == "23503":
                raise ValueError(mensagem) from exc
            raise
        except Exception:
            self.session.rollback()
            raise

    def _buscar_bloqueado(self, produto_id):
        produto = (self.session.query(Produto).filter(Produto.id == produto_id)
                   .populate_existing().with_for_update().one_or_none())
        if produto is None:
            raise ValueError("Produto não encontrado.")
        return produto

    def buscar_por_id(self, produto_id):
        return self.session.get(Produto, produto_id)

    def listar(self, descricao="", categoria_id=None, marca_id=None, estoque=""):
        query = self.session.query(Produto).options(
            joinedload(Produto.categoria), joinedload(Produto.marca), joinedload(Produto.fornecedor)
        )
        if descricao.strip():
            # Busca literal: % e _ digitados não viram curingas SQL.
            query = query.filter(Produto.descricao.icontains(descricao.strip(), autoescape=True))
        if categoria_id is not None:
            query = query.filter(Produto.categoria_id == categoria_id)
        if marca_id is not None:
            query = query.filter(Produto.marca_id == marca_id)
        if estoque == "normal":
            query = query.filter(Produto.estoque > 5)
        elif estoque == "baixo":
            query = query.filter(Produto.estoque.between(1, 5))
        elif estoque == "sem":
            query = query.filter(Produto.estoque == 0)
        elif estoque:
            raise ValueError("Filtro de estoque inválido.")
        return query.order_by(Produto.descricao, Produto.id).all()

    def opcoes_cadastro(self):
        return {
            "categorias": self.session.query(Categoria).order_by(Categoria.nome, Categoria.id).all(),
            "marcas": self.session.query(Marca).order_by(Marca.nome, Marca.id).all(),
            "fornecedores": self.session.query(Fornecedor).order_by(Fornecedor.nome, Fornecedor.id).all(),
        }
