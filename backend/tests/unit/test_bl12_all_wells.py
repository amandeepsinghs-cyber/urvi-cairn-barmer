"""BL-12 regression: the recommendation engine must answer for every well without raising.

Before the fix, 31 of 412 wells crashed in ``nba._pressure`` when the latest pressure survey had no PI value.
"""
from __future__ import annotations

import pytest

from app.analytics.tools.common import ToolStatus, load_table
from app.analytics.tools.nba import _pressure
from app.analytics.tools.success_engine import recommend_interventions
from app import settings

KNOWN_BAD = ["MNG-012", "MNG-042", "BHG-019"]  # representative wells across fields


@pytest.mark.parametrize("well_id", KNOWN_BAD)
def test_pressure_tolerates_missing_pi(well_id):
    out = _pressure(well_id, settings.AS_OF)
    assert out is not None
    if out["latest"]["pi_bpd_per_kgcm2"] is None:
        assert out["pi_change_pct"] is None


def test_recommendation_never_raises_for_any_well():
    wells = load_table("well_master")["well_id"].tolist()
    assert len(wells) == 460
    failures = []
    for wid in wells:
        try:
            r = recommend_interventions(wid)
            assert r["status"] in {s.value for s in ToolStatus}
            for c in r.get("data", {}).get("candidates", []):
                assert 0.05 <= c["p_success"] <= 0.95
            raw = str(r).lower()
            for tok in ("_usd", "currency", "payback", "₹"):
                assert tok not in raw
        except Exception as e:  # noqa: BLE001
            failures.append(f"{wid}: {type(e).__name__}: {e}")
    assert not failures, f"{len(failures)} wells failed: {failures[:5]}"
