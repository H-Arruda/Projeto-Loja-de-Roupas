import os
import secrets

from dotenv import load_dotenv
from flask import Flask, abort, render_template, request, session
from sqlalchemy.exc import SQLAlchemyError


def create_app():
    load_dotenv()
    app = Flask(__name__)
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("Configure SECRET_KEY no arquivo .env antes de iniciar o Flask.")
    app.config.update(
        SECRET_KEY=secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=64 * 1024,
    )

    from web.db import close_db
    from web.routes.dashboard import bp as dashboard_bp
    from web.routes.produtos import bp as produtos_bp

    from web.routes.categorias import bp as categorias_bp
    from web.routes.marcas import bp as marcas_bp
    from web.routes.fornecedores import bp as fornecedores_bp

    from web.routes.vendas import bp as vendas_bp

    app.teardown_appcontext(close_db)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(vendas_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(marcas_bp)
    app.register_blueprint(fornecedores_bp)

    @app.before_request
    def protect_forms():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)
        if request.method == "POST":
            token = request.form.get("csrf_token", "")
            if not secrets.compare_digest(token.encode("utf-8"), session["csrf_token"].encode("utf-8")):
                abort(400, description="Formulário expirado. Recarregue a página e tente novamente.")

    @app.template_filter("brl")
    def brl(value):
        formatted = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        return f"R$ {formatted}"

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        # Não registrar parâmetros SQL nem valores dos formulários.
        app.logger.error("Falha de banco: %s", type(error).__name__)
        return render_template(
            "base.html", error_message="Não foi possível concluir a operação. Verifique a conexão e a configuração do banco."
        ), 503

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def http_error(error):
        return render_template("base.html", error_message=error.description), error.code

    return app
