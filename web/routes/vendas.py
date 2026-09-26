from datetime import datetime, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from modulo_vendas.controller.produto_controller import ProdutoController
from modulo_vendas.controller.venda_controller import VendaController
from modulo_vendas.model.venda import StatusVenda
from web.db import get_db

bp = Blueprint("vendas", __name__, url_prefix="/vendas")


def _obter_venda(venda_id):
    venda = VendaController(get_db()).obter_detalhes(venda_id)
    if venda is None:
        abort(404, description="Venda não encontrada.")
    return venda


def _resumo(venda):
    return {
        "itens": [{"item": item, "subtotal": item.calcular_subtotal()} for item in venda.itens],
        "unidades": sum(item.quantidade for item in venda.itens),
        "em_lancamento": venda.status == StatusVenda.EM_LANCAMENTO.value,
        "aguardando_pagamento": venda.status == StatusVenda.AGUARDANDO_PAGAMENTO.value,
        "pode_cancelar": venda.status in (StatusVenda.EM_LANCAMENTO.value, StatusVenda.AGUARDANDO_PAGAMENTO.value),
    }


@bp.get("/")
def historico():
    filtros = {campo: request.args.get(campo, "") for campo in ("inicio", "fim", "status")}
    erro = None
    registros = []
    try:
        inicio = datetime.strptime(filtros["inicio"], "%Y-%m-%d") if filtros["inicio"] else None
        fim = datetime.strptime(filtros["fim"], "%Y-%m-%d") + timedelta(days=1) if filtros["fim"] else None
    except (ValueError, OverflowError):
        erro = "Informe datas válidas para o período."
    if not erro:
        try:
            vendas = VendaController(get_db()).listar(inicio, fim, filtros["status"] or None)
            registros = [{"venda": venda, "unidades": sum(item.quantidade for item in venda.itens)} for venda in vendas]
        except ValueError as exc:
            erro = str(exc)
    return render_template("vendas/historico.html", registros=registros, filtros=filtros,
                           estados=StatusVenda, erro=erro), 400 if erro else 200


@bp.get("/nova")
def nova():
    busca = request.args.get("q", "").strip()
    produtos = ProdutoController(get_db()).listar(descricao=busca)
    return render_template("vendas/pdv.html", venda=None, produtos=produtos, busca=busca)


@bp.post("/nova")
def criar():
    venda = VendaController(get_db()).criar_venda()
    flash("Venda criada. Adicione os produtos ao carrinho.", "success")
    return redirect(url_for("vendas.pdv", venda_id=venda.id, q=request.form.get("q", "")), code=303)


@bp.get("/<int:venda_id>/pdv")
def pdv(venda_id):
    venda = _obter_venda(venda_id)
    busca = request.args.get("q", "").strip()
    produtos = ProdutoController(get_db()).listar(descricao=busca)
    return render_template("vendas/pdv.html", venda=venda, produtos=produtos, busca=busca, **_resumo(venda))


@bp.get("/<int:venda_id>")
def detalhes(venda_id):
    venda = _obter_venda(venda_id)
    return render_template("vendas/detalhes.html", venda=venda, **_resumo(venda))


def _executar(venda_id, operacao, mensagem):
    venda = _obter_venda(venda_id)
    try:
        operacao(VendaController(get_db()), venda)
    except ValueError as exc:
        get_db().rollback()
        flash(str(exc), "error")
    else:
        flash(mensagem, "success")
    return redirect(url_for("vendas.pdv", venda_id=venda_id, q=request.form.get("q", "")), code=303)


@bp.post("/<int:venda_id>/itens")
def adicionar_item(venda_id):
    def adicionar(controller, venda):
        try:
            produto_id = int(request.form.get("produto_id", ""))
            quantidade = int(request.form.get("quantidade", ""))
        except ValueError:
            raise ValueError("Informe um produto e uma quantidade inteira positiva.") from None
        # Nenhum preço ou total enviado pelo navegador é utilizado.
        controller.adicionar_item(venda, produto_id, quantidade)
    return _executar(venda_id, adicionar, "Produto adicionado ao carrinho.")


@bp.post("/<int:venda_id>/itens/<int:item_id>/quantidade")
def quantidade(venda_id, item_id):
    def atualizar(controller, venda):
        acao = request.form.get("acao", "definir")
        if acao in ("aumentar", "diminuir"):
            controller.ajustar_quantidade(venda, item_id, 1 if acao == "aumentar" else -1)
        elif acao == "definir":
            try:
                quantidade = int(request.form.get("quantidade", ""))
            except ValueError:
                raise ValueError("A quantidade deve ser um inteiro positivo.") from None
            controller.alterar_quantidade(venda, item_id, quantidade)
        else:
            raise ValueError("Ação de quantidade inválida.")
    return _executar(venda_id, atualizar, "Quantidade atualizada.")


@bp.post("/<int:venda_id>/itens/<int:item_id>/remover")
def remover_item(venda_id, item_id):
    return _executar(venda_id, lambda c, v: c.remover_item(v, item_id), "Item removido do carrinho.")


@bp.post("/<int:venda_id>/confirmar-itens")
def confirmar_itens(venda_id):
    return _executar(venda_id, lambda c, v: c.confirmar_itens(v), "Itens confirmados. A venda aguarda pagamento.")


@bp.post("/<int:venda_id>/confirmar-pagamento")
def confirmar_pagamento(venda_id):
    return _executar(venda_id, lambda c, v: c.confirmar_pagamento(v), "Venda finalizada. Pagamento confirmado e estoque atualizado.")


@bp.post("/<int:venda_id>/cancelar")
def cancelar(venda_id):
    return _executar(venda_id, lambda c, v: c.cancelar(v), "Venda cancelada. Nenhuma baixa de estoque foi realizada.")
