"""Stage R · TC-027 counterfactual "why X and not Y?" (BDD F-13, SDD §9.2, Gate R)."""

from __future__ import annotations

import dataclasses

import pytest

from app.analytics.docs_pdf.store import get_store
from app.analytics.tools import counterfactual as cf
from app.analytics.tools import nba
from app.analytics.tools.common import ToolStatus, currency_keys, load_table

DIMS = ["diagnostic_fit", "well_history", "field_efficacy", "execution", "value", "verdict"]


def _cf(well: str, alt: str, rec: str | None = None):
    r = cf.compare_interventions(well, recommended_job=rec, alternative_job=alt)
    assert r.value is not None, r.message
    return r


@pytest.mark.parametrize("rec", ["WATER_SHUTOFF_SQUEEZE", None])
def test_mng042_squeeze_vs_wax_removal(rec):
    """Gate R: verdict + deciding dimension + cited prior-job document (scan / CBL)."""
    v = _cf("MNG-042", "WAX_REMOVAL", rec).value
    assert v.recommended.job_code == "CEMENT_SQUEEZE" and v.alternative.job_code == "WAX_HOTOIL"
    assert v.verdict == "RECOMMENDED_PREFERRED" and v.deciding_dimension == "diagnostic_fit"
    assert [r.dimension for r in v.rows] == DIMS
    cited = {c["doc_id"] for c in v.citations}
    assert {"DOC-SCAN-MNG-042-2019", "DOC-CBL-MNG042-2014"} <= cited
    store = get_store()
    for c in v.citations:
        assert store.pdf_path(c["doc_id"]) is not None and c["url"] == f"/api/docs/{c['doc_id']}.pdf"
    fit = v.rows[0]
    assert fit.recommended.symbol == "✔" and fit.alternative.symbol == "✘" and fit.winner == "RECOMMENDED"
    assert "DOC-SCAN-MNG-042-2019" in v.verdict_text or "diagnostic fit" in v.verdict_text


def test_mng042_vs_reperforation():
    v = _cf("MNG-042", "REPERFORATION", "WATER_SHUTOFF_SQUEEZE").value
    assert v.alternative.job_code == "RE_PERFORATION"
    assert v.verdict == "RECOMMENDED_PREFERRED" and v.deciding_dimension == "diagnostic_fit"
    assert v.rows[0].winner == "RECOMMENDED"


def test_row1_pressure_survey_values_match_table():
    """Row 1 covers reservoir / IPR: latest pressure_surveys row on or before as_of."""
    v = _cf("MNG-042", "WAX_REMOVAL").value
    ps = load_table("pressure_surveys")
    ps = ps[(ps["well_id"] == "MNG-042") & (ps["survey_date"] <= v.as_of)].sort_values("survey_date")
    last = ps.iloc[-1]
    vals = v.rows[0].recommended.values
    assert vals["survey_id"] == last["survey_id"]
    assert vals["sbhp_kgcm2"] == pytest.approx(float(last["sbhp_kgcm2"]))
    assert vals["pi_bpd_per_kgcm2"] == pytest.approx(float(last["pi_bpd_per_kgcm2"]))
    assert f"pressure_surveys:{last['survey_id']}" in v.rows[0].evidence_refs


def test_rows_cover_efficacy_and_execution_without_currency():
    r = _cf("MNG-042", "WAX_REMOVAL")
    v = r.value
    eff = v.rows[2]
    assert eff.recommended.values["n"] >= 0 and 0 <= eff.recommended.values["p_success"] <= 1
    ex = v.rows[3]
    for cell in (ex.recommended, ex.alternative):
        assert cell.values["cost_band"] in {"LOW", "MED", "HIGH"} and cell.values["rig_days"] >= 0
    assert currency_keys(r.envelope()) == []
    assert "payback" not in str(r.envelope()).lower()


def test_ash061_vs_reperf():
    v = _cf("ASH-061", "REPERFORATION").value
    assert v.verdict in {"RECOMMENDED_PREFERRED", "CLOSE"}
    assert len(v.rows) == 6


def _fake(c: nba.CandidateEval, score: float, fit: str = nba.FIT) -> nba.CandidateEval:
    return dataclasses.replace(c, score=score, diagnostic_fit=fit, fit_symbol=nba.FIT_SYMBOL[fit])


def test_verdict_rules():
    ev = nba.well_evidence("MNG-042")
    a = nba.evaluate_job("CEMENT_SQUEEZE", ev)
    b = nba.evaluate_job("STRADDLE_PACKER", ev)
    verdict, deciding, margin, txt = cf._verdict(_fake(a, 100.0), _fake(b, 95.0))
    assert (verdict, deciding) == ("CLOSE", "value") and margin == pytest.approx(5.0) and "Close call" in txt
    verdict, deciding, margin, _ = cf._verdict(_fake(a, 50.0), _fake(b, 100.0))
    assert (verdict, deciding, margin) == ("ALTERNATIVE_PREFERRED", "value", -50.0)
    verdict, deciding, _, _ = cf._verdict(_fake(a, 10.0), _fake(b, 100.0, nba.UNCLEAR))
    assert (verdict, deciding) == ("RECOMMENDED_PREFERRED", "diagnostic_fit")  # fit beats value
    verdict, _, _, _ = cf._verdict(_fake(a, 10.0, nba.CONTRADICTED), _fake(b, 100.0, nba.CONTRADICTED))
    assert verdict == "NEITHER_FITS"


@pytest.mark.parametrize("alt", ["CEMENT_SQUEEZE", "IC-11", "NOT_A_JOB_XYZ", ""])
def test_unavailable_cases(alt):
    r = cf.compare_interventions("MNG-042", recommended_job="CEMENT_SQUEEZE", alternative_job=alt)
    assert r.status == ToolStatus.UNAVAILABLE and r.value is None and r.missing_fields


def test_resolve_job_aliases():
    ev = nba.well_evidence("MNG-042")
    assert cf.resolve_job("WATER_SHUTOFF_SQUEEZE", ev)[0] == "CEMENT_SQUEEZE"
    assert cf.resolve_job("wax removal", ev)[0] == "WAX_HOTOIL"
    assert cf.resolve_job("REPERFORATION", ev)[0] == "RE_PERFORATION"
    assert cf.resolve_job("PUMP_OVERHAUL", ev)[0] == "PUMP_OVERHAUL"


def test_compare_route(client):
    resp = client.get("/api/wells/MNG-042/compare", params={"alternative": "WAX_REMOVAL",
                                                           "recommended": "WATER_SHUTOFF_SQUEEZE"})
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert d["verdict"] == "RECOMMENDED_PREFERRED" and d["deciding_dimension"] == "diagnostic_fit"
    assert [r["dimension"] for r in d["rows"]] == DIMS
    assert client.get("/api/wells/MNG-042/compare").status_code == 422  # alternative required
    assert client.get("/api/wells/ZZ-999/compare?alternative=WAX_REMOVAL").status_code == 404


def test_voice_compare_interventions():
    from app.live import voice_tools as vt

    out = vt.execute_voice_tool("compare_interventions", {"well_id": "MNG-042", "alternative": "WAX_REMOVAL"})
    assert out["status"] == "OK" and out["data"]["verdict"] == "RECOMMENDED_PREFERRED"
    assert vt.VOICE_TOOLS["compare_interventions"].action_kind == "counterfactual"
