from __future__ import annotations

import pandas as pd


def normalize_category(value: str) -> str:
    raw = str(value).strip().lower()
    if raw in {"classic", "classico"}:
        return "classic"
    if raw in {"pqc", "post-quantum", "pos-quantico", "post_quantum"}:
        return "pqc"
    if raw in {"hybrid", "hibrido"}:
        return "hybrid"
    return raw or "na"


def extract_family(algorithm: str, crypto_type: str) -> str:
    name = str(algorithm)
    cat = normalize_category(crypto_type)
    if cat == "hybrid":
        if "ML-KEM" in name:
            return "Hybrid-KEM"
        if "ML-DSA" in name:
            return "Hybrid-Sign"
        return "Hybrid"
    if "ML-KEM" in name:
        return "ML-KEM"
    if "ML-DSA" in name:
        return "ML-DSA"
    if "SLH-DSA" in name:
        return "SLH-DSA"
    if "RSA" in name:
        return "RSA"
    if "ECDSA" in name or "P256" in name:
        return "ECDSA"
    return "Other"


def _apply_in_filter(df: pd.DataFrame, column: str, values) -> pd.DataFrame:
    if not values or column not in df.columns:
        return df
    series = df[column]
    if pd.api.types.is_numeric_dtype(series):
        return df[series.astype(float).isin([float(v) for v in values])]
    return df[series.astype(str).isin([str(v) for v in values])]


def apply_filters(
    df: pd.DataFrame,
    envs,
    libs,
    ops,
    env_types,
    processors,
    operating_systems,
    latency_range,
    crypto_types,
) -> pd.DataFrame:
    if df.empty:
        return df

    filtered = df.copy()
    filtered["crypto_type"] = filtered["crypto_type"].map(normalize_category)

    filtered = _apply_in_filter(filtered, "environment", envs)
    filtered = _apply_in_filter(filtered, "library", libs)
    filtered = _apply_in_filter(filtered, "operation", ops)
    filtered = _apply_in_filter(filtered, "environment_type", env_types)
    filtered = _apply_in_filter(filtered, "processor", processors)
    filtered = _apply_in_filter(filtered, "operating_system", operating_systems)

    if crypto_types:
        normalized = [normalize_category(v) for v in crypto_types]
        filtered = filtered[filtered["crypto_type"].isin(normalized)]

    if latency_range:
        filtered = filtered[filtered["response_ms"].between(latency_range[0], latency_range[1])]

    return filtered
