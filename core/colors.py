from __future__ import annotations
import math
from typing import Dict, List
import pandas as pd

# Paleta Banco Inter
COLORS: Dict[str, str] = {
    "bg": "#F5F5F5",
    "bg_soft": "#FFF8F3",
    "surface": "rgba(255,255,255,0.96)",
    "surface_solid": "#FFFFFF",
    "surface_dark": "#333333", 
    "text": "#1A1A1A",
    "muted": "#5F6473",
    "muted_2": "#8A90A2",
    "accent": "#FF6600",  
    "accent_2": "#E56700",
    "accent_3": "#FFB062",
    "accent_soft": "#FFF1E5",
    "secondary": "#FF2A6D",
    "secondary_soft": "#FFE6EF",
    "navy_soft": "#151944",
    "border": "rgba(1, 3, 38, 0.08)",
    "grid": "rgba(1, 3, 38, 0.10)",
    "success": "#12B76A",
    "warning": "#F79009",
    "danger": "#F04438",
    "shadow": "0 24px 60px rgba(1, 3, 38, 0.10)",
    "shadow_soft": "0 12px 24px rgba(1, 3, 38, 0.06)",
}

CATEGORY_COLORS: Dict[str, str] = {
    "pqc": "#FF7A00",
    "hybrid": "#333333",
    "classic": "#B0B8C0",
}

LIBRARY_COLORS: Dict[str, str] = {
    "RSA-2048": "#010326",
    "ECDSA-P256": "#1A2A6B",
    "ML-KEM-512": "#FF7A00",
    "ML-KEM-768": "#FF8C1A",
    "ML-KEM-1024": "#FFB062",
}

LIBRARY_COLOR_SEQUENCE: List[str] = [
    "#FF7A00", "#FF2A6D", "#010326", "#FFB062", "#151944", "#8A90A2",
]

ENVIRONMENT_PALETTE: List[str] = [
    "#1A5490", "#E84C3D", "#FFA500", "#2ECC71", "#9B59B6",
    "#3498DB", "#34495E", "#F39C12",
]

DISPLAY_LABELS: Dict[str, str] = {
    "library": "Algoritmo",
    "environment": "Ambiente",
    "environment_type": "Tipo de Ambiente",
    "operation": "Operacao",
    "response_ms": "Latencia (ms)",
    "cpu_percent": "CPU (%)",
    "ram_percent": "RAM (%)",
    "ram_mb": "RAM (MB)",
    "ram_gb": "RAM (GB)",
    "processor": "Processador",
    "operating_system": "Sistema Operacional",
    "execution_method": "Metodo de Execucao",
    "vcpu": "vCPU",
    "hypervisor": "Hypervisor",
    "throughput_ops": "Throughput (ops/s)",
    "payload_kb": "Payload (KB)",
    "ciphertext_bytes": "Ciphertext (B)",
    "key_size_bytes": "Chave (bytes)",
    "iterations": "Iteracoes",
    "crypto_type": "Familia Criptografica",
    "hybrid_overhead_pct": "Overhead Hibrido (%)",
    "vs_classic_pct": "Comparativo vs Classico (%)",
}

def _to_br_fmt(formatted: str) -> str:
    return formatted.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

def human_ms(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "--"
    return _to_br_fmt(f"{value:,.3f}") + " ms"

def human_pct(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "--"
    return _to_br_fmt(f"{value:,.1f}") + "%"

def human_n(value: float | int | None, suffix: str = "") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "--"
    return _to_br_fmt(f"{value:,.0f}") + suffix

def display_name(column: str) -> str:
    return DISPLAY_LABELS.get(column, column.replace("_", " ").title())

def build_library_color_map(values) -> Dict[str, str]:
    libraries = [str(v) for v in pd.Series(values).dropna().astype(str).unique()]
    color_map: Dict[str, str] = {}
    used: set[str] = set()

    for lib in libraries:
        if lib in LIBRARY_COLORS:
            color_map[lib] = LIBRARY_COLORS[lib]
            used.add(LIBRARY_COLORS[lib])

    idx = 0
    for lib in libraries:
        if lib in color_map:
            continue
        while (
            LIBRARY_COLOR_SEQUENCE[idx % len(LIBRARY_COLOR_SEQUENCE)] in used
            and len(used) < len(LIBRARY_COLOR_SEQUENCE)
        ):
            idx += 1
        color = LIBRARY_COLOR_SEQUENCE[idx % len(LIBRARY_COLOR_SEQUENCE)]
        color_map[lib] = color
        used.add(color)
        idx += 1

    return color_map

def build_environment_color_map(values) -> Dict[str, str]:
    envs = sorted({str(v) for v in pd.Series(values).dropna().astype(str) if v})
    return {env: ENVIRONMENT_PALETTE[i % len(ENVIRONMENT_PALETTE)] for i, env in enumerate(envs)}
