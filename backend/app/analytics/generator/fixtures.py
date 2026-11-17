"""Scripted Barmer Basin demo stories (docs/build.md Part I §7) written into a ``WellSim`` inside its fixture window.

The renewal process for a fixture well stops at ``fw0`` (AS_OF − 200 d); the script below then
writes the story into the same state arrays the renderer reads, so daily rows, status episodes,
workover rows and operations_events stay mutually consistent (V-N2, V-N4).

All story numbers come from ``FieldConfig.fixtures[...].params`` (orchestrator-owned).
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np

from .catalogue import JOB_SPECS
from .simulate import Cycle, WellSim, apply_signature

FIXTURE_WINDOW_DAYS = 200          # renewal cycles stop this many days before AS_OF for fixture wells

# Fixture histories: the first renewal cycles of a fixture well take these jobs (None = drawn).
FORCED_HISTORY = {
    "MNG-042": ["STRADDLE_PACKER", None, "WAX_HOTOIL"],
    "ASH-023": ["SAND_CLEANOUT", None, "SAND_CLEANOUT"],
    "ASH-061": [None, "GLV_REPLACE"],
}

# BHG-088 / BHG-PAD-2 scripted desert 33kV feeder outages inside the 180-day window: (date, days). Cluster-wide.
BHG_PAD_2_SCRIPTED_OUTAGES = [
    ("2026-04-08", 2), ("2026-05-02", 1), ("2026-05-27", 3), ("2026-06-19", 1),
    ("2026-07-14", 2), ("2026-08-06", 2), ("2026-09-01", 1),
]


def _idx(sim: WellSim, iso: str) -> int:
    return (date.fromisoformat(iso) - sim.start).days


def expected_oil(sim: WellSim, d: int) -> float:
    """Noise-free oil the renderer would produce on day ``d`` (without the ``m_oil`` multiplier)."""
    a = sim.a
    qb = sim.q_base(d)
    wc0 = sim.wc_base(d)
    liq = qb / (1.0 - wc0 / 100.0) * sim.pm[d] * a["m_liq"][d] * a["m_ops"][d]
    wc = float(np.clip(wc0 + sim.wcp[d] + a["wc_add"][d], 1.0, 97.5))
    rt = float(np.clip(a["runtime"][d], 0.05, 1.0))
    return liq * (1 - wc / 100.0) * rt


def pin_oil_drop(sim: WellSim, a: int, b_incl: int, frac: float) -> None:
    """Make expected oil fall linearly by ``frac`` from the level on day a-1 to day b_incl; hold after."""
    ref = expected_oil(sim, a - 1)
    n = b_incl - a + 1
    for i, d in enumerate(range(a, sim.n)):
        k = min(1.0, (i + 1) / n)
        target = ref * (1.0 - frac * k)
        e = expected_oil(sim, d)
        sim.a["m_oil"][d] = float(np.clip(target / e, 0.0, 1.5)) if e > 0 else 1.0


def _run_pump_change_after_waits(sim: WellSim, params: dict, force_seq: int | None = None) -> None:
    p0, f = _idx(sim, params["precursor_start"]), _idx(sim, params["failure_date"])
    job = params["job"]
    sim.a["noise"][max(0, p0 - 15):f] = 0.35
    apply_signature(sim.a, JOB_SPECS[job]["signature"], p0, f, 1.0, sim.p)
    base_seq = len([c for c in sim.cycles if c.mode != "REVIEW"]) + 1
    seq = max(force_seq, base_seq) if force_seq is not None else base_seq
    wo_id = f"WO-{sim.row.well_id}-{seq:03d}"
    cyc = Cycle(
        job=job,
        failure_code=JOB_SPECS[job]["failure_code"],
        is_rigless=False,
        mode="FAILURE",
        fail_day=f,
        sig_start=p0,
        wait_rig=int(params["wait_on_rig_days"]),
        wait_mat=int(params["wait_on_material_days"]),
        repair=int(params["repair_days"]),
        outcome=params["outcome"],
        run_life=f - (max([c.job_end for c in sim.cycles], default=-1) + 1),
        rig_id=f"RIG-BARMER-{int(sim.rng.integers(1, 16)):02d}",
    )
    fc = cyc.failure_code
    d = f
    for st, etype, nd in (
        ("WAITING_ON_RIG", "WAIT_ON_RIG", cyc.wait_rig),
        ("WAITING_ON_MATERIAL", "WAIT_ON_MATERIAL", cyc.wait_mat),
    ):
        sim._mark_down(d, d + nd, fc)
        sim._set_status(d, d + nd, st, fc, None, False)
        sim._event(etype, d, d + nd - 1, wo_id)
        d += nd
    cyc.job_start, cyc.job_end, cyc.wo_id = d, d + cyc.repair - 1, wo_id
    cyc.report_doc_id = f"DOC-SCAN-{sim.row.well_id}-{seq:03d}"
    sim._mark_down(cyc.job_start, cyc.job_end + 1, fc)
    sim._set_status(cyc.job_start, cyc.job_end + 1, "UNDER_WORKOVER", fc, wo_id, False)
    sim.cycles.append(cyc)
    sim._apply_effect(cyc, JOB_SPECS[job]["signature"], 1.0)


def _pin_two_stage_drop(sim: WellSim, a: int, mid: int, b_incl: int, frac: float, mid_share: float = 0.86) -> None:
    """Drop oil by ``mid_share * frac`` over [a, mid] and to ``frac`` over [mid, b_incl], then hold flat."""
    ref = expected_oil(sim, a - 1)
    n1 = max(1, mid - a + 1)
    n2 = max(1, b_incl - mid)
    for d in range(a, sim.n):
        if d <= mid:
            k = (d - a + 1) / n1
            drop = frac * mid_share * k
        elif d <= b_incl:
            k = (d - mid) / n2
            drop = frac * (mid_share + (1.0 - mid_share) * k)
        else:
            drop = frac
        target = ref * (1.0 - drop)
        e = expected_oil(sim, d)
        sim.a["m_oil"][d] = float(np.clip(target / e, 0.0, 1.5)) if e > 0 else 1.0


def script_fixture(sim: WellSim, kind: str, params: dict, as_of_idx: int) -> None:
    n = sim.n
    if kind == "PUMP_CHANGE_AFTER_WAITS":
        _run_pump_change_after_waits(sim, params)
    elif kind == "WAX_HEATER_CHOKE":                 # BHG-019: earlier PCP overhaul + recent trace-heater wax choke
        _run_pump_change_after_waits(sim, params, force_seq=7)
        wax_days = int(params.get("wax_signature_days", 35))
        w0 = as_of_idx - wax_days + 1
        plateau_idx = as_of_idx - 7
        sim.a["noise"][max(0, as_of_idx - 50):n] = 0.30
        wht_target = float(params.get("wht_drop_to_degc", 40.8))
        for d in range(w0, n):
            doy = (sim.start.toordinal() + d - date(sim.start.year, 1, 1).toordinal() + 1)
            season_d = 4.0 * math.sin(2 * math.pi * (doy - 110.0) / 365.25)
            ramp = min(1.0, (d - w0 + 1) / max(1, plateau_idx - w0 + 1))
            sim.a["thp_add"][d] = 0.42 * ramp * sim.p.thp_base
            sim.a["m_liq"][d] = 1.0 - 0.28 * ramp
            desired_wht_add = (wht_target - (sim.p.wht_base + season_d)) * ramp
            sim.a["wht_add"][d] = desired_wht_add
        pin_oil_drop(sim, w0, plateau_idx, float(params.get("oil_drop_frac", 0.67)))
    elif kind == "CHANNELLING":                      # MNG-042: open polymer/water channelling at AS_OF
        for c in sim.cycles:
            if c.job == "WAX_HOTOIL" and c.outcome == "FAILED":
                c.outcome = "PARTIAL"
        if sim.row.well_id == "MNG-042":
            ho_day = as_of_idx - 120
            prev_end = max([c.job_end for c in sim.cycles if c.mode != "REVIEW"], default=0)
            if ho_day > prev_end + 25:
                seq = len([c for c in sim.cycles if c.mode != "REVIEW"]) + 1
                wo_id = f"WO-MNG-042-{seq:03d}"
                cyc = Cycle(
                    job="WAX_HOTOIL",
                    failure_code="WAX",
                    is_rigless=True,
                    mode="FAILURE",
                    fail_day=ho_day,
                    sig_start=ho_day - 20,
                    repair=1,
                    outcome="PARTIAL",
                    run_life=ho_day - (prev_end + 1),
                    rig_id=None,
                    job_start=ho_day,
                    job_end=ho_day,
                    wo_id=wo_id,
                    report_doc_id=f"DOC-SCAN-MNG-042-{seq:03d}",
                )
                sim._mark_down(ho_day, ho_day + 1, "WAX")
                sim._set_status(ho_day, ho_day + 1, "UNDER_WORKOVER", "WAX", wo_id, True)
                sim.cycles.append(cyc)
        a = as_of_idx - int(params["signature_days"]) + 1
        sim.wcp[max(0, as_of_idx - 500):n] = 0.0
        sim.a["noise"][max(0, a - 20):n] = 0.25
        pr = np.linspace(1.0 / (n - a), 1.0, n - a)
        sim.a["wc_add"][a:n] = 33.0 * (pr ** 2.0)
        sim.a["m_liq"][a:n] = 1.0 + 0.04 * pr
        sim.a["m_oil"][a:n] = 1.0
    elif kind == "GGS_POWER_OUTAGES":                # BHG-088: outages come from the scripted cluster events
        pass
    elif kind == "SAND_INFLUX":                      # ASH-023: open sand signature at AS_OF
        sim.a["noise"][max(0, as_of_idx - 50):as_of_idx - 28] = 0.18
        a = as_of_idx - 28
        apply_signature(sim.a, "SAND", a, n, 1.5, sim.p)
        pin_oil_drop(sim, a, as_of_idx, float(params["oil_drop_frac"]))
        for d in range(as_of_idx - 10, n):
            sim.a["m_oil"][d] *= (1.18 if d % 2 == 0 else 0.82)
    elif kind == "GLV_PLUS_WAX":                     # ASH-061: Jet-Pump nozzle/GLV degradation + wax build-up
        apply_signature(sim.a, "GLV", as_of_idx - int(params["glv_signature_days"]) + 1, n, 1.0, sim.p)
        apply_signature(sim.a, "WAX", as_of_idx - int(params["wax_signature_days"]) + 1, n, 0.8, sim.p)
    elif kind == "RESERVOIR_DECLINE":                # RAG-014: shared reservoir decline
        a = as_of_idx - int(params["signature_days"]) + 1
        sim.a["noise"][max(0, a - 30):n] = 0.30
        sim.a["thp_add"][a:n] = 0.0
        sim.a["chp_add"][a:n] = 0.0
        sim.a["wc_add"][a:n] = 0.0
        _pin_two_stage_drop(sim, a, as_of_idx - 45, as_of_idx - 7, float(params["decline_frac"]), mid_share=0.86)
    elif kind == "RESERVOIR_DECLINE_OFFSET":         # RAG-014 offsets (same zone, nearest)
        a = as_of_idx - int(params["signature_days"]) + 1
        sim.a["noise"][max(0, a - 30):n] = 0.30
        sim.a["thp_add"][a:n] = 0.0
        sim.a["chp_add"][a:n] = 0.0
        sim.a["wc_add"][a:n] = 0.0
        _pin_two_stage_drop(sim, a, as_of_idx - 45, as_of_idx - 7, float(params["offset_decline_frac"]), mid_share=0.86)
    else:
        raise ValueError(f"unknown fixture kind {kind}")


def scripted_cluster_events(field: str, start: date) -> list[dict]:
    if field != "Bhagyam":
        return []
    out = []
    for iso, nd in BHG_PAD_2_SCRIPTED_OUTAGES:
        out.append(dict(event_type="GRID_POWER_OUTAGE", cluster_id="BHG-PAD-2",
                        d0=(date.fromisoformat(iso) - start).days, n=nd, partial=False, runtime=0.0,
                        scripted=True))
    return out
