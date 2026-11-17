"""Stage T REST routes (SDD §13.4) + Live voice tools resolve to TC-024 / TC-028 / TC-029."""

from __future__ import annotations

from app.analytics.tools.common import CURRENCY_KEY_RE


def _no_currency_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert not CURRENCY_KEY_RE.search(str(k)), f"{path}.{k}"
            _no_currency_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _no_currency_keys(v, f"{path}[{i}]")


def test_get_fields(client):
    r = client.get("/api/fields")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "OK" and body["provenance"]["tool_id"] == "TC-025"
    f = {x["field"]: x for x in body["data"]["fields"]}
    assert (f["Bhagyam"]["n_wells"], len(f["Bhagyam"]["clusters"])) == (120, 3)
    assert sum(f["Bhagyam"]["health_counts"].values()) == 120
    assert f["Bhagyam"]["is_synthetic_geometry"] is True and f["Bhagyam"]["centroid"]
    kinds = [ft["properties"]["kind"] for ft in f["Bhagyam"]["boundary_geojson"]["features"]]
    assert kinds.count("CLUSTER_POLYGON") == 3


def test_fields_history_and_alias(client):
    r = client.get("/api/fields/history?fields=Mangala,Bhagyam,Aishwariya,Raageshwari&freq=M")
    assert r.status_code == 200 and r.json()["status"] == "OK"
    assert len(r.json()["data"]["series"]) == 240
    one = client.get("/api/fields/Bhagyam/history").json()
    assert one["data"]["fields"] == ["Bhagyam"] and len(one["data"]["series"]) == 60
    bhagyam_all = [x for x in r.json()["data"]["series"] if x["field"] == "Bhagyam"]
    assert [x["oil_bopd"] for x in bhagyam_all] == [x["oil_bopd"] for x in one["data"]["series"]]
    assert client.get("/api/fields/history?fields=Rudrasagar").status_code == 404
    assert client.get("/api/fields/history", headers={"X-Persona": "FIELD_ENGINEER"}).status_code == 403


def test_fields_compare(client):
    r = client.get("/api/fields/compare?period=QTD")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["worst_field"] == "Bhagyam" and d["top_driver"]["controllable"] is True
    _no_currency_keys(r.json())
    assert client.get("/api/fields/compare?period=WEEK").status_code == 422


def test_fields_map_bhagyam(client):
    d = client.get("/api/fields/map?field=Bhagyam").json()["data"]
    assert len(d["points"]) == 120 and {p["field"] for p in d["points"]} == {"Bhagyam"}
    assert len(d["cluster_polygons"]) == 3
    assert client.get("/api/fields/map?field=Atlantis").status_code == 404


def test_priority(client):
    r = client.get("/api/fields/Bhagyam/priority?queue=rig&limit=5")
    assert r.status_code == 200
    d = r.json()["data"]
    assert len(d["rig_queue"]) <= 5 and d["rigless_queue"] == []
    _no_currency_keys(r.json())
    assert client.get("/api/fields/Rudrasagar/priority").status_code == 404


def test_well_profile_and_production(client):
    from app.analytics.tools.common import load_table

    wm = load_table("well_master")
    gl_well = str(wm[wm["lift_type"] == "GAS_LIFT"]["well_id"].iloc[0])
    p = client.get("/api/wells/MNG-042/profile").json()
    assert p["status"] == "OK" and len(p["data"]["neighbours"]) >= 3
    r = client.get(f"/api/wells/{gl_well}/production?months=36&metrics=oil,gor,wht,gl_inj_rate,gl_inj_pressure")
    d = r.json()["data"]
    assert set(d["series"]) == {"oil", "gor", "wht", "gl_inj_rate", "gl_inj_pressure"}
    assert len(d["dates"]) == len(d["series"]["wht"]) and d["gas_lift"] is True
    r_mng = client.get("/api/wells/MNG-042/production?months=36").json()["data"]
    assert r_mng["interventions"] and all(
        m["doc_url"] is None or m["doc_url"].startswith("/api/docs/") for m in r_mng["interventions"]
    )
    assert client.get("/api/wells/GLK-001/profile").status_code == 404
    assert client.get("/api/wells/ZZ-1/production").status_code == 404
    assert client.get("/api/wells/MNG-042/production?metrics=bogus").status_code == 422


def test_voice_tools_resolve_to_stage_t():
    from app.live import voice_tools as vt

    out = vt.execute_voice_tool("compare_fields", {"period": "QTD"})
    assert out["status"] == "OK" and out["data"]["worst_field"] == "Bhagyam"
    assert out["provenance"]["tool_id"] == "TC-024"
    h = vt.execute_voice_tool("field_production_history", {})
    assert h["status"] == "OK" and len(h["data"]["summary"]) == 4 and "series" not in h["data"]
    w = vt.execute_voice_tool("well_profile", {"well_id": "MNG-042", "months": 36})
    assert w["status"] == "OK" and len(w["data"]["neighbours"]) >= 3 and w["data"]["interventions_in_window"]
    assert len(vt.declarations_data()) <= 14  # Stage R: 13 until Stage V trims legacy tools (SDD §11.3 target 12)
