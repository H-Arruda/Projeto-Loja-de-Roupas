from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from itsdangerous import BadSignature, URLSafeSerializer

from modulo_vendas.controller.produto_controller import ProdutoController
from web.db import get_db

bp = Blueprint("produtos", __name__, url_prefix="/produtos")


def _dados_formulario():
    try:
        return dict(
            descricao=request.form.get("descricao", ""),
            tamanho=request.form.get("tamanho", ""),
            preco=float(request.form.get("preco", "").strip().replace(",", ".")),
            estoque=int(request.form.get("estoque", "")),
            categoria_id=int(request.form.get("categoria_id", "")),
            marca_id=int(request.form.get("marca_id", "")),
            fornecedor_id=int(request.form.get("fornecedor_id", "")),
        )
    except ValueError:
        raise ValueError("Confira preço, estoque e opções selecionadas. Use preço sem separador de milhar, como 129,90.") from None


def _assinador():
    return URLSafeSerializer(current_app.secret_key, salt="edicao-estoque-produto")


@bp.get("/")
def lista():
    controller = ProdutoController(get_db())
    filtros = {campo: request.args.get(campo, "") for campo in ("descricao", "categoria_id", "marca_id", "estoque")}
    try:
        produtos = controller.listar(
            descricao=filtros["descricao"],
            categoria_id=int(filtros["categoria_id"]) if filtros["categoria_id"] else None,
            marca_id=int(filtros["marca_id"]) if filtros["marca_id"] else None,
            estoque=filtros["estoque"],
        )
    except ValueError:
        abort(400, description="Filtros inválidos. Confira categoria, marca e situação do estoque.")
    return render_template("produtos/lista.html", produtos=produtos, filtros=filtros,
                           **controller.opcoes_cadastro())


@bp.route("/novo", methods=["GET", "POST"])
def cadastro():
    controller = ProdutoController(get_db())
    erro = None
    if request.method == "POST":
        try:
            controller.cadastrar(**_dados_formulario())
        except ValueError as exc:
            erro = str(exc)
        else:
            flash("Produto cadastrado com sucesso.", "success")
            return redirect(url_for("produtos.lista"), code=303)
    return render_template("produtos/cadastro.html", dados=request.form, erro=erro,
                           **controller.opcoes_cadastro()), 400 if erro else 200


@bp.route("/<int:produto_id>/editar", methods=["GET", "POST"])
def editar(produto_id):
    controller = ProdutoController(get_db())
    produto = controller.buscar_por_id(produto_id)
    if produto is None:
        abort(404, description="Produto não encontrado.")
    erro = None
    if request.method == "POST":
        dados = request.form
        token = dados.get("estoque_token", "")
        try:
            origem = _assinador().loads(token)
            if origem["produto_id"] != produto_id:
                raise ValueError("Formulário inválido. Reabra a edição do produto.")
            controller.editar(produto_id, estoque_anterior=origem["estoque"], **_dados_formulario())
        except BadSignature:
            erro = "Formulário inválido. Reabra a edição do produto."
        except ValueError as exc:
            erro = str(exc)
        else:
            flash("Produto atualizado com sucesso.", "success")
            return redirect(url_for("produtos.lista"), code=303)
    else:
        dados = {campo: str(getattr(produto, campo)) for campo in (
            "descricao", "preco", "tamanho", "estoque", "categoria_id", "marca_id", "fornecedor_id")}
        token = _assinador().dumps(dict(produto_id=produto.id, estoque=produto.estoque))
    return render_template("produtos/editar.html", produto=produto, dados=dados,
                           estoque_token=token, erro=erro, **controller.opcoes_cadastro()), 400 if erro else 200


@bp.route("/<int:produto_id>/excluir", methods=["GET", "POST"])
def excluir(produto_id):
    controller = ProdutoController(get_db())
    produto = controller.buscar_por_id(produto_id)
    if produto is None:
        abort(404, description="Produto não encontrado.")
    erro = None
    if request.method == "POST":
        try:
            controller.excluir(produto_id)
        except ValueError as exc:
            erro = str(exc)
        else:
            flash("Produto excluído com sucesso.", "success")
            return redirect(url_for("produtos.lista"), code=303)
    return render_template("catalogos/excluir.html", nome=produto.descricao, titulo="produto",
                           voltar=url_for("produtos.lista"), erro=erro), 409 if erro else 200
