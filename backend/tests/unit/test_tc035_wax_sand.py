"""Stage ED-5 (v0.6): TC-035 wax / sand behaviour (F-31)."""
from __future__ import annotations

import random
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.analytics.tools.common import load_table
from app.analytics.tools.wax_sand import wax_sand_behaviour

VERDICTS = {"NOT_PRONE", "FLAGGED_NO_JOBS", "DOWNTIME_ONLY", "ISOLATED", "REPEAT", "PREDICTABLE"}


def _sample(n=20, seed=35):
    return random.Random(seed).sample(sorted(load_table("well_master")["well_id"].astype(str)), n)


def test_hero_wells():
    bhg = wax_sand_behaviour("BHG-019").value
    assert bhg["wax"]["verdict"] in VERDICTS and bhg["wax"]["flag"] is True
    mng = wax_sand_behaviour("MNG-042").value
    assert mng["wax"]["verdict"] in VERDICTS and mng["sand"]["verdict"] in VERDICTS
    assert "no sand-rate" in mng["data_note"].lower()


@pytest.mark.parametrize("well", ["MNG-042", "BHG-019", "ASH-061"] + _sample())
def test_shape_and_rules(well):
    v = wax_sand_behaviour(well).value
    for k in ("wax", "sand"):
        b = v[k]
        assert b["verdict"] in VERDICTS
        assert len(b["job_dates"]) == min(b["n_jobs"], 10)
        # next-due is predicted only from the well's own repeat cadence
        if b["next_due"] is not None:
            assert b["n_jobs"] >= 2 and b["own_interval_days"] and b["interval_basis"] == "OWN"
            assert date.fromisoformat(b["next_due"]) > date.fromisoformat(b["last_job"]["date"])
        if b["verdict"] == "PREDICTABLE":
            assert b["n_jobs"] >= 3


def test_deterministic():
    assert wax_sand_behaviour("ASH-061").value == wax_sand_behaviour("ASH-061").value


def test_route():
    from app.main import app

    c = TestClient(app)
    r = c.get("/api/wells/BHG-019/wax-sand")
    assert r.status_code == 200 and r.json()["data"]["wax"]["verdict"] in VERDICTS
    assert c.get("/api/wells/ZZ-999/wax-sand").status_code == 404
