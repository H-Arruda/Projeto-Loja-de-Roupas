import os
import runpy
import unittest
from unittest.mock import patch


class ConfiguracaoTest(unittest.TestCase):
    def test_senha_com_caracteres_reservados_nao_altera_host(self):
        # Segredo apenas sintético: não realiza conexão nem lê credenciais locais.
        with patch.dict(os.environ, {"DB_USER": "teste", "DB_PASSWORD": "senha@com:/#%",
                                     "DB_HOST": "127.0.0.1", "DB_PORT": "55432", "DB_NAME": "loja_test"}):
            with patch("sqlalchemy.create_engine") as criar:
                runpy.run_path("database/connection.py")
        url = criar.call_args.args[0]
        self.assertEqual(url.password, "senha@com:/#%")
        self.assertEqual(url.host, "127.0.0.1")
        self.assertEqual(url.port, 55432)
        self.assertEqual(url.database, "loja_test")
