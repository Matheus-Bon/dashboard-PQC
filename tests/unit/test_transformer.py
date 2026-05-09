"""Tests for core.filters - normalize_category, extract_family, apply_filters, _apply_in_filter"""
import pytest
import pandas as pd

from core.filters import normalize_category, extract_family, apply_filters, _apply_in_filter


# ---------------------------------------------------------------------------
# normalize_category
# ---------------------------------------------------------------------------

class TestNormalizeCategory:

    def test_classic_variants(self):
        assert normalize_category("Classic") == "classic"
        assert normalize_category("CLASSICO") == "classic"
        assert normalize_category("classico") == "classic"

    def test_pqc_variants(self):
        assert normalize_category("PQC") == "pqc"
        assert normalize_category("post-quantum") == "pqc"
        assert normalize_category("Pos-Quantico") == "pqc"
        assert normalize_category("post_quantum") == "pqc"

    def test_hybrid_variants(self):
        assert normalize_category("Hybrid") == "hybrid"
        assert normalize_category("HIBRIDO") == "hybrid"
        assert normalize_category("hybrid") == "hybrid"

    def test_unknown_passthrough(self):
        result = normalize_category("SomeUnknownType")
        assert result == "someunknowntype"

    def test_empty_string_returns_na(self):
        assert normalize_category("") == "na"
        assert normalize_category("   ") == "na"

    def test_strips_whitespace(self):
        assert normalize_category("  classic  ") == "classic"


# ---------------------------------------------------------------------------
# extract_family
# ---------------------------------------------------------------------------

class TestExtractFamily:

    def test_ml_kem_pqc(self):
        assert extract_family("ML-KEM-512", "pqc") == "ML-KEM"

    def test_ml_dsa_pqc(self):
        assert extract_family("ML-DSA-44", "pqc") == "ML-DSA"

    def test_slh_dsa_pqc(self):
        assert extract_family("SLH-DSA-SHA2-128s", "pqc") == "SLH-DSA"

    def test_rsa_classic(self):
        assert extract_family("RSA-2048", "classic") == "RSA"

    def test_ecdsa_classic(self):
        assert extract_family("ECDSA-P256", "classic") == "ECDSA"

    def test_hybrid_kem(self):
        assert extract_family("Hybrid-ML-KEM-768", "hybrid") == "Hybrid-KEM"

    def test_hybrid_sign(self):
        assert extract_family("Hybrid-ML-DSA-44", "hybrid") == "Hybrid-Sign"

    def test_hybrid_generic(self):
        assert extract_family("Hybrid-Unknown", "hybrid") == "Hybrid"

    def test_unknown_algorithm_other(self):
        assert extract_family("SomeNewAlgo", "pqc") == "Other"


# ---------------------------------------------------------------------------
# _apply_in_filter
# ---------------------------------------------------------------------------

class TestApplyInFilter:

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "environment": ["AWS", "GCP", "Azure"],
            "response_ms": [10.0, 20.0, 30.0],
        })

    def test_empty_values_returns_all(self, sample_df):
        result = _apply_in_filter(sample_df, "environment", [])
        assert len(result) == 3

    def test_none_values_returns_all(self, sample_df):
        result = _apply_in_filter(sample_df, "environment", None)
        assert len(result) == 3

    def test_missing_column_returns_all(self, sample_df):
        result = _apply_in_filter(sample_df, "nonexistent_col", ["AWS"])
        assert len(result) == 3

    def test_filters_string_column(self, sample_df):
        result = _apply_in_filter(sample_df, "environment", ["AWS", "GCP"])
        assert list(result["environment"]) == ["AWS", "GCP"]

    def test_filters_numeric_column(self, sample_df):
        result = _apply_in_filter(sample_df, "response_ms", [10.0, 30.0])
        assert len(result) == 2


# ---------------------------------------------------------------------------
# apply_filters
# ---------------------------------------------------------------------------

class TestApplyFilters:

    @pytest.fixture
    def bench_df(self):
        return pd.DataFrame({
            "library": ["OQS", "Botan", "OQS", "OpenSSL"],
            "environment": ["AWS", "AWS", "GCP", "GCP"],
            "operation": ["keygen", "keygen", "sign", "verify"],
            "environment_type": ["cloud", "cloud", "cloud", "cloud"],
            "processor": ["x86_64", "x86_64", "arm64", "x86_64"],
            "operating_system": ["Linux", "Linux", "Linux", "Linux"],
            "crypto_type": ["pqc", "classic", "pqc", "classic"],
            "response_ms": [5.0, 50.0, 8.0, 20.0],
        })

    def test_empty_df_returns_empty(self):
        empty = pd.DataFrame()
        result = apply_filters(empty, [], [], [], [], [], [], None, [])
        assert result.empty

    def test_no_filters_returns_all_rows(self, bench_df):
        result = apply_filters(bench_df, [], [], [], [], [], [], None, [])
        assert len(result) == 4

    def test_filter_by_environment(self, bench_df):
        result = apply_filters(bench_df, ["AWS"], [], [], [], [], [], None, [])
        assert all(result["environment"] == "AWS")
        assert len(result) == 2

    def test_filter_by_library(self, bench_df):
        result = apply_filters(bench_df, [], ["OQS"], [], [], [], [], None, [])
        assert all(result["library"] == "OQS")
        assert len(result) == 2

    def test_filter_by_crypto_type_normalizes(self, bench_df):
        result = apply_filters(bench_df, [], [], [], [], [], [], None, ["PQC"])
        assert all(result["crypto_type"] == "pqc")

    def test_filter_by_latency_range(self, bench_df):
        result = apply_filters(bench_df, [], [], [], [], [], [], [0, 10], [])
        assert all(result["response_ms"] <= 10)
        assert len(result) == 2

    def test_combined_filters(self, bench_df):
        result = apply_filters(bench_df, ["AWS"], ["OQS"], [], [], [], [], None, [])
        assert len(result) == 1
        assert result.iloc[0]["library"] == "OQS"
        assert result.iloc[0]["environment"] == "AWS"
