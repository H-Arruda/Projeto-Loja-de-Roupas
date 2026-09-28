import unittest
from scripts.seed_demo import validar_destino


class SeedSegurancaTest(unittest.TestCase):
    def test_recusa_banco_principal_e_confirmacao_errada(self):
        for url, confirmacao in (("postgresql://localhost/loja", "loja"),
                                 ("postgresql://localhost/loja_test", "loja_test"),
                                 ("postgresql://localhost/loja_demo", "outra_demo"),
                                 ("sqlite:///loja_demo", "loja_demo")):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validar_destino(url, confirmacao)

    def test_aceita_somente_destino_demo_explicito(self):
        self.assertEqual(validar_destino("postgresql://localhost/loja_demo", "loja_demo").database, "loja_demo")
