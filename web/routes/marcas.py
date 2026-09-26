from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from modulo_vendas.controller.marca_controller import MarcaController
from web.db import get_db

bp = Blueprint("marcas", __name__, url_prefix="/marcas")


@bp.get("/")
def lista():
    controller = MarcaController(get_db())
    return render_template("catalogos/lista.html", registros=controller.listar(),
                           titulo="Marcas", modulo="marcas")


@bp.route("/novo", methods=["GET", "POST"])
def cadastro():
    controller = MarcaController(get_db())
    erro = None
    nome = request.form.get("nome", "")
    if request.method == "POST":
        try:
            controller.cadastrar(nome)
        except ValueError as exc:
            erro = str(exc)
        else:
            flash("Cadastro realizado com sucesso.", "success")
            return redirect(url_for("marcas.lista"), code=303)
    return render_template("catalogos/formulario.html", titulo="Cadastrar marca",
                           modulo="marcas", nome=nome, erro=erro), 400 if erro else 200


@bp.route("/<int:registro_id>/editar", methods=["GET", "POST"])
def editar(registro_id):
    controller = MarcaController(get_db())
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
            return redirect(url_for("marcas.lista"), code=303)
    return render_template("catalogos/formulario.html", titulo="Editar marca",
                           modulo="marcas", nome=nome, erro=erro), 400 if erro else 200


@bp.route("/<int:registro_id>/excluir", methods=["GET", "POST"])
def excluir(registro_id):
    controller = MarcaController(get_db())
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
            return redirect(url_for("marcas.lista"), code=303)
    return render_template("catalogos/excluir.html", nome=registro.nome, titulo="marca",
                           voltar=url_for("marcas.lista"), erro=erro), 409 if erro else 200
