"""Regras de venda sem acesso ao banco: python -m unittest discover -s tests -v."""
import os
import unittest
from unittest.mock import MagicMock

# A importação dos Models cria o engine, mas estes testes não abrem conexões.
os.environ.setdefault("DB_PORT", "5432")

from sqlalchemy.orm import make_transient_to_detached
from modulo_vendas.model.produto import Produto
from modulo_vendas.model.item_venda import ItemVenda
from modulo_vendas.model.venda import Venda, StatusVenda
from modulo_vendas.controller.venda_controller import VendaController


class RegrasVendaTest(unittest.TestCase):
    def setUp(self):
        self.produto = Produto(id=1, descricao="Camisa", preco=50, estoque=5)
        self.venda = Venda(status=StatusVenda.EM_LANCAMENTO.value, total=0)

    def item(self, quantidade=1, produto=None):
        produto = produto or self.produto
        return ItemVenda(produto_id=produto.id, produto=produto,
                         quantidade=quantidade, valor=produto.preco)

    def test_total_atualizado_ao_adicionar_alterar_remover(self):
        item = self.item(2)
        self.venda.adicionar_item(item)
        self.assertEqual(self.venda.total, 100)
        self.produto.preco = 99
        self.venda.alterar_quantidade(item, 3)
        self.assertEqual(self.venda.total, 150)
        self.venda.alterar_quantidade(item, 1)
        self.assertEqual(self.venda.total, 50)
        self.venda.remover_item(item)
        self.assertEqual(self.venda.total, 0)
        self.assertEqual(self.produto.estoque, 5)

    def test_quantidades_invalidas_nao_modificam_carrinho(self):
        for quantidade in (0, -1, True, 1.5, "2", None):
            with self.subTest(quantidade=quantidade), self.assertRaises(ValueError):
                self.venda.adicionar_item(self.item(quantidade))
        self.assertEqual(self.venda.itens, [])

    def test_venda_vazia_nao_confirma(self):
        with self.assertRaisesRegex(ValueError, "pelo menos um"):
            self.venda.confirmar_itens()
        self.assertEqual(self.venda.status, StatusVenda.EM_LANCAMENTO.value)

    def test_produto_repetido_respeita_estoque_acumulado(self):
        self.venda.adicionar_item(self.item(3))
        with self.assertRaisesRegex(ValueError, "Estoque insuficiente"):
            self.venda.adicionar_item(self.item(3))
        self.assertEqual(len(self.venda.itens), 1)
        self.assertEqual(self.venda.total, 150)

    def test_aumento_considera_outras_linhas_do_produto(self):
        item = self.item(2)
        self.venda.adicionar_item(item)
        self.venda.adicionar_item(self.item(2))
        with self.assertRaises(ValueError):
            self.venda.alterar_quantidade(item, 4)
        self.assertEqual(item.quantidade, 2)
        self.assertEqual(self.venda.total, 200)

    def test_item_de_outra_venda_rejeitado(self):
        for operacao in (lambda: self.venda.remover_item(self.item()),
                         lambda: self.venda.alterar_quantidade(self.item(), 2)):
            with self.assertRaisesRegex(ValueError, "nesta venda"):
                operacao()

    def test_baixa_somente_no_pagamento_e_sem_duplicacao(self):
        self.venda.adicionar_item(self.item(2))
        self.venda.adicionar_item(self.item(1))
        self.venda.confirmar_itens()
        self.assertEqual(self.produto.estoque, 5)
        self.venda.confirmar_pagamento()
        self.assertEqual(self.produto.estoque, 2)
        self.assertEqual(self.venda.status, StatusVenda.FINALIZADA.value)
        with self.assertRaises(ValueError):
            self.venda.confirmar_pagamento()
        self.assertEqual(self.produto.estoque, 2)

    def test_pagamento_revalida_estoque_sem_baixa_parcial(self):
        outro = Produto(id=2, descricao="Calça", preco=90, estoque=2)
        self.venda.adicionar_item(self.item(2))
        self.venda.adicionar_item(self.item(2, outro))
        self.venda.confirmar_itens()
        outro.estoque = 1
        with self.assertRaises(ValueError):
            self.venda.confirmar_pagamento()
        self.assertEqual(self.produto.estoque, 5)
        self.assertEqual(outro.estoque, 1)
        self.assertEqual(self.venda.status, StatusVenda.AGUARDANDO_PAGAMENTO.value)

    def test_mutacoes_bloqueadas_fora_de_lancamento(self):
        item = self.item()
        self.venda.adicionar_item(item)
        for status in (StatusVenda.AGUARDANDO_PAGAMENTO, StatusVenda.FINALIZADA,
                       StatusVenda.CANCELADA):
            self.venda.status = status.value
            for acao in (lambda: self.venda.adicionar_item(self.item()),
                         lambda: self.venda.alterar_quantidade(item, 2),
                         lambda: self.venda.remover_item(item)):
                with self.subTest(status=status), self.assertRaises(ValueError):
                    acao()
        self.assertEqual(self.venda.total, 50)

    def test_cancelamento_nao_altera_estoque(self):
        self.venda.adicionar_item(self.item(2))
        self.venda.confirmar_itens()
        self.venda.cancelar()
        self.assertEqual(self.produto.estoque, 5)
        with self.assertRaises(ValueError):
            self.venda.confirmar_pagamento()

    def test_finalizada_nao_pode_ser_cancelada(self):
        self.venda.adicionar_item(self.item())
        self.venda.confirmar_itens()
        self.venda.confirmar_pagamento()
        with self.assertRaises(ValueError):
            self.venda.cancelar()


class ControllerVendaTest(unittest.TestCase):
    """Contratos/rollback com sessão simulada; bloqueios reais são testados à parte."""
    def setUp(self):
        self.session = MagicMock()
        self.controller = VendaController(self.session)
        self.venda = Venda(id=1, total=0, status=StatusVenda.EM_LANCAMENTO.value)
        self.venda.itens = []
        make_transient_to_detached(self.venda)
        self.session.query.return_value.options.return_value.filter.return_value.populate_existing.return_value.with_for_update.return_value.one_or_none.return_value = self.venda
        self.produto = Produto(id=1, descricao="Camisa", preco=50, estoque=5)
        self.session.query.return_value.filter.return_value.order_by.return_value.populate_existing.return_value.with_for_update.return_value.all.return_value = [self.produto]

    def test_preco_enviado_e_ignorado(self):
        item = self.controller.adicionar_item(self.venda, 1, 2, valor=0.01)
        self.assertEqual(item.valor, 50)
        self.assertEqual(self.venda.total, 100)
        self.session.commit.assert_called_once()

    def test_erro_de_negocio_executa_rollback(self):
        with self.assertRaises(ValueError):
            self.controller.adicionar_item(self.venda, 1, 0)
        self.session.rollback.assert_called_once()
        self.session.commit.assert_not_called()

    def test_falha_no_commit_executa_rollback(self):
        self.session.commit.side_effect = RuntimeError("falha simulada")
        with self.assertRaises(RuntimeError):
            self.controller.adicionar_item(self.venda, 1, 1)
        self.session.rollback.assert_called_once()

    def test_criacao_confirma_transacao(self):
        venda = self.controller.criar_venda()
        self.assertIsInstance(venda, Venda)
        self.session.add.assert_called_once_with(venda)
        self.session.commit.assert_called_once()

    def test_item_de_outra_venda_nao_e_removido(self):
        with self.assertRaises(ValueError):
            self.controller.remover_item(self.venda, 999)
        self.session.delete.assert_not_called()
        self.session.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
