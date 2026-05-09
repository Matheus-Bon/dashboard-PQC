"""Tests for dashboard callback helper behavior."""

import core.callbacks as callbacks


class TestDashboardCallbacks:
    """Callback helper tests."""

    def test_normalize_multi_handles_none_and_list(self):
        assert callbacks._normalize_multi(None) == ()
        assert callbacks._normalize_multi(["aws", "gcp"]) == ("aws", "gcp")

    def test_normalize_latency_handles_invalid_and_valid_values(self):
        assert callbacks._normalize_latency(None) == (0.0, 1000.0)
        assert callbacks._normalize_latency([5, 25]) == (5.0, 25.0)

    def test_cached_dashboard_payload_invalidates_on_dataset_version(self, monkeypatch):
        call_count = {"count": 0}

        def fake_build_dashboard_payload(*args, **kwargs):
            call_count["count"] += 1
            from core.dashboard_payload import DashboardPayload
            return DashboardPayload()

        monkeypatch.setattr(callbacks, "build_dashboard_payload", fake_build_dashboard_payload)
        callbacks._cached_dashboard_payload.cache_clear()

        base_args = (
            ("aws",),
            ("algo",),
            (),
            (),
            (),
            (),
            (0.0, 100.0),
            (),
        )

        callbacks._cached_dashboard_payload("v1", *base_args)
        callbacks._cached_dashboard_payload("v1", *base_args)
        callbacks._cached_dashboard_payload("v2", *base_args)

        assert call_count["count"] == 2
