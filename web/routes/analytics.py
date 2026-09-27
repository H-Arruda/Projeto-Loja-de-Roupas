from datetime import date, datetime, time

from flask import Blueprint, render_template, request

from modulo_data_analysis.controller.analytics_controller import AnalyticsController
from web.db import get_db
from web.graficos import graficos_vendas

bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@bp.get("/")
def index():
    controller = AnalyticsController(get_db())
    inicio = request.args.get("data_inicio", "").strip()
    fim = request.args.get("data_fim", "").strip()
    erro = None
    periodo = None
    if inicio or fim:
        try:
            if not inicio or not fim:
                raise ValueError("Informe a data inicial e a data final.")
            try:
                dia_inicio = date.fromisoformat(inicio)
                dia_fim = date.fromisoformat(fim)
                if dia_inicio.isoformat() != inicio or dia_fim.isoformat() != fim:
                    raise ValueError()
            except ValueError:
                raise ValueError("Informe datas válidas no formato dia, mês e ano.") from None
            if dia_inicio > dia_fim:
                raise ValueError("A data inicial não pode ser posterior à data final.")
            limites = (datetime.combine(dia_inicio, time.min), datetime.combine(dia_fim, time.max))
            periodo = dict(vendas=controller.vendas_por_periodo(*limites),
                           faturamento=controller.faturamento_por_periodo(*limites))
        except ValueError as exc:
            erro = str(exc)

    dias = controller.vendas_por_dia()
    produtos = controller.produtos_mais_vendidos()
    categorias = controller.faturamento_por_categoria()
    marcas = controller.faturamento_por_marca()
    return render_template(
        "analytics.html", indicadores=controller.obter_indicadores(),
        graficos=graficos_vendas(dias, produtos, categorias, marcas),
        dias=dias, produtos=produtos, categorias=categorias, marcas=marcas,
        faturamento_produtos=controller.faturamento_por_produto(),
        vendas_categorias=controller.vendas_por_categoria(),
        vendas_marcas=controller.vendas_por_marca(),
        estoque_baixo=controller.estoque_baixo(), sem_estoque=controller.produtos_sem_estoque(),
        data_inicio=inicio, data_fim=fim, erro_periodo=erro, periodo=periodo,
    ), 400 if erro else 200
