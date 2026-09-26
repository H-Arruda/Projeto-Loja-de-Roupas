from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from modulo_vendas.controller.fornecedor_controller import FornecedorController
from web.db import get_db

bp = Blueprint("fornecedores", __name__, url_prefix="/fornecedores")


@bp.get("/")
def lista():
    controller = FornecedorController(get_db())
    return render_template("catalogos/lista.html", registros=controller.listar(),
                           titulo="Fornecedores", modulo="fornecedores")


@bp.route("/novo", methods=["GET", "POST"])
def cadastro():
    controller = FornecedorController(get_db())
    erro = None
    nome = request.form.get("nome", "")
    if request.method == "POST":
        try:
            controller.cadastrar(nome)
        except ValueError as exc:
            erro = str(exc)
        else:
            flash("Cadastro realizado com sucesso.", "success")
            return redirect(url_for("fornecedores.lista"), code=303)
    return render_template("catalogos/formulario.html", titulo="Cadastrar fornecedor",
                           modulo="fornecedores", nome=nome, erro=erro), 400 if erro else 200


@bp.route("/<int:registro_id>/editar", methods=["GET", "POST"])
def editar(registro_id):
    controller = FornecedorController(get_db())
    registro = controller.buscar_por_id(registro_id)
    if registro is None:
        abort(404, description="Cadastro não encontrado.")
    erro = None
    nome = request.form.get("nome", "") if request.method == "POST" else registro.nome
    if request.method == "POST":
        try:
            controller.editar(registro_id, nome)
        except ValueError as exc:
            erro = str(exc)
        else:
            flash("Cadastro atualizado com sucesso.", "success")
            return redirect(url_for("fornecedores.lista"), code=303)
    return render_template("catalogos/formulario.html", titulo="Editar fornecedor",
                           modulo="fornecedores", nome=nome, erro=erro), 400 if erro else 200


@bp.route("/<int:registro_id>/excluir", methods=["GET", "POST"])
def excluir(registro_id):
    controller = FornecedorController(get_db())
    registro = controller.buscar_por_id(registro_id)
    if registro is None:
        abort(404, description="Cadastro não encontrado.")
    erro = None
    if request.method == "POST":
        try:
            controller.excluir(registro_id)
        except ValueError as exc:
            erro = str(exc)
        else:
            flash("Cadastro excluído com sucesso.", "success")
            return redirect(url_for("fornecedores.lista"), code=303)
    return render_template("catalogos/excluir.html", nome=registro.nome, titulo="fornecedor",
                           voltar=url_for("fornecedores.lista"), erro=erro), 409 if erro else 200
