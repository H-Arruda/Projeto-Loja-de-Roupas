from modulo_vendas.model.item_venda import ItemVenda
from modulo_vendas.model.produto import Produto
from modulo_vendas.model.venda import Venda, StatusVenda


class VendaController:
    def __init__(self, session):
        self.session = session

    def criar_venda(self):
        venda = Venda()

        self.session.add(venda)
        self.session.commit()

        return venda

    def adicionar_item(
        self,
        venda,
        produto_id,
        quantidade,
        valor=None
    ):
        if venda.status != StatusVenda.EM_LANCAMENTO.value:
            raise ValueError("A venda não está em lançamento.")
        if type(quantidade) is not int or quantidade <= 0:
            raise ValueError("A quantidade deve ser um inteiro positivo.")

        produto = self.session.get(Produto, produto_id)
        if produto is None:
            raise ValueError("Produto não encontrado.")

        # Mantido na assinatura por compatibilidade; o preço vem do banco.
        item = ItemVenda(
            produto_id=produto_id,
            quantidade=quantidade,
            valor=produto.preco
        )

        venda.itens.append(item)

        self.session.add(venda)
        self.session.commit()

        return item

    def confirmar_itens(self, venda):
        venda.confirmar_itens()
        self.session.commit()

    def confirmar_pagamento(self, venda):
        venda.confirmar_pagamento()
        self.session.commit()

    def cancelar(self, venda):
        venda.cancelar()
        self.session.commit()
