from __future__ import annotations

import logging

import pandas as pd

from core.data_adapter import (
    get_dataframe as _adapter_get_df,
    get_dataset_version as _adapter_get_version,
    invalidate_cache as _adapter_invalidate,
)

logger = logging.getLogger(__name__)

LOGO_ASSET_NAME = "logo.jpg"


def get_dataframe() -> pd.DataFrame:
    return _adapter_get_df()


def get_dataset_version() -> str:
    return _adapter_get_version()


def invalidate_cache() -> None:
    """Invalida o cache TTL — próximo get_dataframe() recarrega do banco."""
    _adapter_invalidate()


def run_etl(raw_excel_path=None) -> dict:
    """Executa o pipeline ETL completo (Excel → MySQL).

    Returns:
        dict com chaves: status, rows_loaded, message
    """
    from core.etl_engine import run_full_etl

    return run_full_etl(raw_excel_path)
