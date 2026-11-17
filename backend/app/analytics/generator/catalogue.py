"""Job catalogue v2 and intervention-class labels for Cairn Oil & Gas — Barmer Basin (K-1, K-2; SDD §5.3, §8.1).

* ``build_job_catalogue()``: the 28 base rows + ``GLV_REPLACE`` (29 rows total), with append-only
  columns ``cost_band``, ``intervention_class``, ``sop_doc_id``.
* ``IC_MAP`` / ``IC_LABELS``: the pinned job_code <-> IC-01..IC-15 mapping across Barmer artificial
  lift systems (ESP, JET_PUMP, PCP, SRP, GAS_LIFT, NATURAL).
* ``JOB_SPECS``: per-job simulation semantics used by the native simulator.

Cost band thresholds are on the internal catalogue estimate (``est_cost_lakh_inr``) and the
currency figure itself never leaves the data layer (D-1).
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from app.analytics.generator.v030.job_catalogue import generate_job_catalogue

# Cost band cut points on est_cost_lakh_inr (internal only, never exposed; D-1).
COST_BAND_LOW_MAX = 10.0
COST_BAND_MED_MAX = 35.0

IC_LABELS: dict[str, str] = {
    "IC-01": "Artificial lift pump overhaul / ESP & PCP changeout",
    "IC-02": "Rod / drive-string / ESP power-cable remediation",
    "IC-03": "Production tubing replacement / descaling",
    "IC-04": "Waxy crude thermal & solvent flow assurance",
    "IC-05": "Inorganic & polymer scale treatment",
    "IC-06": "Unconsolidated sand & proppant cleanout / control",
    "IC-07": "Hydraulic jet-pump insert & lift-valve changeout",
    "IC-08": "Lift optimisation & ESP / jet-pump conversion",
    "IC-09": "Hydraulic proppant fracturing & matrix stimulation",
    "IC-10": "Stacked Fatehgarh perforation / re-perforation",
    "IC-11": "Polymer / water breakthrough conformance & squeeze",
    "IC-12": "Zonal isolation & up-hole Fatehgarh zone transfer",
    "IC-13": "Conformance choke & drawdown management",
    "IC-14": "Wellhead, heated flowline & casing barrier repair",
    "IC-15": "Sub-economic / no intervention justified",
}

IC_MAP: dict[str, list[str]] = {
    "IC-01": ["PUMP_OVERHAUL"],
    "IC-02": ["ROD_REPLACE"],
    "IC-03": ["TUBING_REPLACE"],
    "IC-04": ["WAX_SCRAPE", "WAX_HOTOIL", "WAX_SOLVENT", "WAX_INHIBITOR", "WAX_HEATER"],
    "IC-05": ["SCALE_ACID_BULLHEAD", "SCALE_INHIBITOR"],
    "IC-06": ["SAND_CLEANOUT", "SAND_CONTROL"],
    "IC-07": ["GLV_REPLACE"],
    "IC-08": ["LIFT_OPTIM", "GAS_SEP_INSTALL", "LIFT_CONVERSION"],
    "IC-09": ["MATRIX_ACID", "HYDRAULIC_FRAC"],
    "IC-10": ["RE_PERFORATION", "ADD_PERFORATION"],
    "IC-11": ["CEMENT_SQUEEZE", "POLYMER_GEL"],
    "IC-12": ["STRADDLE_PACKER", "ZONE_TRANSFER"],
    "IC-13": ["CHOKE_BACK"],
    "IC-14": ["SURFACE_REPAIR", "CASING_REPAIR"],
    "IC-15": ["NO_JOB_JUSTIFIED", "PLUG_ABANDON"],
}
JOB_TO_IC: dict[str, str] = {job: ic for ic, jobs in IC_MAP.items() for job in jobs}

GLV_REPLACE_ROW = (
    "GLV_REPLACE",
    "Hydraulic jet-pump nozzle/throat insert & gas-lift valve replacement (wireline)",
    "GAS_LIFT",
    "GL_VALVE",
    "Power-fluid / lift-gas injection pressure drop with rising injection rate and degraded liquid lift",
    False,
    "SLICKLINE_UNIT",
    1.0,
    4.5,
)


def cost_band(est_cost_lakh_inr: float) -> str:
    if est_cost_lakh_inr < COST_BAND_LOW_MAX:
        return "LOW"
    if est_cost_lakh_inr <= COST_BAND_MED_MAX:
        return "MED"
    return "HIGH"


def build_job_catalogue() -> pd.DataFrame:
    base = generate_job_catalogue()
    glv = pd.DataFrame([GLV_REPLACE_ROW], columns=list(base.columns))
    df = pd.concat([base, glv], ignore_index=True)
    df["cost_band"] = df["est_cost_lakh_inr"].map(cost_band)
    df["intervention_class"] = df["job_code"].map(JOB_TO_IC)
    df["sop_doc_id"] = [None if ic == "IC-15" else f"SOP-{ic}" for ic in df["intervention_class"]]
    return df


# ---------------------------------------------------------------------------------------------
# K-1: Legacy failure_code -> catalogue job mapping (weights; rigless rows only map to rigless jobs).
# ---------------------------------------------------------------------------------------------
PREPEND_FAILURE_TO_JOB: dict[tuple[str, bool], dict[str, float]] = {
    ("TUBING_LEAK", False): {"TUBING_REPLACE": 0.85, "CASING_REPAIR": 0.15},
    ("ROD_PART", False): {"ROD_REPLACE": 1.0},
    ("WAX", False): {"WAX_SCRAPE": 0.85, "WAX_HEATER": 0.15},
    ("WAX", True): {"WAX_HOTOIL": 0.60, "WAX_SOLVENT": 0.25, "WAX_INHIBITOR": 0.15},
    ("PUMP_WEAR", False): {"PUMP_OVERHAUL": 0.80, "LIFT_CONVERSION": 0.10, "GAS_SEP_INSTALL": 0.10},
    ("SURFACE", True): {"SURFACE_REPAIR": 0.75, "LIFT_OPTIM": 0.25},
    ("OTHER", False): {
        "MATRIX_ACID": 0.25,
        "RE_PERFORATION": 0.15,
        "ADD_PERFORATION": 0.10,
        "CEMENT_SQUEEZE": 0.20,
        "STRADDLE_PACKER": 0.10,
        "ZONE_TRANSFER": 0.05,
        "POLYMER_GEL": 0.05,
        "HYDRAULIC_FRAC": 0.10,
    },
    ("SUDDEN_MECH", False): {"ROD_REPLACE": 0.45, "PUMP_OVERHAUL": 0.35, "TUBING_REPLACE": 0.20},
    ("SAND", False): {"SAND_CLEANOUT": 0.80, "SAND_CONTROL": 0.20},
    ("SCALE", True): {"SCALE_ACID_BULLHEAD": 0.70, "SCALE_INHIBITOR": 0.30},
    ("GL_INJ_ANOMALY", False): {"GLV_REPLACE": 0.75, "TUBING_REPLACE": 0.15, "LIFT_CONVERSION": 0.10},
    ("GL_HEADING", True): {"LIFT_OPTIM": 0.85, "GLV_REPLACE": 0.15},
    ("GL_LOADING", False): {"GLV_REPLACE": 0.60, "LIFT_CONVERSION": 0.40},
}
DIRECT_JOB_CODES = {"WSO_STRADDLE": "STRADDLE_PACKER"}


def _row_rng(seed: int, key: str) -> np.random.Generator:
    """Per-row stream keyed by a stable hash so labels do not depend on row order."""
    h = int.from_bytes(hashlib.sha256(f"{seed}:{key}".encode()).digest()[:8], "big")
    return np.random.default_rng(h)


def label_legacy_workovers(wo: pd.DataFrame, seed: int = 42_001) -> pd.DataFrame:
    """Append catalogue_job_code + intervention_class (K-1). Censored rows get None."""
    cat_codes: list[str | None] = []
    for wid, job_code, fc, rigless, cens in zip(
        wo["workover_id"], wo["job_code"], wo["failure_code"], wo["is_rigless"], wo["is_censored"]
    ):
        if bool(cens):
            cat_codes.append(None)
            continue
        if job_code in DIRECT_JOB_CODES:
            cat_codes.append(DIRECT_JOB_CODES[job_code])
            continue
        weights = PREPEND_FAILURE_TO_JOB[(str(fc), bool(rigless))]
        jobs = list(weights)
        p = np.array([weights[j] for j in jobs], dtype=float)
        cat_codes.append(str(_row_rng(seed, str(wid)).choice(jobs, p=p / p.sum())))
    out = wo.copy()
    out["catalogue_job_code"] = cat_codes
    out["intervention_class"] = [JOB_TO_IC.get(c) if c else None for c in cat_codes]
    return out


# ---------------------------------------------------------------------------------------------
# Native simulation semantics per catalogue job.
#   failure_code : code written to workover_history.failure_code / daily downtime_reason
#   mode         : FAILURE (well goes down, waits for rig if rig job) | PLANNED (well keeps producing
#                  until the job) | REVIEW (no job executed, IC-15 NJJ) | TERMINAL (P&A)
#   signature    : precursor signature family in daily_production (see simulate.SIGNATURES)
#   effect       : post-job effect family
# ---------------------------------------------------------------------------------------------
JOB_SPECS: dict[str, dict] = {
    "PUMP_OVERHAUL": dict(failure_code="PUMP_WEAR", mode="FAILURE", signature="PUMP_WEAR", effect="RESTORE"),
    "ROD_REPLACE": dict(failure_code="ROD_PART", mode="FAILURE", signature="ROD_PART", effect="RESTORE"),
    "TUBING_REPLACE": dict(failure_code="TUBING_LEAK", mode="FAILURE", signature="TUBING_LEAK", effect="RESTORE"),
    "WAX_SCRAPE": dict(failure_code="WAX", mode="FAILURE", signature="WAX", effect="RESTORE"),
    "WAX_HOTOIL": dict(failure_code="WAX", mode="FAILURE", signature="WAX", effect="RESTORE"),
    "WAX_SOLVENT": dict(failure_code="WAX", mode="FAILURE", signature="WAX", effect="RESTORE"),
    "WAX_INHIBITOR": dict(failure_code="WAX", mode="PLANNED", signature="WAX", effect="RESTORE"),
    "WAX_HEATER": dict(failure_code="WAX", mode="FAILURE", signature="WAX", effect="RESTORE"),
    "SCALE_ACID_BULLHEAD": dict(failure_code="SCALE", mode="FAILURE", signature="SCALE", effect="RESTORE"),
    "SCALE_INHIBITOR": dict(failure_code="SCALE", mode="PLANNED", signature="SCALE", effect="RESTORE"),
    "SAND_CLEANOUT": dict(failure_code="SAND", mode="FAILURE", signature="SAND", effect="RESTORE"),
    "SAND_CONTROL": dict(failure_code="SAND", mode="FAILURE", signature="SAND", effect="RESTORE"),
    "GLV_REPLACE": dict(failure_code="GL_INJ_ANOMALY", mode="FAILURE", signature="GLV", effect="RESTORE"),
    "LIFT_OPTIM": dict(failure_code="LIFT_INEFFICIENCY", mode="PLANNED", signature="LIFT", effect="RESTORE"),
    "GAS_SEP_INSTALL": dict(failure_code="GAS_INTERFERENCE", mode="PLANNED", signature="LIFT", effect="RESTORE"),
    "LIFT_CONVERSION": dict(failure_code="OTHER", mode="PLANNED", signature="LIFT", effect="STIM_SMALL"),
    "MATRIX_ACID": dict(failure_code="PI_DECLINE", mode="PLANNED", signature="PI_DECLINE", effect="STIM"),
    "HYDRAULIC_FRAC": dict(failure_code="PI_DECLINE", mode="PLANNED", signature="PI_DECLINE", effect="STIM"),
    "RE_PERFORATION": dict(failure_code="PI_DECLINE", mode="PLANNED", signature="PERF", effect="STIM"),
    "ADD_PERFORATION": dict(failure_code="BYPASSED_PAY", mode="PLANNED", signature="PERF", effect="STIM"),
    "CEMENT_SQUEEZE": dict(failure_code="WATER_CHANNELLING", mode="PLANNED", signature="CHANNELLING", effect="WSO"),
    "POLYMER_GEL": dict(failure_code="WATER_CHANNELLING", mode="PLANNED", signature="CHANNELLING", effect="WSO"),
    "STRADDLE_PACKER": dict(failure_code="WATER_ZONE", mode="PLANNED", signature="ZONAL", effect="WSO"),
    "ZONE_TRANSFER": dict(failure_code="WATER_ZONE", mode="PLANNED", signature="ZONAL", effect="WSO_STIM"),
    "CHOKE_BACK": dict(failure_code="CONING", mode="PLANNED", signature="CONING", effect="CONING"),
    "SURFACE_REPAIR": dict(failure_code="SURFACE", mode="FAILURE", signature="SURFACE", effect="RESTORE"),
    "CASING_REPAIR": dict(failure_code="CASING_LEAK", mode="FAILURE", signature="CASING", effect="WSO"),
    "NO_JOB_JUSTIFIED": dict(failure_code="RESERVOIR_DECLINE", mode="REVIEW", signature="RESERVOIR", effect="NONE"),
    "PLUG_ABANDON": dict(failure_code="RESERVOIR_DECLINE", mode="TERMINAL", signature="RESERVOIR", effect="NONE"),
}


def __getattr__(name: str):
    if name.startswith("label_") and name.endswith("_workovers"):
        return label_legacy_workovers
    if name.endswith("_FAILURE_TO_JOB"):
        return PREPEND_FAILURE_TO_JOB
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
