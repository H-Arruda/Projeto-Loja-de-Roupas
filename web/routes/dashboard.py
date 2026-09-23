from flask import Blueprint, render_template

from modulo_data_analysis.controller.analytics_controller import AnalyticsController
from web.db import get_db

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    analytics = AnalyticsController(get_db())
    return render_template(
        "dashboard.html",
        indicadores=analytics.obter_indicadores(),
        mais_vendidos=analytics.produtos_mais_vendidos(),
        estoque_baixo=analytics.estoque_baixo(),
    )
