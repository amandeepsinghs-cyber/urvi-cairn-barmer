"""Stage ED-6: India view — Cairn Oil & Gas / Vedanta upstream assets, position-only tags outside Barmer (F-32, D-34)."""
from __future__ import annotations

from fastapi.testclient import TestClient


def _load_cairn_assets() -> dict:
    try:
        from app.analytics.tools.cairn_assets import cairn_assets

        return cairn_assets()
    except ImportError:
        from app.analytics.tools import ongc_assets as mod

        fn = getattr(mod, "cairn_assets", getattr(mod, "ongc_assets"))
        return fn()


def test_cairn_assets_only_barmer_live():
    d = _load_cairn_assets()
    assert d["n_assets"] == len(d["assets"]) >= 4
    live = [a for a in d["assets"] if a["live"]]
    assert len(live) == 1
    assert "BARMER" in live[0]["asset_id"].upper() or "Barmer" in live[0]["name"]
    assert set(live[0]["fields"]) == {"Mangala", "Bhagyam", "Aishwariya", "Raageshwari"}
    assert live[0]["well_tags"] == []


def test_tags_are_position_only_and_near_centre():
    for a in _load_cairn_assets()["assets"]:
        if a["live"]:
            continue
        assert 4 <= len(a["well_tags"]) <= 35
        names = [t["name"] for t in a["well_tags"]]
        assert len(names) == len(set(names))
        for t in a["well_tags"]:
            assert set(t) == {"name", "lat", "lng"}  # D-34: no data behind a tag
            assert abs(t["lat"] - a["lat"]) < 0.5 and abs(t["lng"] - a["lng"]) < 0.5


def test_deterministic_and_route():
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/geo/cairn-assets")
    assert r.status_code == 200
    assert r.json() == _load_cairn_assets()
    assert "Barmer" in r.text and "Ravva" in r.text
    assert "ONGC" not in r.text
