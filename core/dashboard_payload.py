from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
import pandas as pd
import plotly.graph_objects as go
from core.chart_core import empty_figure
from core.chart_figures import (
    fig_cloud_latency,
    fig_kem_ranking,
    fig_local_latency,
    fig_rsa_vs_mlkem,
    fig_security_vs_speed,
    fig_signature_comparison,
)
from core.data import get_dataframe
from core.filters import apply_filters, normalize_category

@dataclass
class DashboardPayload:
    banner: List[Any] = field(default_factory=list)
    kem_ranking: Dict = field(default_factory=dict)
    security_speed: Dict = field(default_factory=dict)
    signature_comparison: Dict = field(default_factory=dict)
    cloud_latency: Dict = field(default_factory=dict)
    local_latency: Dict = field(default_factory=dict)
    rsa_vs_mlkem: Dict = field(default_factory=dict)
    
    # Styles to control visibility of each chart row
    kem_ranking_style: Dict = field(default_factory=dict)
    security_speed_style: Dict = field(default_factory=dict)
    signature_comparison_style: Dict = field(default_factory=dict)
    cloud_latency_style: Dict = field(default_factory=dict)
    local_latency_style: Dict = field(default_factory=dict)
    rsa_vs_mlkem_style: Dict = field(default_factory=dict)

    def as_callback_tuple(self):
        return (
            self.banner,
            self.kem_ranking,
            self.security_speed,
            self.signature_comparison,
            self.cloud_latency,
            self.local_latency,
            self.rsa_vs_mlkem,
            self.kem_ranking_style,
            self.security_speed_style,
            self.signature_comparison_style,
            self.cloud_latency_style,
            self.local_latency_style,
            self.rsa_vs_mlkem_style,
        )
        
    def figures_by_id(self) -> Dict[str, Dict]:
        return {
            "chart-kem-ranking": self.kem_ranking,
            "chart-security-speed": self.security_speed,
            "chart-signature-comparison": self.signature_comparison,
            "chart-cloud-latency": self.cloud_latency,
            "chart-local-latency": self.local_latency,
            "chart-rsa-vs-mlkem": self.rsa_vs_mlkem,
        }
        
    def styles_by_id(self) -> Dict[str, Dict]:
        return {
            "row-chart-kem-ranking": self.kem_ranking_style,
            "row-chart-security-speed": self.security_speed_style,
            "row-chart-signature-comparison": self.signature_comparison_style,
            "row-chart-cloud-latency": self.cloud_latency_style,
            "row-chart-local-latency": self.local_latency_style,
            "row-chart-rsa-vs-mlkem": self.rsa_vs_mlkem_style,
        }

def _as_figure_payload(fig: go.Figure | dict) -> dict:
    if isinstance(fig, dict):
        return fig
    import json as _json
    return _json.loads(fig.to_json())

def build_dashboard_payload(
    envs,
    libs,
    ops,
    env_types,
    processors,
    operating_systems,
    latency_range,
    crypto_types=None,
) -> DashboardPayload:
    df = get_dataframe()
    dff = apply_filters(df, envs, libs, ops, env_types, processors, operating_systems, latency_range, crypto_types)

    if not dff.empty:
        dff = dff.copy()
        dff["crypto_type"] = dff["crypto_type"].map(normalize_category)

    banner: List[Any] = []

    # Preset Inference
    is_pix_preset = False
    is_contract_preset = False
    
    # If explicitly ML-KEM-512 or only KEM operations are selected
    if (libs and len(libs) == 1 and "ML-KEM-512" in libs) or \
       (ops and all(o in ["encap", "decap", "keygen", "encrypt", "decrypt"] for o in ops)):
        is_pix_preset = True
    # If explicitly ML-DSA or only signature operations are selected
    elif (libs and all("ML-DSA" in l for l in libs)) or \
         (ops and all(o in ["sign", "verify", "keygen"] for o in ops)):
        is_contract_preset = True

    if dff.empty:
        empty_fig = _as_figure_payload(empty_figure("Sem dados para os filtros selecionados"))
        hidden_style = {"display": "none"}
        return DashboardPayload(
            banner=banner,
            kem_ranking=empty_fig,
            security_speed=empty_fig,
            signature_comparison=empty_fig,
            cloud_latency=empty_fig,
            local_latency=empty_fig,
            rsa_vs_mlkem=empty_fig,
            kem_ranking_style=hidden_style,
            security_speed_style=hidden_style,
            signature_comparison_style=hidden_style,
            cloud_latency_style=hidden_style,
            local_latency_style=hidden_style,
            rsa_vs_mlkem_style=hidden_style,
        )

    # Generate Figures
    fig_kem = _as_figure_payload(fig_kem_ranking(dff))
    fig_sec = _as_figure_payload(fig_security_vs_speed(dff))
    fig_sig = _as_figure_payload(fig_signature_comparison(dff))
    fig_cloud = _as_figure_payload(fig_cloud_latency(dff))
    fig_local = _as_figure_payload(fig_local_latency(dff))
    fig_rsa_mlkem = _as_figure_payload(fig_rsa_vs_mlkem(dff))
    
    # Determine Styles (Hide charts with "Sem dados" or based on preset)
    def _style_for(fig: dict, hide_for_preset: bool = False) -> dict:
        if hide_for_preset:
            return {"display": "none"}
        
        # Check if it's an empty figure (has annotations but no data traces)
        data = fig.get("data", [])
        if not data:
            return {"display": "none"}
            
        return {}

    return DashboardPayload(
        banner=banner,
        kem_ranking=fig_kem,
        security_speed=fig_sec,
        signature_comparison=fig_sig,
        cloud_latency=fig_cloud,
        local_latency=fig_local,
        rsa_vs_mlkem=fig_rsa_mlkem,
        kem_ranking_style=_style_for(fig_kem, hide_for_preset=is_contract_preset),
        security_speed_style=_style_for(fig_sec),
        signature_comparison_style=_style_for(fig_sig, hide_for_preset=is_pix_preset),
        cloud_latency_style=_style_for(fig_cloud),
        local_latency_style=_style_for(fig_local),
        rsa_vs_mlkem_style=_style_for(fig_rsa_mlkem, hide_for_preset=is_contract_preset),
    )