"""TC-025 query_hierarchy (BDD-F05-S01 / S04) and TC-016 v2 multi-field map with cluster polygons (Gate T)."""

from __future__ import annotations

from app.analytics.tools.common import ToolStatus, currency_keys
from app.analytics.tools.geodata import build_field_geojson, cluster_polygons, load_field_geojson
from app.analytics.tools.hierarchy import query_hierarchy
from app.analytics.tools.render_well_map import render_well_map


def test_fields_and_clusters():
    r = query_hierarchy()
    assert r.status == ToolStatus.OK
    f = {x["field"]: x for x in r.value["fields"]}
    assert (f["Mangala"]["n_wells"], len(f["Mangala"]["clusters"])) == (180, 4)
    assert (f["Bhagyam"]["n_wells"], len(f["Bhagyam"]["clusters"])) == (120, 3)
    assert (f["Aishwariya"]["n_wells"], len(f["Aishwariya"]["clusters"])) == (100, 3)
    assert (f["Raageshwari"]["n_wells"], len(f["Raageshwari"]["clusters"])) == (60, 3)
    for x in f.values():
        assert sum(c["n_wells"] for c in x["clusters"]) == x["n_wells"]
    assert r.value["n_wells"] == 460
    assert currency_keys(r.value) == []


def test_filters_and_refusals():
    r = query_hierarchy(field="bhagyam")
    assert [x["field"] for x in r.value["fields"]] == ["Bhagyam"]
    r = query_hierarchy(cluster_id="BHG-PAD-2")
    assert [c["cluster_id"] for c in r.value["fields"][0]["clusters"]] == ["BHG-PAD-2"]
    bad = query_hierarchy(field="Rudrasagar")
    assert bad.status == ToolStatus.UNAVAILABLE and "Aishwariya" in bad.message  # lists the 4 fields
    assert query_hierarchy(cluster_id="NOPE").status == ToolStatus.UNAVAILABLE


def test_geojson_files_three_pads_for_bhagyam():
    gj = load_field_geojson("Bhagyam")
    kinds = [f["properties"]["kind"] for f in gj["features"]]
    assert kinds.count("FIELD_BOUNDARY") == 1 and kinds.count("CLUSTER_POLYGON") == 3
    assert all(f["properties"]["is_synthetic_geometry"] for f in gj["features"])
    assert {p["properties"]["cluster_id"] for p in cluster_polygons("Bhagyam")} == {"BHG-PAD-1", "BHG-PAD-2", "BHG-PAD-3"}
    assert len(cluster_polygons("Aishwariya")) == 3
    # committed file == deterministic rebuild from data
    assert build_field_geojson("Bhagyam")["features"] == gj["features"]


def _inside(lon, lat, ring):
    c = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            c = not c
    return c


def test_bhagyam_map_only_bhg_wells_and_3_pad_polygons():
    r = render_well_map(field="Bhagyam")
    v = r.value
    assert len(v.points) == 120 and all(p["well_id"].startswith("BHG-") for p in v.points)
    assert len(v.cluster_polygons) == 3
    rings = {p["properties"]["cluster_id"]: p["geometry"]["coordinates"][0] for p in v.cluster_polygons}
    for p in v.points:  # every well sits inside its own pad polygon
        assert _inside(p["lng"], p["lat"], rings[p["cluster_id"]]), p["well_id"]
    assert any(p["oil_bopd"] is not None for p in v.points)


def test_multi_field_map():
    r = render_well_map(field="Bhagyam,Aishwariya")
    assert r.value.fields == ["Bhagyam", "Aishwariya"] and len(r.value.points) == 220
    assert len(r.value.cluster_polygons) == 6
    assert len(render_well_map(field="ALL").value.points) == 460
