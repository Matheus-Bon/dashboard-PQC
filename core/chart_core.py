from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from core.colors import COLORS
from core.config import assumed_vcpu_per_operation, cloud_price_per_vcpu_second, load_pricing_config, target_utilization

_ENV_TO_PROVIDER: dict[str, str] = {
    "google cloud platform": "GCP",
    "gcp": "GCP",
    "google": "GCP",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "aws": "AWS",
    "aws ec2": "AWS",
    "amazon web services": "AWS",
    "amazon ec2": "AWS",
    "ec2": "AWS",
}

def _resolve_provider_filter(selected_envs, all_provider_keys: list[str]) -> list[str]:
    if not selected_envs:
        return all_provider_keys
    matched = [
        key
        for env in selected_envs
        for key in [_ENV_TO_PROVIDER.get(str(env).strip().lower())]
        if key and key in all_provider_keys
    ]
    matched_unique = list(dict.fromkeys(matched))  # preserve order, deduplicate
    return matched_unique if matched_unique else all_provider_keys

def has_cloud_provider_match(selected_envs, all_provider_keys: list[str]) -> bool:
    if not selected_envs:
        return False
    return any(
        _ENV_TO_PROVIDER.get(str(env).strip().lower()) in all_provider_keys
        for env in selected_envs
    )

def base_layout(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        autosize=True,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FBFBFC",
        margin=dict(l=24, r=24, t=52, b=24),
        font=dict(family="Georgia, Times New Roman, serif", color=COLORS["text"], size=14),
        title=None,
        transition=dict(duration=350, easing="cubic-in-out"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="left",
            x=0,
            bgcolor="rgba(255,255,255,.96)",
            bordercolor="rgba(0,0,0,0.10)",
            borderwidth=1,
            font=dict(size=11, family="Arial, sans-serif"),
        ),
        hoverlabel=dict(bgcolor="#ffffff", font_size=12, font_family="Arial, sans-serif"),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=True,
        linewidth=1,
        linecolor="rgba(0,0,0,0.35)",
        mirror=False,
        ticks="outside",
        ticklen=5,
        tickwidth=1,
        tickcolor="rgba(0,0,0,0.35)",
        tickfont=dict(size=12, family="Arial, sans-serif"),
        title_font=dict(size=14, family="Arial, sans-serif"),
    )
    fig.update_yaxes(
        gridcolor="rgba(0,0,0,0.09)",
        gridwidth=0.7,
        zeroline=False,
        showline=True,
        linewidth=1,
        linecolor="rgba(0,0,0,0.35)",
        ticks="outside",
        ticklen=5,
        tickwidth=1,
        tickcolor="rgba(0,0,0,0.35)",
        tickfont=dict(size=12, family="Arial, sans-serif"),
        title_font=dict(size=14, family="Arial, sans-serif"),
    )
    return fig

def empty_figure(message: str) -> go.Figure:
    fig = base_layout(go.Figure())
    fig.add_annotation(text=message, x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=COLORS["muted"]))
    return fig

def _calc_vps_cost(
    provider: str,
    category: str,
    provider_config: dict,
    req_mean_vcpu_s: float,
    req_p95_vcpu_s: float,
    util: float,
    period: str,
) -> dict:
    try:
        hourly_usd = float(provider_config["hourly_usd"]) if provider_config.get("hourly_usd") is not None else None
        vcpus = float(provider_config["vcpus"]) if provider_config.get("vcpus") is not None else None
    except (TypeError, ValueError):
        hourly_usd = None
        vcpus = None

    if hourly_usd is None or vcpus is None or hourly_usd < 0 or vcpus <= 0:
        return {
            "provider": provider, "crypto_type": category,
            "cost_mean_usd": 0.0, "cost_p95_usd": 0.0,
            "pricing_model": "vps",
            "pricing_note_mean": "VPS: preco/h nao configurado",
            "pricing_note_p95": "VPS: preco/h nao configurado",
            "is_missing_price": True,
        }

    effective_vcpu = vcpus * util
    mean_h = (req_mean_vcpu_s / (effective_vcpu * 3600.0)) if effective_vcpu > 0 else 0.0
    p95_h = (req_p95_vcpu_s / (effective_vcpu * 3600.0)) if effective_vcpu > 0 else 0.0

    free_config = provider_config.get("free_tier") if isinstance(provider_config.get("free_tier"), dict) else {}
    try:
        free_hours = float(free_config["hours_per_month"]) if free_config.get("hours_per_month") is not None else None
    except (TypeError, ValueError):
        free_hours = None

    in_free_tier = period in {"free", "free_tier"} and free_hours and free_hours > 0
    mean_bill = max(0.0, mean_h - free_hours) if in_free_tier else mean_h
    p95_bill = max(0.0, p95_h - free_hours) if in_free_tier else p95_h

    if in_free_tier:
        mean_note = f"VPS: ~{mean_h:.1f}h, free {free_hours:.0f}h -> cobrado {mean_bill:.1f}h"
        p95_note = f"VPS: ~{p95_h:.1f}h (P95), free {free_hours:.0f}h -> cobrado {p95_bill:.1f}h"
    else:
        mean_note = f"VPS: ~{mean_h:.1f}h (media) @ {int(util * 100)}%"
        p95_note = f"VPS: ~{p95_h:.1f}h (P95) @ {int(util * 100)}%"

    if hourly_usd == 0:
        mean_note = p95_note = "VPS FREE"

    return {
        "provider": provider, "crypto_type": category,
        "cost_mean_usd": mean_bill * hourly_usd,
        "cost_p95_usd": p95_bill * hourly_usd,
        "pricing_model": "vps",
        "pricing_note_mean": mean_note,
        "pricing_note_p95": p95_note,
        "is_missing_price": False,
    }

def _calc_cpu_cost(
    provider: str,
    category: str,
    unit_price: float | None,
    req_mean_vcpu_s: float,
    req_p95_vcpu_s: float,
) -> dict:
    if unit_price is None:
        return {
            "provider": provider, "crypto_type": category,
            "cost_mean_usd": 0.0, "cost_p95_usd": 0.0,
            "pricing_model": "cpu",
            "pricing_note_mean": "CPU: preco por vCPU-s nao configurado",
            "pricing_note_p95": "CPU: preco por vCPU-s nao configurado",
            "is_missing_price": True,
        }
    return {
        "provider": provider, "crypto_type": category,
        "cost_mean_usd": req_mean_vcpu_s * unit_price,
        "cost_p95_usd": req_p95_vcpu_s * unit_price,
        "pricing_model": "cpu",
        "pricing_note_mean": f"CPU: {unit_price:.8f} US$/vCPU-s",
        "pricing_note_p95": f"CPU: {unit_price:.8f} US$/vCPU-s",
        "is_missing_price": False,
    }

def cost_frame_for_cloud(dff: pd.DataFrame, monthly_ops: int, pricing_period: str | None = None, selected_envs=None) -> pd.DataFrame:
    grouped = dff.groupby("crypto_type", dropna=False)["response_ms"].agg(
        mean_ms="mean", p95_ms=lambda series: series.quantile(0.95)
    ).reset_index()

    unit_prices = cloud_price_per_vcpu_second()
    vcpu_multiplier = assumed_vcpu_per_operation()
    cfg = load_pricing_config()
    providers_cfg = cfg.get("providers", {}) if isinstance(cfg.get("providers"), dict) else {}
    util = target_utilization()
    period = (pricing_period or "post_free").strip().lower()
    all_providers = list(providers_cfg.keys()) or sorted(unit_prices.keys())
    provider_order = _resolve_provider_filter(selected_envs, all_providers)

    rows: list[dict] = []
    for _, row in grouped.iterrows():
        category = row["crypto_type"]
        mean_seconds = max(float(row["mean_ms"]), 0.0) / 1000.0
        p95_seconds = max(float(row["p95_ms"]), 0.0) / 1000.0
        req_mean_vcpu_s = mean_seconds * monthly_ops * vcpu_multiplier
        req_p95_vcpu_s = p95_seconds * monthly_ops * vcpu_multiplier

        for provider in provider_order:
            provider_config = providers_cfg.get(provider, {}) if isinstance(providers_cfg.get(provider), dict) else {}
            billing_model = str(provider_config.get("billing_model") or "").strip().lower() or (
                "vps" if provider_config.get("hourly_usd") else "cpu"
            )

            if billing_model == "vps":
                rows.append(_calc_vps_cost(provider, category, provider_config, req_mean_vcpu_s, req_p95_vcpu_s, util, period))
            elif billing_model == "cpu":
                rows.append(_calc_cpu_cost(provider, category, unit_prices.get(provider), req_mean_vcpu_s, req_p95_vcpu_s))

    return pd.DataFrame(rows)