from flask import Blueprint, render_template

from modulo_data_analysis.controller.analytics_controller import AnalyticsController
from web.db import get_db
from web.graficos import graficos_vendas

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    analytics = AnalyticsController(get_db())
    mais_vendidos = analytics.produtos_mais_vendidos()
    graficos = graficos_vendas(
        analytics.vendas_por_dia(), mais_vendidos,
        analytics.faturamento_por_categoria(), analytics.faturamento_por_marca(),
    )
    return render_template(
        "dashboard.html",
        indicadores=analytics.obter_indicadores(),
        graficos=graficos,
        estoque_baixo=analytics.estoque_baixo(),
    )
