from __future__ import annotations
import logging
import os
import dash_bootstrap_components as dbc
from dash import Dash
from flask import send_from_directory
from core.callbacks import register_callbacks
from core.dashboard_payload import build_dashboard_payload
from core.data import LOGO_ASSET_NAME, get_dataframe
from core.layout import build_layout

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def create_app() -> Dash:
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
    )
    app.title = "Dashboard PQC"

    logger.info("Carregando dados do banco de dados...")
    dataframe = get_dataframe()
    logger.info("%d registros carregados.", len(dataframe))

    initial_payload = build_dashboard_payload(None, None, None, None, None, None, None)
    app.layout = build_layout(app, dataframe, LOGO_ASSET_NAME, initial_payload=initial_payload)
    register_callbacks(app)

    logger.info("Aplicacao inicializada com sucesso")
    return app

try:
    app = create_app()
    server = app.server

    @server.route("/resumo")
    def executive_summary():
        return send_from_directory(_BASE_DIR, "ExecutiveSummary.html")

except Exception as exc:
    logger.error("Erro ao inicializar aplicacao: %s", exc, exc_info=True)
    raise

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8050"))
    app.run(debug=False, host="0.0.0.0", port=port)
