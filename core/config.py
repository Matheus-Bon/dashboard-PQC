from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Tuple

_ROOT = Path(__file__).resolve().parent.parent
_PRICING_PATH = _ROOT / "cloud_pricing.json"

_DEFAULT_CONFIG: Dict[str, Any] = {
    "cost_model": {
        "metric": "response_ms",
        "assumed_vcpu_per_operation": 1,
        "hours_per_month": 730,
        "target_utilization": 0.7,
        "formula_ptbr": (
            "VPS: horas=(lat_s*vol*vCPU_op)/(vCPU_inst*util) e custo=horas*US$/h. "
            "CPU: custo=(lat_s*vol*vCPU_op)*US$/vCPU-s."
        ),
    },
    "providers": {
        "AWS": {
            "billing_model": "vps",
            "source": "AWS Pricing Calculator (EC2 On-Demand)",
            "region": "us-east-1",
            "instance_type": "c5.large",
            "os": "Linux",
            "tenancy": "Shared",
            "billing": "OnDemand",
            "hourly_usd": 0.0864,
            "vcpus": 2,
        },
        "GCP": {
            "billing_model": "cpu",
            "source": "Configuracao local",
            "usd_per_vcpu_second": 0.000011,
        },
        "Azure": {
            "billing_model": "vps",
            "source": "Assumido: Azure Standard_B1s + Free Tier",
            "region": "eastus",
            "instance_type": "Standard_B1s",
            "hourly_usd": 0.012,
            "vcpus": 1,
            "free_tier": {"months": 12, "hours_per_month": 730, "hourly_usd": 0.0},
        },
    },
}

def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None

@lru_cache(maxsize=1)
def load_pricing_config() -> Dict[str, Any]:
    if not _PRICING_PATH.exists():
        return _DEFAULT_CONFIG

    try:
        raw = json.loads(_PRICING_PATH.read_text(encoding="utf-8"))
    except Exception:
        return _DEFAULT_CONFIG

    merged = _DEFAULT_CONFIG.copy()
    if isinstance(raw.get("cost_model"), dict):
        cm = _DEFAULT_CONFIG["cost_model"].copy()
        cm.update(raw["cost_model"])
        merged["cost_model"] = cm

    if isinstance(raw.get("providers"), dict):
        providers: Dict[str, Any] = {}
        for name, defaults in _DEFAULT_CONFIG["providers"].items():
            cfg = defaults.copy()
            if isinstance(raw["providers"].get(name), dict):
                cfg.update(raw["providers"][name])
            providers[name] = cfg
        for name, cfg in raw["providers"].items():
            if name not in providers and isinstance(cfg, dict):
                providers[name] = cfg
        merged["providers"] = providers

    return merged

def cloud_price_per_vcpu_second() -> Dict[str, float]:
    cfg = load_pricing_config()
    providers = cfg.get("providers", {}) or {}
    out: Dict[str, float] = {}

    for provider, pcfg in providers.items():
        if not isinstance(pcfg, dict):
            continue
        model = str(pcfg.get("billing_model") or "").strip().lower()
        if model == "vps":
            continue

        direct = _safe_float(pcfg.get("usd_per_vcpu_second"))
        if direct and direct > 0:
            out[provider] = direct
            continue

        hourly = _safe_float(pcfg.get("hourly_usd"))
        vcpus = _safe_float(pcfg.get("vcpus"))
        if hourly and vcpus and hourly > 0 and vcpus > 0:
            out[provider] = hourly / (vcpus * 3600.0)

    return out

def assumed_vcpu_per_operation() -> float:
    cfg = load_pricing_config()
    val = _safe_float((cfg.get("cost_model") or {}).get("assumed_vcpu_per_operation"))
    return val if val and val > 0 else float(_DEFAULT_CONFIG["cost_model"]["assumed_vcpu_per_operation"])

def hours_per_month() -> int:
    cfg = load_pricing_config()
    try:
        return max(1, int((cfg.get("cost_model") or {}).get("hours_per_month")))
    except (TypeError, ValueError):
        return int(_DEFAULT_CONFIG["cost_model"]["hours_per_month"])

def target_utilization() -> float:
    cfg = load_pricing_config()
    val = _safe_float((cfg.get("cost_model") or {}).get("target_utilization"))
    if val is None:
        val = float(_DEFAULT_CONFIG["cost_model"]["target_utilization"])
    return max(0.05, min(0.98, val))

def pricing_assumptions(monthly_ops: int | None = None, pricing_period: str | None = None) -> Tuple[str, ...]:
    cfg = load_pricing_config()
    cost_model = cfg.get("cost_model") or {}
    providers = cfg.get("providers") or {}
    unit_prices = cloud_price_per_vcpu_second()

    formula = str(cost_model.get("formula_ptbr") or _DEFAULT_CONFIG["cost_model"]["formula_ptbr"])
    assumed_vcpu = assumed_vcpu_per_operation()
    hpm = hours_per_month()
    util = target_utilization()

    period = (pricing_period or "post_free").strip().lower()
    period_label = "pos-free" if period in {"post_free", "pos_free", "paid", "standard"} else "free"

    parts = [
        formula,
        f"Assuncao: {assumed_vcpu} vCPU/op. Utilizacao alvo: {int(util * 100)}% ({hpm}h/mes). Periodo: {period_label}.",
    ]

    if monthly_ops is not None:
        safe_ops = int(monthly_ops) if monthly_ops and monthly_ops > 0 else 1_000_000
        parts.append(f"Volume: {safe_ops:,}/mes.".replace(",", "."))

    for provider, pcfg in providers.items():
        if not isinstance(pcfg, dict):
            continue
        src = str(pcfg.get("source") or "Configuracao")
        billing_model = str(pcfg.get("billing_model") or "").strip().lower() or (
            "vps" if pcfg.get("hourly_usd") else "cpu"
        )
        hourly_usd = _safe_float(pcfg.get("hourly_usd"))
        vcpus = _safe_float(pcfg.get("vcpus"))

        if billing_model == "vps":
            region = str(pcfg.get("region") or "").strip()
            instance = str(pcfg.get("instance_type") or "").strip()
            id_part = f"{region} {instance}".strip() or "instancia"
            free_cfg = pcfg.get("free_tier") if isinstance(pcfg.get("free_tier"), dict) else {}
            free_months = 0
            try:
                free_months = int(free_cfg.get("months") or 0)
            except (TypeError, ValueError):
                pass
            free_hours = _safe_float(free_cfg.get("hours_per_month"))
            if hourly_usd is not None and vcpus and hourly_usd >= 0 and vcpus > 0:
                free_note = ""
                if free_months > 0 and free_hours and free_hours > 0:
                    free_note = f" | Free tier: {free_months}m, {int(free_hours)}h/mes"
                parts.append(f"{provider}: VPS US$ {hourly_usd:.4f}/h ({id_part}, {int(vcpus)} vCPU) [{src}]{free_note}")
            else:
                parts.append(f"{provider}: VPS ({id_part}) sem preco/h configurado [{src}]")
            continue

        if hourly_usd and vcpus and hourly_usd > 0 and vcpus > 0:
            region = str(pcfg.get("region") or "").strip()
            instance = str(pcfg.get("instance_type") or "").strip()
            id_part = f"{region} {instance}".strip() or "instancia"
            parts.append(f"{provider}: US$ {hourly_usd:.4f}/h ({id_part}, {int(vcpus)} vCPU) [{src}]")
            continue

        unit = unit_prices.get(provider)
        if unit is not None:
            parts.append(f"{provider}: CPU {unit:.8f} US$/vCPU-s [{src}]")
        else:
            parts.append(f"{provider}: sem preco valido [{src}]")

    return tuple(parts)