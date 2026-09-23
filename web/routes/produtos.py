from flask import Blueprint, flash, redirect, render_template, request, url_for

from modulo_vendas.controller.produto_controller import ProdutoController
from web.db import get_db

bp = Blueprint("produtos", __name__, url_prefix="/produtos")


@bp.get("/")
def lista():
    controller = ProdutoController(get_db())
    return render_template("produtos/lista.html", produtos=controller.listar())


@bp.route("/novo", methods=["GET", "POST"])
def cadastro():
    db = get_db()
    controller = ProdutoController(db)
    erro = None
    if request.method == "POST":
        try:
            preco = float(request.form.get("preco", "").strip().replace(",", "."))
            estoque = int(request.form.get("estoque", ""))
            categoria_id = int(request.form.get("categoria_id", ""))
            marca_id = int(request.form.get("marca_id", ""))
            fornecedor_id = int(request.form.get("fornecedor_id", ""))
        except ValueError:
            erro = "Confira o preço, o estoque e as opções selecionadas. Use preço sem separador de milhar, como 129,90."
        else:
            try:
                controller.cadastrar(
                    descricao=request.form.get("descricao", ""),
                    preco=preco,
                    tamanho=request.form.get("tamanho", ""),
                    estoque=estoque,
                    categoria_id=categoria_id,
                    marca_id=marca_id,
                    fornecedor_id=fornecedor_id,
                )
            except ValueError as exc:
                db.rollback()
                erro = str(exc)
            else:
                flash("Produto cadastrado com sucesso.", "success")
                return redirect(url_for("produtos.lista"), code=303)

    return render_template(
        "produtos/cadastro.html",
        dados=request.form,
        erro=erro,
        **controller.opcoes_cadastro(),
    ), 400 if erro else 200
