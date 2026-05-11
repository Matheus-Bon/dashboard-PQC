from __future__ import annotations
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html
from core.dashboard_payload import DashboardPayload
from core.layout_sections import build_analysis_children, build_filter_panel, build_hero_section

def build_layout(app, df: pd.DataFrame, logo_asset_name: str, initial_payload: DashboardPayload | None = None):
    if initial_payload is None:
        initial_payload = DashboardPayload()

    hero_section = build_hero_section(app, df, logo_asset_name)
    filter_panel = build_filter_panel(df)
    analysis_children = build_analysis_children(df, initial_payload.banner, initial_payload.figures_by_id(), initial_payload.styles_by_id())

    team_members = [
        ("JB", "Joseph Bessa Pereira da Costa"),
        ("LI", "Lucas Israel França Gontijo"),
        ("LO", "Lucas Oue"),
        ("MM", "Marcos Martins dos Santos"),
        ("MR", "Matheus Rodrigues Bon"),
        ("YG", "Yuri Geovane Martiniano dos Santos"),
    ]

    footer = html.Footer(
        className="dashboard-footer",
        children=[
            html.Div(
                className="footer-team-strip",
                children=[
                    html.Span("Equipe", className="footer-strip-label"),
                    html.Div(
                        className="footer-members-row",
                        children=[
                            html.Div(
                                className="footer-member-chip",
                                children=[
                                    html.Span(initials, className="chip-avatar"),
                                    html.Span(name, className="chip-name"),
                                ],
                            )
                            for initials, name in team_members
                        ],
                    ),
                    html.Div(
                        className="footer-advisor-chip",
                        children=[
                            html.Span("MH", className="chip-avatar chip-avatar-advisor"),
                            html.Div([
                                html.Span("Prof.ª Michelle Hanne Soares de Andrade", className="chip-name"),
                                html.Span("Orientadora", className="chip-role"),
                            ], className="chip-info"),
                        ],
                    ),
                    html.A(
                        "Ver Resumo Executivo →",
                        href="/resumo",
                        className="footer-summary-link",
                    ),
                ],
            ),
        ],
    )

    return html.Div(
        className="page-shell",
        children=[
            dcc.Store(id="etl-refresh-ts", data=None),
            dbc.Container(
                fluid=True,
                className="main-wrap",
                children=[
                    hero_section,
                    filter_panel,
                    html.Div(style={"height": "16px"}),
                    analysis_children,
                    footer,
                ],
            ),
        ],
    )
