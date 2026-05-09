"""Tests for filter/callback validation - _normalize_multi, _normalize_latency, apply_filters edge cases"""
import pytest
import pandas as pd

from core.callbacks import _normalize_multi, _normalize_latency
from core.filters import apply_filters, normalize_category


class TestNormalizeMulti:

    def test_none_returns_empty_tuple(self):
        assert _normalize_multi(None) == ()

    def test_empty_list_returns_empty_tuple(self):
        assert _normalize_multi([]) == ()

    def test_empty_string_returns_empty_tuple(self):
        assert _normalize_multi("") == ()

    def test_single_string_wraps_in_tuple(self):
        assert _normalize_multi("AWS") == ("AWS",)

    def test_list_converts_to_tuple_of_strings(self):
        assert _normalize_multi(["AWS", "GCP"]) == ("AWS", "GCP")

    def test_list_with_integers_converted(self):
        assert _normalize_multi([1, 2, 3]) == ("1", "2", "3")

    def test_single_integer_wraps_as_string(self):
        assert _normalize_multi(1) == ("1",)

    def test_already_tuple_is_converted(self):
        assert _normalize_multi(("A", "B")) == ("A", "B")


class TestNormalizeLatency:

    def test_none_returns_default(self):
        lo, hi = _normalize_latency(None)
        assert lo == 0.0 and hi == 1000.0

    def test_empty_list_returns_default(self):
        lo, hi = _normalize_latency([])
        assert lo == 0.0 and hi == 1000.0

    def test_wrong_length_returns_default(self):
        lo, hi = _normalize_latency([100])
        assert lo == 0.0 and hi == 1000.0

    def test_valid_range_returns_floats(self):
        lo, hi = _normalize_latency([10, 500])
        assert lo == pytest.approx(10.0) and hi == pytest.approx(500.0)

    def test_string_numbers_converted(self):
        lo, hi = _normalize_latency(["5", "999"])
        assert lo == pytest.approx(5.0) and hi == pytest.approx(999.0)

    def test_always_returns_two_element_tuple(self):
        assert len(_normalize_latency([0, 100])) == 2


class TestApplyFiltersEdgeCases:

    @pytest.fixture
    def full_df(self):
        return pd.DataFrame({
            "library": ["OQS", "Botan", "OpenSSL", "OQS"],
            "environment": ["AWS", "GCP", "Azure", "AWS"],
            "operation": ["keygen", "sign", "verify", "encap"],
            "environment_type": ["cloud", "cloud", "cloud", "vps"],
            "processor": ["x86_64", "arm64", "x86_64", "x86_64"],
            "operating_system": ["Linux", "Linux", "Windows", "Linux"],
            "crypto_type": ["pqc", "classic", "classic", "pqc"],
            "response_ms": [1.0, 500.0, 250.0, 900.0],
        })

    def test_filter_unknown_type_yields_no_rows(self, full_df):
        result = apply_filters(full_df, [], [], [], [], [], [], None, ["quantum"])
        assert result.empty

    def test_negative_latency_range_yields_no_rows(self, full_df):
        result = apply_filters(full_df, [], [], [], [], [], [], [-100, -1], [])
        assert result.empty

    def test_zero_latency_range_yields_no_rows(self, full_df):
        result = apply_filters(full_df, [], [], [], [], [], [], [0, 0], [])
        assert result.empty

    def test_beyond_max_latency_yields_all(self, full_df):
        result = apply_filters(full_df, [], [], [], [], [], [], [0, 9999], [])
        assert len(result) == 4

    def test_filter_by_operating_system(self, full_df):
        result = apply_filters(full_df, [], [], [], [], [], ["Windows"], None, [])
        assert len(result) == 1 and result.iloc[0]["operating_system"] == "Windows"

    def test_filter_by_processor(self, full_df):
        result = apply_filters(full_df, [], [], [], [], ["arm64"], [], None, [])
        assert len(result) == 1 and result.iloc[0]["processor"] == "arm64"

    def test_filter_by_environment_type(self, full_df):
        result = apply_filters(full_df, [], [], [], ["vps"], [], [], None, [])
        assert len(result) == 1 and result.iloc[0]["environment_type"] == "vps"

    def test_filter_by_operation(self, full_df):
        result = apply_filters(full_df, [], [], ["keygen"], [], [], [], None, [])
        assert len(result) == 1 and result.iloc[0]["operation"] == "keygen"
