from contextlib import contextmanager

from sqlalchemy import inspect
from sqlalchemy.orm import selectinload

from modulo_vendas.model.item_venda import ItemVenda
from modulo_vendas.model.produto import Produto
from modulo_vendas.model.venda import Venda


class VendaController:
    def __init__(self, session):
        self.session = session

    def criar_venda(self):
        try:
            venda = Venda()
            self.session.add(venda)
            self.session.commit()
            return venda
        except Exception:
            self.session.rollback()
            raise

    def buscar_por_id(self, venda_id):
        return self.session.get(Venda, venda_id)

    def adicionar_item(self, venda, produto_id, quantidade, valor=None):
        with self._operacao(venda) as venda:
            produtos = self._bloquear_produtos(venda, produto_id)
            produto = produtos.get(produto_id)
            if produto is None:
                raise ValueError("Produto não encontrado.")
            # Compatibilidade: o argumento valor é ignorado; preço vem do banco.
            item = ItemVenda(
                produto_id=produto.id,
                produto=produto,
                quantidade=quantidade,
                valor=produto.preco,
            )
            venda.adicionar_item(item)
        return item

    def alterar_quantidade(self, venda, item_id, quantidade):
        with self._operacao(venda) as venda:
            self._bloquear_produtos(venda)
            item = self._buscar_item(venda, item_id)
            venda.alterar_quantidade(item, quantidade)
        return item

    def remover_item(self, venda, item_id):
        with self._operacao(venda) as venda:
            item = self._buscar_item(venda, item_id)
            venda.remover_item(item)
            # A FK venda_id é obrigatória: remover a linha, sem gravar FK nula.
            self.session.delete(item)

    def confirmar_itens(self, venda):
        with self._operacao(venda) as venda:
            self._bloquear_produtos(venda)
            venda.confirmar_itens()

    def confirmar_pagamento(self, venda):
        with self._operacao(venda) as venda:
            self._bloquear_produtos(venda)
            venda.confirmar_pagamento()

    def cancelar(self, venda):
        with self._operacao(venda) as venda:
            venda.cancelar()

    @contextmanager
    def _operacao(self, venda):
        """Uma operação por transação, com releitura protegida contra concorrência.

        Use uma sessão dedicada à operação/requisição, como na camada web.
        O bloqueio permanece até commit ou rollback.
        """
        try:
            identidade = inspect(venda).identity
            if identidade is None:
                raise ValueError("A venda precisa estar cadastrada.")
            atual = (
                self.session.query(Venda)
                .options(selectinload(Venda.itens))
                .filter(Venda.id == identidade[0])
                .populate_existing()
                .with_for_update()
                .one_or_none()
            )
            if atual is None:
                raise ValueError("Venda não encontrada.")
            yield atual
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def _bloquear_produtos(self, venda, produto_id=None):
        ids = {item.produto_id for item in venda.itens}
        if produto_id is not None:
            ids.add(produto_id)
        if not ids:
            return {}
        produtos = (
            self.session.query(Produto)
            .filter(Produto.id.in_(ids))
            .order_by(Produto.id)
            .populate_existing()
            .with_for_update()
            .all()
        )
        return {produto.id: produto for produto in produtos}

    @staticmethod
    def _buscar_item(venda, item_id):
        item = next((item for item in venda.itens if item.id == item_id), None)
        if item is None:
            raise ValueError("Item não encontrado nesta venda.")
        return item
