from modulo_vendas.model.item_venda import ItemVenda
from modulo_vendas.model.venda import Venda


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
        valor
    ):
        item = ItemVenda(
            produto_id=produto_id,
            quantidade=quantidade,
            valor=valor
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