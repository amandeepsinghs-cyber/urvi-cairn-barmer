"""Stage P · ADK tool-contract tests on Urvi Cairn Barmer fields (Mangala, Bhagyam, Aishwariya, Raageshwari)."""

from __future__ import annotations

import inspect

import pytest

from app.analytics import tools as T
from app.analytics.tools.arps_decline import fit_decline_curve
from app.analytics.tools.candidate_ranking import (
    check_mro,
    check_offsets,
    detect_mechanical_signature,
    generate_draft_plan,
    plot_production,
    query_wells,
    rank_candidates,
    route_intervention,
    trigger_scan,
)
from app.analytics.tools.chan_diagnostic import chan_diagnostic
from app.analytics.tools.common import OffsetVerdict, ToolStatus, currency_keys


# --- TC-001 ---------------------------------------------------------------------------------------
def test_tc001_mng042_residual_below_minus_25():
    r = fit_decline_curve("MNG-042")
    assert r.status == ToolStatus.OK
    assert r.value.residual_pct < -25.0
    assert r.provenance["tool_id"] == "TC-001" and r.provenance["as_of"]


def test_tc001_fallback_only_replaces_low_fits():
    """Stage P fallback: LOW multi-cycle fits may be refitted since the last workover, and the refit is used
    only if it is itself not LOW (status == OK and r_squared >= 0.5)."""
    from app.analytics.tools.common import field_well_ids

    refits = [fit_decline_curve(w) for w in field_well_ids("Mangala") + field_well_ids("Aishwariya")]
    used = [r for r in refits if r.value is not None and r.value.fit_basis.startswith("SINCE_LAST_WORKOVER")]
    assert used and all(r.status == ToolStatus.OK and r.value.r_squared >= 0.5 for r in used)


def test_tc001_unknown_well_unavailable():
    assert fit_decline_curve("ZZ-999").status == ToolStatus.UNAVAILABLE


# --- TC-002 ---------------------------------------------------------------------------------------
def test_tc002_mng042_channelling():
    v = chan_diagnostic("MNG-042").value
    assert v.mechanism.value == "CHANNELLING"
    assert v.wor_prime_slope > 0.30
    assert v.paired_injectors == []  # no injector table in v0.4: never invented


def test_tc002_chan_diagnostic_valid_mechanism():
    v = chan_diagnostic("BHG-019").value
    assert v.mechanism.value in {"CHANNELLING", "CONING", "NORMAL_DISPLACEMENT", "INDETERMINATE"}


# --- TC-004 / TC-008 ------------------------------------------------------------------------------
def test_tc004_tc008_rag014_reservoir_decline_no_job():
    off = check_offsets("RAG-014").value
    assert off.verdict == OffsetVerdict.RESERVOIR_DECLINE
    route = route_intervention("RAG-014", None, off.verdict).value
    assert route.job_code == "NO_JOB_JUSTIFIED"


def test_tc008_channelling_routes_to_cement_squeeze():
    route = route_intervention("MNG-042", "CHANNELLING", OffsetVerdict.WELL_SPECIFIC).value
    assert route.job_code == "CEMENT_SQUEEZE" and route.requires_rig


# --- TC-005 ---------------------------------------------------------------------------------------
@pytest.mark.parametrize("well,sig", [("BHG-019", "WAX"), ("ASH-023", "SAND")])
def test_tc005_signatures_from_data(well, sig):
    assert detect_mechanical_signature(well).value.signature.value == sig


# --- TC-007 ---------------------------------------------------------------------------------------
def test_tc007_barmer_hero_wells():
    mng_rows = {r.well_id: r for r in trigger_scan("Mangala").value}
    assert mng_rows["MNG-042"].trigger_a in ("FLAG", "URGENT")
    assert mng_rows["MNG-042"].trigger_c == "CHANNELLING"

    bhg_rows = {r.well_id: r for r in trigger_scan("Bhagyam").value}
    assert bhg_rows["BHG-019"].trigger_c == "WAX"

    ash_rows = {r.well_id: r for r in trigger_scan("Aishwariya").value}
    assert ash_rows["ASH-023"].trigger_c == "SAND"


def test_tc007_unknown_field():
    assert trigger_scan("Atlantis").status == ToolStatus.UNAVAILABLE


# --- TC-010 ---------------------------------------------------------------------------------------
def test_tc010_rank_without_rupees():
    q = rank_candidates("Mangala").value
    assert q.rig_queue and q.rigless_queue
    assert all(r.cost_band in ("LOW", "MED", "HIGH") for r in q.rig_queue + q.rigless_queue)
    assert currency_keys(q) == []

    q_rag = rank_candidates("Raageshwari").value
    refused = {r.well_id if hasattr(r, "well_id") else r[0] for r in q_rag.excluded_refusals}
    assert "RAG-014" in refused


# --- TC-011 / TC-013 ------------------------------------------------------------------------------
def test_tc011_mro_returns_feasible_start():
    r = check_mro("CEMENT_SQUEEZE")
    assert r.status == ToolStatus.OK
    assert r.value["earliest_feasible_start"] is not None


def test_tc013_draft_plan_awaits_review():
    plan = generate_draft_plan("MNG-042").value
    assert plan["approval_status"] == "AWAITING REVIEW"
    assert currency_keys(plan) == []


# --- TC-017 / TC-018 ------------------------------------------------------------------------------
def test_tc017_plot_has_null_gaps_and_markers():
    ps = plot_production("MNG-042").value
    assert ps.n_producing_days > 90
    assert all(p.value is None for p in ps.series["oil"] if p.source == "NULL")
    assert all(m.outcome in ("SUCCESS", "PARTIAL", "FAILED", "UNKNOWN") for m in ps.interventions)


def test_tc018_rate_ranking_has_caveat():
    assert query_wells("Mangala", order_by="oil_rate_bopd").value.caveat
    assert query_wells("Mangala").value.caveat is None


# --- cross-cutting: K-6 (no hero defaults), D-1 (no currency) --------------------------------------
def test_no_hero_or_field_defaults_anywhere():
    for name in T.__all__:
        fn = getattr(T, name)
        if not callable(fn):
            continue
        for p in inspect.signature(fn).parameters.values():
            d = p.default
            if isinstance(d, str):
                assert "MNG-" not in d.upper() and "MANGALA" not in d.upper(), (name, p.name, d)


def test_exports_cover_tc001_to_tc020():
    expected = {"fit_decline_curve", "chan_diagnostic", "fillage_proxy", "check_offsets",
                "detect_mechanical_signature", "predict_failure", "trigger_scan", "route_intervention",
                "estimate_uplift", "rank_candidates", "check_mro", "search_well_history", "generate_draft_plan",
                "generate_report", "schedule_rigs", "plot_production", "query_wells", "attribute_decline",
                "classify_well_health"}
    assert expected <= set(T.__all__)


@pytest.mark.parametrize("call", [
    lambda: fit_decline_curve("BHG-019"), lambda: chan_diagnostic("RAG-014"), lambda: check_offsets("BHG-088"),
    lambda: detect_mechanical_signature("ASH-023"), lambda: trigger_scan("Aishwariya"),
    lambda: query_wells("Bhagyam"), lambda: plot_production("BHG-019"),
])
def test_no_currency_keys_in_tool_values(call):
    assert currency_keys(call().value) == []
