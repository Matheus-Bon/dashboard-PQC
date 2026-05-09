"""Unit tests for core.data_adapter.DataStore."""
from __future__ import annotations

import time
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from core.data_adapter import DataStore, DataSource, _normalize_df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_valid_df() -> pd.DataFrame:
    return pd.DataFrame({
        "library": ["kyber", "dilithium"],
        "operation": ["encapsulate", "sign"],
        "crypto_type": ["KEM", "Signature"],
        "response_ms": [1.5, 2.0],
        "payload_kb": [1.0, 2.0],
        "key_size_bytes": [800, 1312],
        "ram_gb": [8.0, 16.0],
        "vcpu": [2.0, 4.0],
        "hybrid_overhead_pct": [0.0, 0.0],
        "vs_classic_pct": [0.0, 0.0],
        "iterations": [1000, 1000],
        "security_level": [3, 3],
    })


# ---------------------------------------------------------------------------
# _normalize_df
# ---------------------------------------------------------------------------

class TestNormalizeDF:
    def test_empty_df_returns_empty(self):
        df = pd.DataFrame()
        result = _normalize_df(df)
        assert result.empty

    def test_numeric_columns_coerced(self):
        df = _make_valid_df()
        df["response_ms"] = ["1.5", "bad"]
        result = _normalize_df(df)
        assert pd.isna(result.loc[1, "response_ms"])
        assert result.loc[0, "response_ms"] == 1.5

    def test_drops_rows_missing_required_columns(self):
        df = _make_valid_df()
        df.loc[0, "library"] = None
        result = _normalize_df(df)
        assert len(result) == 1
        assert result.iloc[0]["library"] == "dilithium"

    def test_crypto_type_normalized_lowercase(self):
        df = _make_valid_df()
        df["crypto_type"] = ["KEM", "SIGNATURE"]
        result = _normalize_df(df)
        assert result["crypto_type"].tolist() == ["kem", "signature"]

    def test_does_not_fillna_zero(self):
        """NaN in numeric columns must be preserved, not silently zeroed."""
        df = _make_valid_df()
        df.loc[0, "payload_kb"] = float("nan")
        result = _normalize_df(df)
        assert pd.isna(result.loc[0, "payload_kb"])


# ---------------------------------------------------------------------------
# DataStore.invalidate + stale detection
# ---------------------------------------------------------------------------

class TestDataStoreCache:
    def test_invalidate_forces_reload(self):
        store = DataStore()
        store._df = _make_valid_df()
        store._version = "test:1"
        store._loaded_at = time.monotonic()
        store._source = DataSource.NONE

        store.invalidate()

        assert store._is_stale()

    def test_fresh_load_not_stale(self):
        store = DataStore()
        store._df = _make_valid_df()
        store._loaded_at = time.monotonic()
        assert not store._is_stale()

    def test_none_df_always_stale(self):
        store = DataStore()
        store._df = None
        assert store._is_stale()

    def test_expired_ttl_is_stale(self):
        store = DataStore()
        store._df = _make_valid_df()
        store._loaded_at = time.monotonic() - 99999
        assert store._is_stale()


# ---------------------------------------------------------------------------
# DataStore source detection
# ---------------------------------------------------------------------------

class TestDataStoreSourceDetection:
    def test_cached_source_not_redetected(self):
        store = DataStore()
        store._source = DataSource.EXCEL

        with patch.object(store, "_try_mysql") as mock_mysql:
            result = store._detect_source()

        mock_mysql.assert_not_called()
        assert result == DataSource.EXCEL

    def test_mysql_preferred_over_excel(self):
        store = DataStore()

        with patch.object(store, "_try_mysql", return_value=True) as mock_mysql, \
             patch.object(store, "_try_excel", return_value=True) as mock_excel:
            result = store._detect_source()

        mock_mysql.assert_called_once()
        mock_excel.assert_not_called()
        assert result == DataSource.MYSQL

    def test_falls_back_to_excel_when_mysql_unavailable(self):
        store = DataStore()

        with patch.object(store, "_try_mysql", return_value=False), \
             patch.object(store, "_try_excel", return_value=True):
            result = store._detect_source()

        assert result == DataSource.EXCEL

    def test_none_source_when_nothing_available(self):
        store = DataStore()

        with patch.object(store, "_try_mysql", return_value=False), \
             patch.object(store, "_try_excel", return_value=False):
            result = store._detect_source()

        assert result == DataSource.NONE


# ---------------------------------------------------------------------------
# DataStore public API via mocked _reload
# ---------------------------------------------------------------------------

class TestDataStorePublicAPI:
    def _fresh_store(self, df: pd.DataFrame, version: str = "2:abc") -> DataStore:
        store = DataStore()
        store._df = df
        store._version = version
        store._loaded_at = time.monotonic()
        store._source = DataSource.EXCEL
        return store

    def test_get_dataframe_returns_cached_df(self):
        df = _make_valid_df()
        store = self._fresh_store(df)
        result = store.get_dataframe()
        assert result is df

    def test_get_dataset_version_returns_cached_version(self):
        store = self._fresh_store(_make_valid_df(), version="42:xyz")
        assert store.get_dataset_version() == "42:xyz"

    def test_get_dataset_version_fallback_on_none(self):
        store = self._fresh_store(_make_valid_df())
        store._version = None
        store._loaded_at = time.monotonic()
        # version is None but not stale — returns "unknown"
        assert store.get_dataset_version() == "unknown"

    def test_get_dataframe_reloads_empty_when_no_source(self):
        store = DataStore()
        with patch.object(store, "_detect_source", return_value=DataSource.NONE):
            df = store.get_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert df.empty
