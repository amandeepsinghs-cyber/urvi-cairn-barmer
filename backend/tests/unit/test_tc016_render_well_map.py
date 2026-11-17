"""Unit tests for TC-016 render_well_map."""

from __future__ import annotations

import inspect
from collections import Counter

import pytest

from app.analytics.tools.common import ToolStatus, currency_keys, load_table
from app.analytics.tools.render_well_map import WellMap, render_well_map


def test_tc016_all_fields_points():
    wm = load_table("well_master")
    expected_total = len(wm)
    res = render_well_map()
    assert res.status == ToolStatus.OK
    assert isinstance(res.value, WellMap)
    points = res.value.points
    assert len(points) == expected_total == 460

    counts = Counter(p["field"] for p in points)
    assert counts["Mangala"] == 180
    assert counts["Bhagyam"] == 120
    assert counts["Aishwariya"] == 100
    assert counts["Raageshwari"] == 60

    for p in points:
        assert isinstance(p["lat"], float)
        assert isinstance(p["lng"], float)
        assert p["highlighted"] is False

    assert len(res.value.boundaries) == 4
    assert len(res.value.facilities) == 17
    assert res.value.bbox["min_lat"] is not None
    assert res.value.bbox["max_lat"] is not None
    assert res.value.bbox["min_lng"] is not None
    assert res.value.bbox["max_lng"] is not None


def test_tc016_field_bhagyam():
    res = render_well_map(field="Bhagyam")
    assert res.status == ToolStatus.OK
    val = res.value
    assert isinstance(val, WellMap)
    assert len(val.points) == 120
    assert val.fields == ["Bhagyam"]

    valid_buckets = {"PRODUCING_OK", "AT_RISK", "UNDERPERFORMING", "NOT_PRODUCING"}
    for p in val.points:
        assert p["field"] == "Bhagyam"
        assert p["bucket"] in valid_buckets
        assert p["color_key"] == p["bucket"]

    for b in val.boundaries:
        assert b["field"] == "Bhagyam"

    for f in val.facilities:
        assert f["field"] == "Bhagyam"


def test_tc016_highlight_well_id():
    res = render_well_map(field="Bhagyam", highlight_well_ids=["BHG-019"])
    assert res.status == ToolStatus.OK
    assert res.value is not None
    highlighted = [p for p in res.value.points if p["highlighted"]]
    assert len(highlighted) == 1
    assert highlighted[0]["well_id"] == "BHG-019"

    non_highlighted = [p for p in res.value.points if not p["highlighted"]]
    assert len(non_highlighted) == 119


def test_tc016_unknown_field_unavailable():
    res = render_well_map(field="Atlantis")
    assert res.status == ToolStatus.UNAVAILABLE
    assert "field" in res.missing_fields
    assert res.value is None


def test_tc016_signature_defaults_clean():
    sig = inspect.signature(render_well_map)
    for name, param in sig.parameters.items():
        if param.default is not inspect.Parameter.empty and isinstance(param.default, str):
            assert "MNG-" not in param.default
            assert "Mangala" not in param.default


def test_tc016_no_currency_keys():
    res = render_well_map()
    assert res.status == ToolStatus.OK
    assert currency_keys(res.value) == []


def test_tc016_color_by_lift_type_and_invalid():
    res_lift = render_well_map(field="Bhagyam", color_by="lift_type")
    assert res_lift.status == ToolStatus.OK
    assert res_lift.value is not None
    for p in res_lift.value.points:
        assert p["color_key"] == p["lift_type"]

    res_inv = render_well_map(color_by="invalid_mode")
    assert res_inv.status == ToolStatus.UNAVAILABLE
    assert "color_by" in res_inv.missing_fields
