"""Tests for dashboard layout composition."""

import pandas as pd

from core.layout import build_layout


class FakeApp:
    """Minimal app stub for layout tests."""

    @staticmethod
    def get_asset_url(asset_name):
        return f"/assets/{asset_name}"


def _collect_ids(component):
    ids = set()
    if hasattr(component, "id") and component.id is not None:
        ids.add(component.id)

    children = getattr(component, "children", None)
    if children is None:
        return ids
    if isinstance(children, (list, tuple)):
        for child in children:
            ids.update(_collect_ids(child))
        return ids
    ids.update(_collect_ids(children))
    return ids


def test_build_layout_exposes_main_dashboard_controls():
    dataframe = pd.DataFrame(
        {
            "environment": ["AWS", "Azure"],
            "library": ["ML-KEM", "RSA"],
            "operation": ["enc", "dec"],
            "crypto_type": ["pqc", "classic"],
            "environment_type": ["cloud", "cloud"],
            "processor": ["Xeon", "EPYC"],
            "operating_system": ["Linux", "Linux"],
            "execution_method": ["native", "docker"],
            "response_ms": [10.0, 12.0],
        }
    )

    layout = build_layout(FakeApp(), dataframe, "logo.jpg")
    component_ids = _collect_ids(layout)

    assert "clear-filters" in component_ids
    assert "env-filter" in component_ids
    assert "warning-banner" in component_ids
    assert "chart-kem-ranking" in component_ids
