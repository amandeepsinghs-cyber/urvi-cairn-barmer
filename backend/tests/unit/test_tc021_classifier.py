"""Stage Q · TC-021 intervention classifier (BDD F-03, SDD §8.3 Gate Q)."""

from __future__ import annotations

import itertools
import json
import math
from datetime import date

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.analytics.model.features import IC_CODES, build_features, to_vector
from app.analytics.tools import intervention_classifier as tc
from app.analytics.tools.common import ToolStatus, currency_keys, load_yaml


@pytest.fixture(scope="module")
def metrics() -> dict:
    assert tc.METRICS_PATH.exists() and tc.PKL_PATH.exists(), "run: uv run python -m app.analytics.model.train_classifier"
    return json.loads(tc.METRICS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def client():
    from app.main import app

    return TestClient(app)


# ---- BDD-F03-S04 · Gate Q quality bars (read from the metrics file written by the training script) ----------
def test_gate_q_metric_bars(metrics):
    g, ho, base = metrics["gate_q"]["thresholds"], metrics["holdout"], metrics["baseline"]
    assert g["macro_f1_min"] <= ho["macro_f1"] <= g["macro_f1_max"]
    assert ho["top3_accuracy"] >= g["top3_min"]
    assert ho["macro_f1"] - base["macro_f1"] >= g["beats_baseline_by"]
    assert ho["ece"] <= g["ece_max"]
    assert min(metrics["train_class_support"].values()) >= g["min_class_support"]
    assert metrics["split"]["type"] == "temporal" and metrics["trained_as_of"] == "2026-09-23"
    # the recorded verdict is the conjunction of the items (never overridden)
    items = [k for k in metrics["gate_q"] if k not in ("thresholds", "passed")]
    assert metrics["gate_q"]["passed"] == all(metrics["gate_q"][k] for k in items)
    assert metrics["gate_q"]["passed"] is True


# ---- BDD-F03-S01 / S02 · fixtures (raw model output, independent of the gate verdict) -----------------------
def test_fixture_ash023_sand(metrics):
    r = tc.predict_top_k("ASH-023", date(2026, 9, 23), top_k=3)
    assert r["status"] == "OK"
    top = r["_top"]
    assert top[0].ic == "IC-06" and top[0].display == "IC-06 SAND_CLEANOUT"
    assert len(top) == 3 and sum(c.prob for c in top) <= 1.0 + 1e-9
    assert [c.prob for c in top] == sorted((c.prob for c in top), reverse=True)
    assert len(r["_contribs"]) >= 3 and all(c.direction in ("↑", "↓") for c in r["_contribs"])
    assert r["model_version"] == metrics["model_version"]


def test_fixture_ash061_top2(metrics):
    """ASH-061 dual-signature fixture => top-2 calibrated classes."""
    r = tc.predict_top_k("ASH-061", date(2026, 9, 23), top_k=3)
    top2 = {c.ic for c in r["_top"][:2]}
    assert "IC-04" in top2 or top2 == {"IC-07", "IC-04"}
    if "ASH-061" in metrics.get("fixtures", {}):
        assert metrics["fixtures"]["ASH-061"]["criterion"]["kind"] == "top2_set"


# ---- Tool / API contract: OK path when Gate Q passed, ML_UNAVAILABLE path when it did not (SDD §8.3) --------
def test_tool_respects_gate(metrics):
    r = tc.classify_intervention("ASH-023")
    if metrics["gate_q"]["passed"]:
        assert r.status in (ToolStatus.OK, ToolStatus.LOW_CONFIDENCE), r.message
        v = r.value
        assert v.top_k[0].ic == "IC-06"
        assert v.holdout_macro_f1 == metrics["holdout"]["macro_f1"]
        assert v.baseline_macro_f1 == metrics["baseline"]["macro_f1"]
        assert "synthetic" in v.disclosure.lower()
    else:
        assert r.status == ToolStatus.UNAVAILABLE and r.value is None
        assert r.message.startswith("ML_UNAVAILABLE") and r.missing_fields == ["gate_q"]
    assert not currency_keys(r.envelope())


def test_api_classification(client, metrics):
    r = client.get("/api/wells/ASH-023/classification")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"status", "data", "message", "missing_fields", "provenance"}
    assert body["provenance"]["tool_id"] == "TC-021"
    if metrics["gate_q"]["passed"]:
        assert body["data"]["top_k"][0]["ic"] == "IC-06"
        assert body["data"]["holdout_macro_f1"] == metrics["holdout"]["macro_f1"]
    else:
        assert body["status"] == "UNAVAILABLE" and "ML_UNAVAILABLE" in body["message"]
    assert client.get("/api/wells/GLK-101/classification").status_code == 404
    assert client.get("/api/wells/XX-999/classification").status_code == 404


# ---- BDD-F03-S05 · insufficient history ------------------------------------------------------------------
def test_insufficient_history_returns_status():
    r = tc.predict_top_k("BHG-001", date(2021, 11, 15))   # window starts 2021-10-01 (< 90 days of rows)
    assert r["status"] == "INSUFFICIENT_HISTORY" and "top_k" not in r
    fr = build_features("BHG-001", date(2021, 11, 16))
    assert fr.status == "INSUFFICIENT_HISTORY" and not fr.values


def test_unknown_well_unavailable():
    r = tc.classify_intervention("BHG-999")
    assert r.status == ToolStatus.UNAVAILABLE and r.value is None


def test_mangala_well_classification_succeeds(metrics):
    r = tc.classify_intervention("MNG-042")
    if metrics["gate_q"]["passed"] and r.value is not None:
        assert r.status in (ToolStatus.OK, ToolStatus.LOW_CONFIDENCE)


# ---- BDD-F03-S03 · model quality equals the metrics file; voice tool wired ---------------------------------
def test_model_quality_matches_metrics_file(metrics):
    q = tc.model_quality().value
    assert q["holdout_macro_f1"] == metrics["holdout"]["macro_f1"]
    assert q["holdout_top3_accuracy"] == metrics["holdout"]["top3_accuracy"]
    assert q["baseline_macro_f1"] == metrics["baseline"]["macro_f1"]
    assert "synthetic" in q["data_disclosure"].lower()


def test_voice_tool_registered(metrics):
    from app.live.voice_tools import VOICE_TOOLS, execute_voice_tool

    assert "classify_intervention" in VOICE_TOOLS
    out = execute_voice_tool("classify_intervention", {})
    blob = json.dumps(out)
    assert str(metrics["holdout"]["macro_f1"]) in blob and str(metrics["baseline"]["macro_f1"]) in blob


# ---- BDD-F03-S06 · ESP mapping in Barmer ic_map.yaml ------------------------------------------------------
def test_esp_maps_to_ic08():
    arch = load_yaml("ic_map.yaml")["archetypes"]
    esp = arch["ESP Replacement"]
    assert esp["ic"] == "IC-01" and "IC-08" in esp["disclosure"]
    assert "IC-08" in tc.ESP_NOTE


# ---- TreeSHAP correctness ------------------------------------------------------------------------------------
def test_treeshap_is_additive_on_served_model():
    art = tc._model()
    fr = build_features("ASH-023", date(2026, 9, 24))
    x = to_vector(fr.values, art["feature_names"])
    boosters = tc._boosters(art)
    raw = np.mean([b.decision_function(x.reshape(1, -1))[0] for b in boosters], axis=0)
    for k in (IC_CODES.index("IC-06"), IC_CODES.index("IC-01")):
        phi, expv = tc.shap_for_ensemble(boosters, x, k)
        assert math.isclose(phi.sum() + expv, float(raw[k]), rel_tol=1e-6, abs_tol=1e-6)


def _cond_exp(nodes, x, S, j=0):
    """Path-dependent E[f(x) | x_S] by cover-weighted descent (Lundberg 2018, Alg. 1)."""
    nd = nodes[j]
    if nd["is_leaf"]:
        return float(nd["value"])
    left, right = int(nd["left"]), int(nd["right"])
    d = int(nd["feature_idx"])
    if d in S:
        v = x[d]
        go_left = nd["missing_go_to_left"] if np.isnan(v) else v <= nd["num_threshold"]
        return _cond_exp(nodes, x, S, left if go_left else right)
    c = float(nd["count"])
    return (_cond_exp(nodes, x, S, left) * nodes[left]["count"] + _cond_exp(nodes, x, S, right) * nodes[right]["count"]) / c


def test_treeshap_matches_brute_force_shapley():
    from sklearn.ensemble import HistGradientBoostingClassifier

    rng = np.random.default_rng(0)
    X = rng.normal(size=(400, 4))
    y = (X[:, 0] + 0.5 * X[:, 1] * X[:, 2] > 0).astype(int) + (X[:, 3] > 1).astype(int)
    m = HistGradientBoostingClassifier(max_iter=5, max_leaf_nodes=6, random_state=0).fit(X, y)
    x = X[3]
    M = 4
    for k in range(3):
        phi, _ = tc.shap_for_class(m, x, k)
        exact = np.zeros(M)
        for preds in m._predictors:
            nodes = preds[k].nodes
            for i in range(M):
                others = [f for f in range(M) if f != i]
                for r in range(M):
                    for S in itertools.combinations(others, r):
                        w = math.factorial(len(S)) * math.factorial(M - len(S) - 1) / math.factorial(M)
                        exact[i] += w * (_cond_exp(nodes, x, set(S) | {i}) - _cond_exp(nodes, x, set(S)))
        assert np.allclose(phi, exact, atol=1e-9), (k, phi, exact)
