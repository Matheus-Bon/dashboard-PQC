from __future__ import annotations
import time as _time
from functools import lru_cache
from dash import Input, Output, no_update
from core.dashboard_payload import build_dashboard_payload
from core.data import get_dataframe, get_dataset_version, invalidate_cache, run_etl

def _default_latency_range(df):
    if df.empty or "response_ms" not in df.columns:
        return [0, 1000]
    max_latency = float(df["response_ms"].max())
    upper = float(df["response_ms"].quantile(0.99))
    return [0, upper if upper > 0 else max_latency]

def _normalize_multi(value):
    if not value:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return (str(value),)

def _normalize_latency(value):
    if not value or not isinstance(value, (list, tuple)) or len(value) != 2:
        return (0.0, 1000.0)
    return (float(value[0]), float(value[1]))

@lru_cache(maxsize=64)
def _cached_dashboard_payload(
    dataset_version,
    envs,
    libs,
    ops,
    env_types,
    processors,
    operating_systems,
    latency_range,
    crypto_types,
):
    return build_dashboard_payload(
        list(envs),
        list(libs),
        list(ops),
        list(env_types),
        list(processors),
        list(operating_systems),
        list(latency_range),
        list(crypto_types),
    )

def register_callbacks(app):
    @app.callback(
        Output("etl-refresh-ts", "data"),
        Output("etl-refresh-status", "children"),
        Output("etl-refresh-status", "color"),
        Output("etl-refresh-status", "is_open"),
        Input("etl-refresh-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def etl_refresh(_n_clicks):
        try:
            result = run_etl()
            if result["status"] != "ok":
                return _time.time(), f"Erro: {result['message']}", "danger", True
            invalidate_cache()
            _cached_dashboard_payload.cache_clear()
            df = get_dataframe()
            n_rows = len(df)
            ts = _time.time()
            msg = f"Sucesso: ETL concluído — {n_rows:,} registros disponíveis no dashboard."
            return ts, msg, "success", True
        except Exception as exc:  # noqa: BLE001
            return _time.time(), f"Erro ao executar ETL: {exc}", "danger", True

    from dash import ctx
    @app.callback(
        Output("env-filter", "value"),
        Output("lib-filter", "value"),
        Output("op-filter", "value"),
        Output("env-type-filter", "value"),
        Input("clear-filters", "n_clicks"),
        Input("btn-preset-pix", "n_clicks"),
        Input("btn-preset-contract", "n_clicks"),
        prevent_initial_call=True,
    )
    def handle_filters_and_presets(btn_clear, btn_pix, btn_contract):
        triggered_id = ctx.triggered_id
        
        if triggered_id == "btn-preset-pix":
            return (
                [], ["ML-KEM-512"], ["encap", "decap", "keygen"], []
            )
        elif triggered_id == "btn-preset-contract":
            return (
                [], ["ML-DSA-44", "ML-DSA-65", "ML-DSA-87"], ["sign", "verify", "keygen"], []
            )
        elif triggered_id == "clear-filters":
            return (
                [], [], [], []
            )
        
        return [no_update] * 4

    @app.callback(
        Output('warning-banner', 'children'),
        Output('chart-kem-ranking', 'figure'),
        Output('chart-security-speed', 'figure'),
        Output('chart-signature-comparison', 'figure'),
        Output('chart-cloud-latency', 'figure'),
        Output('chart-local-latency', 'figure'),
        Output("chart-rsa-vs-mlkem", "figure"),
        Output("row-chart-kem-ranking", "style"),
        Output("row-chart-security-speed", "style"),
        Output("row-chart-signature-comparison", "style"),
        Output("row-chart-cloud-latency", "style"),
        Output("row-chart-local-latency", "style"),
        Output("row-chart-rsa-vs-mlkem", "style"),
        Input("env-filter", "value"),
        Input("lib-filter", "value"),
        Input("op-filter", "value"),
        Input("env-type-filter", "value"),
        Input("etl-refresh-ts", "data"),
    )
    def update_dashboard(
        envs,
        libs,
        ops,
        env_types,
        etl_refresh_ts, 
    ):
        payload = _cached_dashboard_payload(
            get_dataset_version(),
            _normalize_multi(envs),
            _normalize_multi(libs),
            _normalize_multi(ops),
            _normalize_multi(env_types),
            (), # processors
            (), # operating_systems
            _normalize_latency(None),
            (), # crypto_types
        )
        return payload.as_callback_tuple()
