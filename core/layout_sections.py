from __future__ import annotations
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html
from core.filter_config import MAIN_FILTER_FIELDS
from core.layout_shared import card_shell, filters_options, responsive_graph
from core.ui_text import (
    CHART_SECTIONS,
    CLEAR_FILTERS_LABEL,
    FILTERS_TITLE,
    HERO_EYEBROW,
    HERO_TEXT,
    HERO_TITLE,
)

FILTER_GRID_CLASS = "g-3 filter-grid"
SECTION_ROW_CLASS = "g-3 section-gap"
PREMIUM_CARD_CLASS = "soft-card premium-card"

def _build_main_filter_cols(df: pd.DataFrame) -> list:
    cols = []
    # Main filters from config
    for field in MAIN_FILTER_FIELDS:
        cols.append(
            dbc.Col([
                html.Label(field.label, className="filter-label mb-1"),
                dcc.Dropdown(
                    id=field.component_id,
                    options=filters_options(df, field.dataframe_column),
                    multi=True,
                    placeholder=field.placeholder,
                    className="filter-control",
                ),
            ], xl=3, md=6, sm=12, className="mb-3")
        )
    return cols

_CHIP_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "padding": "6px 14px",
    "borderRadius": "999px",
    "background": "rgba(1,3,38,0.05)",
    "border": "1px solid rgba(1,3,38,0.09)",
    "color": "#4B5563",
    "fontSize": "12px",
    "fontWeight": "600",
    "letterSpacing": "0.01em",
}

def build_hero_section(app, _df: pd.DataFrame, logo_asset_name: str) -> html.Div:
    return html.Div(
        className="hero-panel",
        children=[
            html.Div(
                className="hero-copy",
                style={"width": "100%", "padding": "40px 32px"},
                children=[
                    html.Div(
                        [
                            html.Img(src=app.get_asset_url(logo_asset_name), className="brand-logo inter-logo", alt="Banco Inter"),
                            html.Div(className="brand-divider"),
                            html.Img(src=app.get_asset_url("logo-puc.png"), className="brand-logo puc-logo", alt="PUC Minas"),
                        ],
                        className="brand-strip",
                    ),
                    html.Div(
                        [
                            html.Div(HERO_EYEBROW, className="eyebrow"),
                            html.H1(HERO_TITLE, className="hero-title", style={"color": "#FF7A00"}),
                            html.P(HERO_TEXT, className="hero-text"),
                            html.A(
                                "Ver Resumo Executivo →",
                                href="/resumo",
                                className="hero-summary-btn",
                                style={
                                    "display": "inline-block",
                                    "marginTop": "24px",
                                    "padding": "12px 28px",
                                    "background": "#FF7A00",
                                    "color": "#fff",
                                    "border": "none",
                                    "borderRadius": "10px",
                                    "fontWeight": "700",
                                    "fontSize": "0.92rem",
                                    "textDecoration": "none",
                                    "boxShadow": "0 4px 16px rgba(255,122,0,0.32)",
                                    "letterSpacing": "-0.01em",
                                },
                            ),
                            html.Div(
                                [
                                    html.Span("6 Algoritmos avaliados", style=_CHIP_STYLE),
                                    html.Span("Cloud + Local", style=_CHIP_STYLE),
                                    html.Span("NIST FIPS 203 · 204 · 205", style=_CHIP_STYLE),
                                ],
                                style={
                                    "display": "flex",
                                    "gap": "10px",
                                    "marginTop": "20px",
                                    "justifyContent": "center",
                                    "flexWrap": "wrap",
                                },
                            ),
                        ],
                        className="hero-brand",
                    ),
                ],
            ),
        ],
    )

def build_filter_panel(df: pd.DataFrame) -> dbc.Card:
    filter_cols = _build_main_filter_cols(df)
    
    presets_row = dbc.Row(
        className="mb-4 mt-3",
        children=[
            dbc.Col(
                dbc.ButtonGroup([
                    dbc.Button("Otimização para PIX", id="btn-preset-pix", color="primary", outline=True),
                    dbc.Button("Assinatura de Contratos", id="btn-preset-contract", color="primary", outline=True),
                ], className="w-100 shadow-sm"),
                md=12,
            )
        ]
    )

    return card_shell(
        [
            dbc.Row(
                className="align-items-center mb-3",
                children=[
                    dbc.Col(html.Div(FILTERS_TITLE, className="section-title mb-0"), xs=12, md=6),
                    dbc.Col(
                        dbc.Button(CLEAR_FILTERS_LABEL, id="clear-filters", n_clicks=0, color="secondary", outline=True, className="w-100"),
                        xs=6, md=3, className="mt-2 mt-md-0"
                    ),
                    dbc.Col(
                        dbc.Button("Atualizar Dados", id="etl-refresh-btn", n_clicks=0, color="warning", outline=True, className="w-100"),
                        xs=6, md=3, className="mt-2 mt-md-0"
                    ),
                ],
            ),
            presets_row,
            html.Div(dbc.Row(filter_cols, className=FILTER_GRID_CLASS), style={"padding": "0 8px"}),
            dbc.Alert(
                id="etl-refresh-status",
                is_open=False,
                dismissable=True,
                duration=4000,
                className="mt-3 mb-0",
            ),
        ],
        class_name="filter-card glass-panel shadow-sm",
    )

def build_analysis_children(df: pd.DataFrame, banner, figures=None, styles=None) -> html.Div:
    figures = figures or {}
    styles = styles or {}

    from core.chart_core import cost_frame_for_cloud
    from core.config import cloud_price_per_vcpu_second
    def get_recommended_pix_algo():
        if df.empty or "library" not in df.columns or "operation" not in df.columns:
            return "--"
        kem_df = df[(df["operation"].str.lower() == "encap") & (df["library"].str.contains("ML-KEM", case=False, na=False))]
        if kem_df.empty:
            return "--"
        best = kem_df.loc[kem_df["response_ms"].idxmin()]
        return str(best["library"])

    def get_recommended_sign_algo():
        if df.empty or "library" not in df.columns or "operation" not in df.columns:
            return "--"
        sign_df = df[(df["operation"].str.lower() == "sign") & (df["library"].str.contains("ML-DSA", case=False, na=False))]
        if sign_df.empty:
            return "--"
        best = sign_df.loc[sign_df["response_ms"].idxmin()]
        return str(best["library"])

    def get_kpi_data():
        max_lat = df["response_ms"].max() if not df.empty and "response_ms" in df.columns else None
        max_lat_str = f"{max_lat:.2f} ms" if max_lat else "--"
        unique_algos = df["library"].nunique() if not df.empty and "library" in df.columns else 0
        kem_fig = figures.get("chart-kem-ranking", {})
        overhead = "--"
        if kem_fig and kem_fig.get("data"):
            bars = kem_fig["data"][0]
            if bars.get("x") and bars.get("y"):
                xs = bars["x"]
                ys = bars["y"]
                hybrid_vals = [x for x, y in zip(xs, ys) if "Hybrid" in str(y) or "+" in str(y)]
                if hybrid_vals:
                    overhead = f"{sum(hybrid_vals)/len(hybrid_vals):.2f} ms"
        return max_lat_str, overhead, str(unique_algos)

    max_lat_str, overhead, _ = get_kpi_data()
    recommended_pix = get_recommended_pix_algo()
    recommended_sign = get_recommended_sign_algo()

    kpi_cards = dbc.Row(
        id="kpi-row",
        className="kpi-zone mb-4",
        children=[
            dbc.Col(card_shell([
                html.Div(className="metric-head", children=[
                    html.Div("KEM", className="metric-icon"),
                    html.Div(className="metric-copy", children=[
                        html.Div("Recomendação PIX (KEM)", className="metric-title"),
                        html.Div(className="metric-value-wrap", children=[
                            html.Span(recommended_pix, className="metric-value"),
                        ]),
                    ]),
                ]),
            ], class_name="metric-card shadow-sm"), xs=12, sm=6, lg=3, className="mb-3 mb-lg-0"),
            dbc.Col(card_shell([
                html.Div(className="metric-head", children=[
                    html.Div("SIG", className="metric-icon"),
                    html.Div(className="metric-copy", children=[
                        html.Div("Recomendação Assinatura", className="metric-title"),
                        html.Div(className="metric-value-wrap", children=[
                            html.Span(recommended_sign, className="metric-value"),
                        ]),
                    ]),
                ]),
            ], class_name="metric-card shadow-sm"), xs=12, sm=6, lg=3, className="mb-3 mb-lg-0"),
            dbc.Col(card_shell([
                html.Div(className="metric-head", children=[
                    html.Div("MAX", className="metric-icon"),
                    html.Div(className="metric-copy", children=[
                        html.Div("Latência Máxima", className="metric-title"),
                        html.Div(className="metric-value-wrap", children=[
                            html.Span(max_lat_str, className="metric-value"),
                        ]),
                    ]),
                ]),
            ], class_name="metric-card shadow-sm"), xs=12, sm=6, lg=3, className="mb-3 mb-lg-0"),
            dbc.Col(card_shell([
                html.Div(className="metric-head", children=[
                    html.Div("OHD", className="metric-icon"),
                    html.Div(className="metric-copy", children=[
                        html.Div("Overhead Híbrido", className="metric-title"),
                        html.Div(className="metric-value-wrap", children=[
                            html.Span(overhead, className="metric-value"),
                        ]),
                    ]),
                ]),
            ], class_name="metric-card shadow-sm"), xs=12, sm=6, lg=3, className="mb-3 mb-lg-0"),
        ]
    )

    from dash import dash_table
    def get_table_data_and_columns(section_id):
        if section_id == "chart-kem-ranking":
            cols = ["library", "operation", "response_ms", "security_level", "environment"]
            dff = df[df["operation"].str.lower() == "encap"] if not df.empty and "operation" in df.columns else df
        elif section_id == "chart-security-speed":
            cols = ["library", "security_level", "response_ms", "key_size_bytes", "environment"]
            dff = df[df["security_level"].notna()] if not df.empty and "security_level" in df.columns else df
        elif section_id == "chart-signature-comparison":
            cols = ["library", "operation", "response_ms", "security_level", "environment"]
            dff = df[df["operation"].isin(["sign", "verify"])] if not df.empty and "operation" in df.columns else df
        elif section_id == "chart-cloud-latency":
            cols = ["library", "operation", "response_ms", "environment"]
            dff = df[df["environment"].str.contains("cloud", case=False, na=False)] if not df.empty and "environment" in df.columns else df
        elif section_id == "chart-local-latency":
            cols = ["library", "operation", "response_ms", "environment"]
            dff = df[df["environment"].str.contains("local", case=False, na=False)] if not df.empty and "environment" in df.columns else df
        elif section_id == "chart-rsa-vs-mlkem":
            cols = ["library", "operation", "response_ms", "security_level", "environment"]
            dff = df[df["library"].str.contains("RSA|ML-KEM", case=False, na=False)] if not df.empty and "library" in df.columns else df
        else:
            cols = list(df.columns)
            dff = df
        cols = [c for c in cols if c in dff.columns]
        dff = dff[cols] if not dff.empty else dff
        return dff, cols

    def make_heatmap_style(df_table):
        if "response_ms" not in df_table.columns:
            return []
        min_val = df_table["response_ms"].min()
        max_val = df_table["response_ms"].max()
        if min_val == max_val:
            return []
        return [
            {
                "if": {"column_id": "response_ms", "filter_query": f"{{response_ms}} >= {min_val} && {{response_ms}} <= {max_val}"},
                "background": f"linear-gradient(90deg, #F55 {min_val/max_val*100:.0f}%, #5F5 {max_val/min_val*100:.0f}%)",
                "color": "#222",
            }
        ]

    def get_active_filters_text():
        filters = []
        for col in ["library", "operation", "security_level", "environment"]:
            if col in df.columns:
                vals = df[col].unique()
                if len(vals) == 1:
                    filters.append(f"{col}={vals[0]}")
                elif len(vals) > 1 and len(vals) < 6:
                    filters.append(f"{col}=[{', '.join(str(v) for v in vals)}]")
        return ", ".join(filters) if filters else "Todos os dados"

    chart_rows = []
    for section in CHART_SECTIONS:
        # We always render the row but apply the style (hidden or flex)
        row_style = styles.get(f"row-{section['id']}", {})
        table_df, table_cols = get_table_data_and_columns(section["id"])
        
        table_columns = [{"name": col, "id": col} for col in table_cols] if not table_df.empty else []
        table_data = table_df.to_dict("records") if not table_df.empty else []
        style_data_conditional = make_heatmap_style(table_df) if not table_df.empty else []
        active_filters_text = get_active_filters_text()
        chart_rows.append(
            dbc.Row(id=f"row-{section['id']}", style=row_style, className=SECTION_ROW_CLASS, children=[
                dbc.Col(card_shell([
                    html.Div([
                        html.Div(section["title"], className="section-title", style={"fontSize": 24, "fontWeight": 600, "marginBottom": 2, "marginTop": 2}),
                        html.Div(section["sub"], className="section-sub", style={"fontSize": 15, "color": "#444", "marginBottom": 10, "marginTop": 0}),
                        html.Div(f"Filtros ativos: {active_filters_text}", style={"fontSize": 13, "color": "#888", "marginBottom": 8}),
                    ]),
                    responsive_graph(
                        section["id"],
                        variant=section["variant"],
                        figure=figures.get(section["id"]),
                    ),
                    dbc.Accordion([
                        dbc.AccordionItem([
                            dash_table.DataTable(
                                id=f"datatable-{section['id']}",
                                columns=table_columns,
                                data=table_data,
                                page_size=10,
                                style_table={"overflowX": "auto"},
                                style_data_conditional=style_data_conditional,
                                export_format="csv",
                                filter_action="native",
                                sort_action="native",
                                style_cell={"fontFamily": "monospace", "fontSize": 13},
                            )
                        ], title="Ver dados operacionais"),
                    ], start_collapsed=True, className="mt-2 shadow-sm"),
                ], class_name=PREMIUM_CARD_CLASS), lg=12),
            ])
        )

    return html.Div([
        html.Div(id="warning-banner", children=banner),
        kpi_cards,
        *chart_rows,
    ])