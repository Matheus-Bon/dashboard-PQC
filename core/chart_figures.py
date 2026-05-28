from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats as sp_stats

from core.chart_core import base_layout, empty_figure
from core.colors import COLORS, CATEGORY_COLORS, build_environment_color_map, build_library_color_map


_GRID_COLOR = "rgba(0,0,0,0.06)"
_ERROR_COLOR = "rgba(0,0,0,0.35)"
_MEAN_AXIS_TITLE = "Latência média (ms)"
_ANNOTATION_FONT = {"size": 9, "color": COLORS["muted"]}

_SECURITY_PALETTE = {
    "Clássico": "#010326",
    "L1": "#FFB873",
    "L2": "#FF8C1A",
    "L3": "#FF7A00",
    "L5": "#E56700",
}

_FUNCTIONAL_MAP = {
    "encrypt": "encap",
    "decrypt": "decap",
}

_KEM_LIBRARY_MARKERS = ("ML-KEM",)
_SIGNATURE_LIBRARY_MARKERS = ("ML-DSA", "SLH-DSA", "ECDSA", "RSA")

def _ci95(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    sample_size = len(values)
    if sample_size < 2:
        return 0.0
    return float(sp_stats.sem(values) * sp_stats.t.ppf(0.975, sample_size - 1))


def _contains_any(series: pd.Series, markers: tuple[str, ...]) -> pd.Series:
    pattern = "|".join(markers)
    return series.astype(str).str.contains(pattern, case=False, na=False)


def _prepare_summary(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    summary = (
        frame.groupby(group_cols, dropna=False)["response_ms"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    return summary.rename(columns={"mean": "mean_ms", "median": "median_ms", "count": "n"})


def fig_kem_ranking(dff: pd.DataFrame) -> go.Figure:
    kem = dff[_contains_any(dff["library"], _KEM_LIBRARY_MARKERS)].copy()
    kem = kem[kem["operation"].astype(str).str.lower() == "encap"]
    if kem.empty:
        return empty_figure("Sem dados de encapsulamento para os filtros atuais")

    summary = _prepare_summary(kem, ["library"])
    summary["ci95"] = summary["library"].map(
        lambda library: _ci95(kem.loc[kem["library"] == library, "response_ms"])
    )
    summary = summary.sort_values(["mean_ms", "median_ms", "library"], ascending=[True, True, True])
    def _lib_category(name: str) -> str:
        s = str(name).lower()
        if "+" in s:
            return "hybrid"
        if "ml-kem" in s or "kem" in s:
            return "pqc"
        if "ml-dsa" in s or "slh-dsa" in s or "sphincs" in s:
            return "pqc"
        return "classic"

    colors_for_bars = [CATEGORY_COLORS.get(_lib_category(lib), COLORS["accent"]) for lib in summary["library"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=summary["library"],
            x=summary["mean_ms"],
            orientation="h",
            marker={
                "color": colors_for_bars,
                "line": {"color": "white", "width": 1},
            },
            error_x={"type": "data", "array": summary["ci95"], "color": _ERROR_COLOR, "thickness": 1.5},
            customdata=np.column_stack([summary["median_ms"], summary["n"], summary["ci95"]]),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Média: %{x:.4f} ms<br>"
                "Mediana: %{customdata[0]:.4f} ms<br>"
                "IC95: +/- %{customdata[2]:.4f} ms<br>"
                "n = %{customdata[1]:.0f}<extra></extra>"
            ),
        )
    )

    if "ML-KEM-512" in summary["library"].values:
        idx = int(summary[summary["library"] == "ML-KEM-512"].index[0])
        val = float(summary.loc[summary["library"] == "ML-KEM-512", "mean_ms"].iloc[0])
        fig.add_annotation(
            x=val,
            y="ML-KEM-512",
            text=f"ML-KEM-512 ≈ {val:.3f} ms",
            showarrow=True,
            arrowhead=3,
            ax=60,
            ay=-10,
            font={"color": CATEGORY_COLORS.get("pqc", COLORS["accent"]), "size": 11},
        )
    fig = base_layout(fig)
    fig.update_layout(
        height=max(420, len(summary) * 52 + 120),
        margin={"l": 190, "r": 40, "t": 60, "b": 100},  
        showlegend=False,
    )
    fig.update_xaxes(
        title="Latência média de encapsulamento (ms)",
        showgrid=True,
        gridwidth=0.5,
        gridcolor=_GRID_COLOR,
        automargin=True,
        title_standoff=16  
    )
    fig.update_yaxes(
        title="Algoritmo",
        showgrid=False,
        automargin=True,
        title_standoff=16 
    )
    fig.add_annotation(
        text="Ranking por encapsulamento de chave com barra de erro",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.22,  
        showarrow=False,
        font=_ANNOTATION_FONT,
    )
    return fig

def fig_security_vs_speed(dff: pd.DataFrame) -> go.Figure:
    if dff.empty or "security_level" not in dff.columns:
        return empty_figure("Dados de nível de segurança indisponíveis")

    df = dff.copy()
    if "key_size_bytes" not in df.columns:
        df["key_size_bytes"] = df.get("key_size_bytes", pd.Series([0] * len(df)))

    summary = (
        df.groupby(["library", "security_level"], dropna=False)
        .agg(mean_ms=("response_ms", "mean"), median_ms=("response_ms", "median"), key_bytes=("key_size_bytes", "median"), n=("response_ms", "count"))
        .reset_index()
    )

    if summary.empty:
        return empty_figure("Sem níveis de segurança NIST válidos para os filtros atuais")

    level_map = {"Clássico": 0, "L1": 1, "L2": 2, "L3": 3, "L5": 5}
    summary = summary[summary["security_level"].isin(level_map.keys())]
    summary["x_level"] = summary["security_level"].map(level_map)

    fig = go.Figure()
    for _, row in summary.iterrows():
        lib = row["library"]
        x = float(row["x_level"])
        y = float(row["mean_ms"]) if not pd.isna(row["mean_ms"]) else 0.0
        size = float(row["key_bytes"]) if not pd.isna(row["key_bytes"]) else 8.0
        marker_size = max(8, min(60, size / 4 if size > 0 else 10))
        cat = "pqc" if ("ml" in str(lib).lower() or "kem" in str(lib).lower() or "slh" in str(lib).lower()) else ("hybrid" if "+" in str(lib) else "classic")
        color = CATEGORY_COLORS.get(cat, COLORS["accent"]) if cat else COLORS["accent"]

        fig.add_trace(
            go.Scatter(
                x=[x + np.random.normal(scale=0.08)],
                y=[y],
                mode="markers",
                marker={"size": marker_size, "color": color, "opacity": 0.8, "line": {"width": 1, "color": "white"}},
                name=lib,
                hovertemplate=(f"<b>{lib}</b><br>Seg: {row['security_level']}<br>Latência: {y:.3f} ms<br>Key size: {size} B<br>n={int(row['n'])}<extra></extra>"),
            )
        )

    fig = base_layout(fig)
    fig.update_layout(
        height=520,
        xaxis=dict(title="Nível de segurança", tickmode="array", tickvals=[0, 1, 2, 3, 5], ticktext=["Clássico", "L1", "L2", "L3", "L5"], automargin=True),
        yaxis=dict(title=_MEAN_AXIS_TITLE, type="linear", showgrid=True, gridcolor=_GRID_COLOR, automargin=True),
        showlegend=False,
        margin={"l": 40, "r": 20, "t": 40, "b": 80},
    )

    fig.add_annotation(text="Bolhas: tamanho de chave. Eixo X: nível NIST.", xref="paper", yref="paper", x=0.5, y=-0.20, showarrow=False, font=_ANNOTATION_FONT)
    return fig


def fig_signature_comparison(dff: pd.DataFrame) -> go.Figure:
    signatures = dff[_contains_any(dff["library"], _SIGNATURE_LIBRARY_MARKERS)].copy()
    signatures = signatures[signatures["operation"].isin(["sign", "verify"])]
    if signatures.empty:
        return empty_figure("Sem dados de assinatura digital para os filtros atuais")
    summary = _prepare_summary(signatures, ["library", "operation"])
    ml_dsa = summary[summary["library"].str.contains("ML-DSA", case=False, na=False)]
    slh_dsa = summary[summary["library"].str.contains("SLH-DSA", case=False, na=False)]

    fig = go.Figure()
    if not ml_dsa.empty:
        fig.add_trace(
            go.Bar(
                x=ml_dsa["library"],
                y=ml_dsa["mean_ms"],
                text=ml_dsa["mean_ms"].apply(lambda x: f"{x:.2f} ms"),
                textposition="outside",
                name="ML-DSA (Rápido)",
                marker={"color": "#FF7A00", "line": {"color": "white", "width": 1}},
                hovertemplate="<b>%{x}</b><br>Média: %{y:.3f} ms<extra></extra>",
            )
        )

    if not slh_dsa.empty:
        fig.add_trace(
            go.Bar(
                x=slh_dsa["library"],
                y=slh_dsa["mean_ms"],
                text=slh_dsa["mean_ms"].apply(lambda x: f"{x:.2f} ms"),
                textposition="outside",
                name="SLH-DSA (Lento)",
                marker={"color": "#010326", "line": {"color": "white", "width": 1}},
                hovertemplate="<b>%{x}</b><br>Média: %{y:.3f} ms<extra></extra>",
            )
        )

    fig = base_layout(fig)
    fig.update_layout(
        barmode="group",
        height=600,
        bargap=0.15,
        bargroupgap=0.1,
        margin={"l": 70, "r": 50, "t": 100, "b": 180},
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.05,
            "xanchor": "right",
            "x": 1,
            "bgcolor": "rgba(255, 255, 255, 0.6)",
        },
    )
    fig.update_xaxes(
        title={"text": ""}, # Removed the axis title
        tickangle=-45,
        showgrid=False,
        automargin=True
    )
    fig.update_yaxes(
        title={"text": _MEAN_AXIS_TITLE, "standoff": 20},
        showgrid=True,
        gridwidth=0.5,
        gridcolor=_GRID_COLOR,
        automargin=True,
        range=[0, dff["response_ms"].max() * 1.25 if not dff.empty else 1000]
    )
    
    # Add an annotation about the performance difference, positioned lower
    fig.add_annotation(
        text="Comparando a alta performance do ML-DSA contra a robustez conservadora do SLH-DSA, sob diferentes níveis de proteção NIST e infraestruturas de nuvem.",
        xref="paper", yref="paper",
        x=0.5, y=-0.58, # Lowered to avoid axis title
        showarrow=False,
        font={"size": 11, "color": "#444"},
        align="center"
    )
    return fig


def _fig_latency_by_env_type(dff: pd.DataFrame, env_type: str, title_y: str, annotation_text: str) -> go.Figure:
    """Helper to build a standardized latency box plot by library for a given environment type."""
    if "environment_type" in dff.columns:
        filtered = dff[dff["environment_type"].astype(str).str.lower() == env_type.lower()].copy()
    else:
        if env_type.lower() == "local":
            filtered = dff[dff["environment"].astype(str).str.lower() == "local"].copy()
        else:
            filtered = dff[dff["environment"].astype(str).str.lower() != "local"].copy()

    if filtered.empty:
        return empty_figure(f"Sem dados de ambiente {env_type} para os filtros atuais")

    algorithm_order = (
        filtered.groupby("library")["response_ms"].median().sort_values(ascending=True).index.tolist()
    )
    color_map = build_library_color_map(algorithm_order)

    fig = go.Figure()
    for algorithm in algorithm_order:
        subset = filtered[filtered["library"] == algorithm]
        fig.add_trace(
            go.Box(
                y=subset["library"],
                x=subset["response_ms"],
                name=algorithm,
                legendgroup=algorithm,
                marker_color=color_map.get(algorithm, COLORS["accent"]),
                boxmean=True,
                jitter=0.28,
                pointpos=0,
                boxpoints="all",
                marker={"size": 3, "opacity": 0.32},
                orientation="h",
                hovertemplate="Algoritmo: %{y}<br>Latência: %{x:.4f} ms<extra></extra>",
            )
        )

    fig = base_layout(fig)
    fig.update_layout(
        boxmode="overlay",
        height=max(560, len(algorithm_order) * 34 + 160),
        margin={"l": 210, "r": 40, "t": 60, "b": 90},
        showlegend=False,
    )
    fig.update_xaxes(title="Latência (ms)", showgrid=True, gridwidth=0.5, gridcolor=_GRID_COLOR, automargin=True)
    fig.update_yaxes(title="Algoritmo", categoryorder="array", categoryarray=algorithm_order, showgrid=False, automargin=True)
    fig.add_annotation(
        text=annotation_text,
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.15,
        showarrow=False,
        font=_ANNOTATION_FONT,
    )
    return fig


def fig_cloud_latency(dff: pd.DataFrame) -> go.Figure:
    return _fig_latency_by_env_type(
        dff, 
        "cloud", 
        "Algoritmo", 
        "Ambiente cloud ordenado pela mediana para expor o ranking de desempenho observado"
    )


def fig_local_latency(dff: pd.DataFrame) -> go.Figure:
    return _fig_latency_by_env_type(
        dff, 
        "local", 
        "Algoritmo", 
        "Ambiente local ordenado pela mediana para expor o ranking de desempenho observado"
    )



def fig_rsa_vs_mlkem(dff: pd.DataFrame) -> go.Figure:
    rsa = dff[dff["library"].astype(str) == "RSA-2048"].copy()
    mlkem = dff[dff["library"].astype(str).str.contains("ML-KEM", case=False, na=False)].copy()
    if rsa.empty and mlkem.empty:
        return empty_figure("Sem dados de RSA-2048 ou ML-KEM para os filtros atuais")

    rsa_keygen = rsa[rsa["operation"].astype(str).str.lower().isin(["keygen"])].copy()
    mlkem_keygen = mlkem[mlkem["operation"].astype(str).str.lower().isin(["keygen"])].copy()

    rsa_val = rsa_keygen["response_ms"].median() if not rsa_keygen.empty else None
    mlkem_val = mlkem_keygen.groupby("library")["response_ms"].median().mean() if not mlkem_keygen.empty else None

    labels = []
    values = []
    colors = []
    if rsa_val is not None:
        labels.append("RSA-2048")
        values.append(float(rsa_val))
        colors.append(CATEGORY_COLORS.get("classic", COLORS["surface_dark"]))
    if mlkem_val is not None:
        labels.append("ML-KEM (med)")
        values.append(float(mlkem_val))
        colors.append(CATEGORY_COLORS.get("pqc", COLORS["accent"]))

    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=labels, y=values, marker={"color": colors, "line": {"color": "white", "width": 1}})
    )
    fig = base_layout(fig)
    fig.update_layout(height=420, margin={"l": 60, "r": 40, "t": 60, "b": 110}, showlegend=False)
    fig.update_xaxes(title="Algoritmo (Keygen)", automargin=True)
    fig.update_yaxes(title=_MEAN_AXIS_TITLE, type="log", showgrid=True, gridwidth=0.5, gridcolor=_GRID_COLOR, automargin=True)

    if rsa_val and mlkem_val and mlkem_val > 0:
        ratio = rsa_val / mlkem_val
        fig.add_annotation(text=f"Keygen: RSA ≈ {ratio:.1f}x mais lento que ML-KEM", xref="paper", yref="paper", x=0.5, y=-0.22, showarrow=False, font=_ANNOTATION_FONT)

    return fig
