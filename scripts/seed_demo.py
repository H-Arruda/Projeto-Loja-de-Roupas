"""Carga opcional, atômica e exclusiva de banco vazio com nome terminado em _demo."""
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from database.connection import Base
from modulo_vendas.model import Categoria, Marca, Fornecedor, Produto, Venda, ItemVenda
from modulo_vendas.controller.categoria_controller import CategoriaController
from modulo_vendas.controller.marca_controller import MarcaController
from modulo_vendas.controller.fornecedor_controller import FornecedorController
from modulo_vendas.controller.produto_controller import ProdutoController
from modulo_vendas.controller.venda_controller import VendaController


def validar_destino(url, confirmacao):
    destino = make_url(url)
    if destino.get_backend_name() != "postgresql" or not (destino.database or "").endswith("_demo"):
        raise ValueError("Use somente um banco PostgreSQL exclusivo com nome terminado em _demo.")
    if confirmacao != destino.database:
        raise ValueError("Informe --confirm com o nome exato do banco de demonstração.")
    return destino


def preencher(session, hoje=None):
    """Chamado dentro de uma transação externa; não limpa nem sobrescreve registros."""
    # Serializa duas execuções deste script antes da checagem de banco vazio.
    session.execute(text("SELECT pg_advisory_xact_lock(60260927)"))
    for model in (Categoria, Marca, Fornecedor, Produto, Venda, ItemVenda):
        if session.execute(select(model.id).limit(1)).first():
            raise ValueError("O banco já contém registros. Nenhum dado foi alterado; use um banco _demo vazio.")
    categorias = [CategoriaController(session).cadastrar(nome) for nome in ("Camisetas", "Camisas", "Calças", "Vestidos", "Acessórios")]
    marcas = [MarcaController(session).cadastrar(nome) for nome in ("Essencial", "Horizonte", "Ateliê Urbano")]
    fornecedores = [FornecedorController(session).cadastrar(nome) for nome in ("Malharia Serra", "Confecções Aurora", "Distribuidora Central")]
    catalogo = [
        ("Camiseta básica algodão", "M", 59.90, 25, 0, 0, 0),
        ("Camiseta básica algodão", "G", 59.90, 18, 0, 0, 0),
        ("Camiseta listrada", "P", 79.90, 12, 0, 1, 0),
        ("Camisa de linho", "M", 159.90, 14, 1, 2, 1),
        ("Camisa casual manga curta", "G", 119.90, 18, 1, 1, 1),
        ("Camisa social slim", "M", 139.90, 10, 1, 0, 1),
        ("Calça jeans reta", "40", 189.90, 15, 2, 1, 1),
        ("Calça sarja", "42", 169.90, 12, 2, 0, 1),
        ("Calça pantalona", "M", 179.90, 9, 2, 2, 1),
        ("Vestido midi floral", "M", 219.90, 10, 3, 2, 1),
        ("Vestido casual", "P", 149.90, 8, 3, 1, 1),
        ("Vestido longo", "G", 249.90, 4, 3, 2, 1),
        ("Cinto couro", "Único", 69.90, 20, 4, 0, 2),
        ("Lenço estampado", "Único", 39.90, 3, 4, 2, 2),
        ("Boné casual", "Único", 49.90, 0, 4, 1, 2),
    ]
    produtos = [ProdutoController(session).cadastrar(d, p, t, e, categorias[c].id, marcas[m].id, fornecedores[f].id)
                for d,t,p,e,c,m,f in catalogo]
    hoje = hoje or datetime.now().date()
    pedidos = [(21, [(0,2),(12,1)]), (19, [(3,1),(6,1)]), (17, [(9,1),(13,1)]),
               (14, [(1,2),(4,1)]), (12, [(7,1),(12,2)]), (10, [(10,1),(2,1)]),
               (8, [(5,1),(8,1)]), (6, [(0,3),(4,1)]), (4, [(9,2),(12,1)]),
               (2, [(6,2),(3,1)]), (1, [(2,2),(10,1)]), (0, [(1,1),(7,1)])]
    total = 0
    for dias, itens in pedidos:
        controller = VendaController(session)
        venda = controller.criar_venda()
        for indice, quantidade in itens:
            controller.adicionar_item(venda, produtos[indice].id, quantidade)
        controller.confirmar_itens(venda)
        controller.confirmar_pagamento(venda)
        venda.data = datetime.combine(hoje - timedelta(days=dias), datetime.min.time()).replace(hour=10 + dias % 7, minute=15)
        session.commit()
        total += venda.total
    return dict(produtos=len(produtos), vendas=len(pedidos), faturamento=round(total, 2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", required=True, help="Nome exato do banco *_demo vazio")
    args = parser.parse_args()
    url = os.getenv("DEMO_DATABASE_URL")
    if not url:
        parser.error("Configure DEMO_DATABASE_URL no .env; não há fallback para o banco principal.")
    try:
        destino = validar_destino(url, args.confirm)
        engine = create_engine(destino, connect_args={"connect_timeout": 5})
        try:
            with engine.begin() as conn:
                # Somente cria as tabelas dos Models atuais no banco de demonstração.
                Base.metadata.create_all(conn)
                with Session(bind=conn, join_transaction_mode="create_savepoint", autoflush=False) as session:
                    resumo = preencher(session)
            print(f"Demonstração preparada em {destino.database}: {resumo['produtos']} produtos, {resumo['vendas']} vendas; faturamento R$ {resumo['faturamento']:.2f}.")
        finally:
            engine.dispose()
    except ValueError as exc:
        parser.exit(1, str(exc) + "\n")
    except Exception as exc:
        # Não imprimir URL, senha nem parâmetros SQL.
        parser.exit(1, f"Carga cancelada ({type(exc).__name__}). Confira a conexão; a transação foi revertida.\n")


if __name__ == "__main__":
    main()
