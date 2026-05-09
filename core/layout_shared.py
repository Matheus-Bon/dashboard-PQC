from __future__ import annotations
import math
from typing import List
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html

def filters_options(df: pd.DataFrame, col: str, suffix: str = "") -> List[dict]:
    if col not in df.columns:
        return []
    series = df[col].dropna()
    if series.empty:
        return []
    if pd.api.types.is_numeric_dtype(series):
        options: List[dict] = []
        for value in sorted(pd.unique(series)):
            if value is None or (isinstance(value, float) and math.isnan(value)):
                continue
            numeric = float(value)
            label = f"{int(numeric)}{suffix}" if numeric.is_integer() else f"{numeric:g}{suffix}"
            options.append({"label": label, "value": int(numeric) if numeric.is_integer() else numeric})
        return options
    values = sorted(pd.unique(series.astype(str)), key=lambda value: str(value).lower())
    return [{"label": f"{value}{suffix}", "value": value} for value in values]

def card_shell(children, class_name: str = "soft-card"):
    return dbc.Card(dbc.CardBody(children), className=class_name)

_VARIANT_HEIGHT: dict = {
    "graph-box-md": 440,
    "graph-box-lg": 500,
    "graph-box-xl": 560,
    "graph-box-xxl": 640,
    "graph-box-algo": 680,
}

def responsive_graph(graph_id: str, variant: str = "graph-box-md", figure=None):
    height = _VARIANT_HEIGHT.get(variant, 440)
    if figure is None:
        figure_payload: dict = {"data": [], "layout": {"height": height}}
    elif isinstance(figure, dict):
        figure_payload = dict(figure)
        figure_payload["layout"] = dict(figure_payload.get("layout") or {})
        figure_payload["layout"]["height"] = height
    elif hasattr(figure, "to_dict"):
        figure_payload = figure.to_dict()
        figure_payload.setdefault("layout", {})["height"] = height
    else:
        figure_payload = {"data": [], "layout": {"height": height}}

    return dcc.Graph(
        id=graph_id,
        className=f"graph-box {variant}",
        figure=figure_payload,
        config={"displayModeBar": False, "responsive": True},
    )
