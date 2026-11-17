"""Stage C1 data-contract validator for Cairn Oil & Gas — Barmer Basin (SDD §5.5 V-N1..V-N7, DC-010/DC-014).

    uv run python -m app.analytics.generator.validate --field all

Exit code 0 = no violations, 1 = violations, 2 = missing data.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from app import settings

from .fields import FIELD_CONFIGS, resolve_field
from .geometry import point_in_polygon
from .native import rag014_offsets

EXPECTED_WELLS = {"Mangala": 180, "Bhagyam": 120, "Aishwariya": 100, "Raageshwari": 60}
EXPECTED_CLUSTERS = {"Mangala": 4, "Bhagyam": 3, "Aishwariya": 3, "Raageshwari": 3}
GAP_TARGET = {
    "Mangala": (0.01, 0.035),
    "Bhagyam": (-0.16, 0.035),
    "Aishwariya": (-0.03, 0.035),
    "Raageshwari": (0.02, 0.035),
}
QTD = (date(2026, 7, 1), settings.AS_OF)
T12M = (settings.AS_OF - timedelta(days=364), settings.AS_OF)
FIELD_TABLES = [
    "well_master",
    "daily_production",
    "well_tests",
    "well_status_history",
    "workover_history",
    "well_offsets",
    "document_index",
    "operations_events",
    "casing_tally",
    "tubing_string",
    "perforation_intervals",
    "pressure_surveys",
    "formation_tops",
]
ASSET_TABLES = [
    "job_catalogue",
    "mro_inventory",
    "rig_calendar",
    "field_master",
    "cluster_master",
    "facility_master",
    "field_targets",
]
MANGALA_EXTRA = ["well_run", "draft_plan", "decision_log"]
IC_MIN_ROWS = 35
CURRENCY_TOKENS = ("cost_usd", "_usd", "currency", "payback")


def load(landing: Path, folder: str, table: str) -> pd.DataFrame:
    return pd.read_parquet(landing / folder / f"{table}.parquet")


# ------------------------------------------------------------------------------------------------
# metrics shared with pin_targets
# ------------------------------------------------------------------------------------------------
def gap(landing: Path, field: str, window: tuple[date, date]) -> float:
    from .targets import gap_vs_target

    t = load(landing, "asset", "field_targets")
    d = load(landing, field.lower(), "daily_production")[["production_date", "oil_rate_bopd"]]
    return gap_vs_target(t[t.field == field], d, *window)


def status_days(status: pd.DataFrame, well: str, st: str, lo: date, hi: date) -> int:
    s = status[(status.well_id == well) & (status.status == st)]
    n = 0
    for r in s.itertuples(index=False):
        a = max(r.start_date, lo)
        b = min(r.end_date or hi, hi)
        n += max(0, (b - a).days + 1)
    return n


def bhg019_waits(landing: Path) -> dict:
    st = load(landing, "bhagyam", "well_status_history")
    wo = load(landing, "bhagyam", "workover_history")
    pump = wo[(wo.well_id == "BHG-019") & (wo.catalogue_job_code == "PUMP_OVERHAUL")].sort_values("start_date")
    job = pump.iloc[-1]
    lo = settings.AS_OF - timedelta(days=179)
    hi = job.start_date - timedelta(days=1)
    ev = load(landing, "bhagyam", "operations_events")
    ev = ev[(ev.well_id == "BHG-019") & (ev.trigger_ref == job.workover_id)]
    ev_days = {
        t: int(((g.end_date - g.start_date).apply(lambda x: x.days) + 1).sum())
        for t, g in ev.groupby("event_type")
    }
    return dict(
        workover_id=job.workover_id,
        job_start=job.start_date,
        wait_on_rig_days=status_days(st, "BHG-019", "WAITING_ON_RIG", lo, hi),
        wait_on_material_days=status_days(st, "BHG-019", "WAITING_ON_MATERIAL", lo, hi),
        events=ev_days,
    )


# Backward-compatible alias
lkw047_waits = bhg019_waits


def decline_pct(daily: pd.DataFrame, well: str, a: date, b: date, k: int = 14) -> float:
    d = daily[(daily.well_id == well) & daily.is_producing]
    pre = d[(d.production_date >= a - timedelta(days=k)) & (d.production_date < a)].oil_rate_bopd.mean()
    post = d[(d.production_date > b - timedelta(days=k)) & (d.production_date <= b)].oil_rate_bopd.mean()
    return float(post / pre - 1.0)


def rag014_residuals(landing: Path) -> dict:
    cfg = FIELD_CONFIGS["Raageshwari"]
    wells = load(landing, "raageshwari", "well_master")
    daily = load(landing, "raageshwari", "daily_production")[
        ["well_id", "production_date", "oil_rate_bopd", "is_producing"]
    ]
    days = int(cfg.fixtures["RAG-014"].params["signature_days"])
    a, b = settings.AS_OF - timedelta(days=days - 1), settings.AS_OF
    me = decline_pct(daily, "RAG-014", a, b)
    offs = {w: decline_pct(daily, w, a, b) for w in rag014_offsets(wells, cfg)}
    return dict(
        rag014_decline=me,
        offsets=offs,
        max_abs_residual_pp=max(abs(v - me) for v in offs.values()) * 100,
    )


# Backward-compatible alias
lkm090_residuals = rag014_residuals


def ic_counts(landing: Path) -> dict[str, int]:
    frames = [load(landing, f.lower(), "workover_history") for f in FIELD_CONFIGS]
    wo = pd.concat([f[["intervention_class", "is_censored"]] for f in frames])
    return wo[~wo.is_censored.astype(bool)].intervention_class.value_counts().sort_index().to_dict()


# ------------------------------------------------------------------------------------------------
# checks
# ------------------------------------------------------------------------------------------------
def check_field(landing: Path, field: str) -> list[str]:
    v: list[str] = []
    cfg = FIELD_CONFIGS[field]
    fl = field.lower()
    missing = [
        t
        for t in FIELD_TABLES + (MANGALA_EXTRA if field == "Mangala" else [])
        if not (landing / fl / f"{t}.parquet").exists()
    ]
    if missing:
        return [f"{field}: missing tables {missing}"]
    wells = load(landing, fl, "well_master")
    daily = load(landing, fl, "daily_production")
    status = load(landing, fl, "well_status_history")
    wo = load(landing, fl, "workover_history")
    ev = load(landing, fl, "operations_events")
    fm = load(landing, "asset", "field_master").set_index("field")

    # V-N1 well counts, prefixes, clusters, boundary
    if len(wells) != EXPECTED_WELLS[field]:
        v.append(f"V-N1 {field}: {len(wells)} wells, expected {EXPECTED_WELLS[field]}")
    if not wells.well_id.str.startswith(cfg.prefix).all():
        v.append(f"V-N1 {field}: well ids without prefix {cfg.prefix}")
    if wells.cluster_id.nunique() != EXPECTED_CLUSTERS[field]:
        v.append(f"V-N1 {field}: {wells.cluster_id.nunique()} clusters, expected {EXPECTED_CLUSTERS[field]}")
    poly = [(lat, lon) for lon, lat in json.loads(fm.loc[field, "boundary_geojson"])["coordinates"][0]]
    outside = [w for w, la, lo in zip(wells.well_id, wells.latitude, wells.longitude) if not point_in_polygon(la, lo, poly)]
    if outside:
        v.append(f"V-N1 {field}: {len(outside)} wells outside boundary polygon")

    # DC-010 coverage: one row per well-day across the full window
    n_days = (settings.DATA_END - settings.DATA_START).days + 1
    cnt = daily.groupby("well_id").size()
    if not (cnt == n_days).all() or len(cnt) != len(wells):
        v.append(f"DC-010 {field}: well-day coverage not {n_days} for every well")
    if daily.production_date.min() != settings.DATA_START or daily.production_date.max() != settings.DATA_END:
        v.append(f"DC-010 {field}: window {daily.production_date.min()}..{daily.production_date.max()}")
    if daily.duplicated(["well_id", "production_date"]).any():
        v.append(f"DC-010 {field}: duplicate well-days")
    prod = daily[daily.is_producing]
    bal = (prod.liquid_rate_blpd - (prod.oil_rate_bopd + prod.water_rate_bwpd)).abs()
    if (bal > 0.15).any():
        v.append(f"DC-010 {field}: liquid != oil + water on {(bal > 0.15).sum()} rows")

    # DC-014 null-not-zero
    rate_cols = ["oil_rate_bopd", "water_rate_bwpd", "gas_rate_mscfd", "liquid_rate_blpd"]
    down = daily[~daily.is_producing]
    if down[rate_cols].notna().any().any():
        v.append(f"DC-014 {field}: {int(down[rate_cols].notna().any(axis=1).sum())} shut-in days with non-NULL rates")
    if prod[rate_cols].isna().any().any():
        v.append(f"DC-014 {field}: producing days with NULL rates")

    # V-N7 gap columns
    lift = dict(zip(wells.well_id, wells.lift_type))
    is_gl = daily.well_id.map(lift) == "GAS_LIFT"
    if daily.loc[~is_gl, ["gl_inj_rate_mscfd", "gl_inj_pressure_kgcm2"]].notna().any().any():
        v.append(f"V-N7 {field}: gl_inj_* non-NULL on non-gas-lift wells")
    if daily.loc[~daily.is_producing, ["wht_degc", "gl_inj_rate_mscfd", "gl_inj_pressure_kgcm2"]].notna().any().any():
        v.append(f"V-N7 {field}: gap columns non-NULL on non-producing days")
    if daily.loc[daily.is_producing & is_gl, ["gl_inj_rate_mscfd", "gl_inj_pressure_kgcm2"]].isna().any().any():
        v.append(f"V-N7 {field}: gl_inj_* NULL on producing gas-lift days")
    if daily.loc[daily.is_producing, "wht_degc"].isna().any():
        v.append(f"V-N7 {field}: wht_degc NULL on producing days")
    if "gor_scf_bbl" not in daily.columns:
        v.append(f"V-N7 {field}: gor_scf_bbl missing")
    ps = load(landing, fl, "pressure_surveys").sort_values(["well_id", "survey_date"])
    gaps = ps.groupby("well_id").survey_date.apply(lambda s: s.diff().dropna().apply(lambda x: x.days)).astype(int)
    if len(gaps) and ((gaps < 365) | (gaps > 731)).any():
        v.append(f"V-N7 {field}: pressure survey interval outside [12, 24] months")
    ft = load(landing, fl, "formation_tops")
    if ft.well_id.nunique() != len(wells):
        v.append(f"V-N7 {field}: formation_tops missing wells")

    # V-N2 every event overlaps >= 1 down/degraded day
    degraded = daily[(~daily.is_producing) | (daily.runtime_fraction < 0.999)][["well_id", "production_date"]]
    deg_by_well = {w: set(g.production_date) for w, g in degraded.groupby("well_id")}
    bad = 0
    for r in ev.itertuples(index=False):
        days = deg_by_well.get(r.well_id, set())
        d, ok = r.start_date, False
        end = r.end_date if r.end_date is not None else settings.DATA_END
        while d <= end:
            if d in days:
                ok = True
                break
            d += timedelta(days=1)
        bad += not ok
    if bad:
        v.append(f"V-N2 {field}: {bad} operations_events without a down/degraded day")
    if not ev.event_id.is_unique:
        v.append(f"V-N2 {field}: duplicate event_id")
    if (ev.responsible_function.str.contains(r"\b(?:Mr|Ms|Shri)\b", regex=True)).any():
        v.append(f"V-N2 {field}: responsible_function names a person")

    # DC-030 status episodes contiguous, non-overlapping
    for w, g in status.groupby("well_id"):
        g = g.sort_values("start_date")
        ends = g.end_date.tolist()
        starts = g.start_date.tolist()
        for i in range(1, len(g)):
            if ends[i - 1] is None or starts[i] != ends[i - 1] + timedelta(days=1):
                v.append(f"DC-030 {field}: {w} status episodes not contiguous")
                break

    # K-1 labels
    nc = wo[~wo.is_censored.astype(bool)]
    if nc.catalogue_job_code.isna().any() or nc.intervention_class.isna().any():
        v.append(f"K-1 {field}: non-censored workovers without catalogue_job_code / intervention_class")
    if "job_code" not in wo.columns:
        v.append(f"K-1 {field}: job_code dropped")
    if not wo.workover_id.is_unique:
        v.append(f"DC-040 {field}: duplicate workover_id")

    # currency (D-1): no currency columns in well-keyed tables
    for t in FIELD_TABLES:
        cols = [c for c in load(landing, fl, t).columns if any(tok in c.lower() for tok in CURRENCY_TOKENS)]
        if cols:
            v.append(f"D-1 {field}.{t}: currency columns {cols}")

    # gap vs target
    tgt, tol = GAP_TARGET[field]
    g = gap(landing, field, QTD)
    if abs(g - tgt) > tol + 1e-9:
        v.append(f"F-09 {field}: QTD gap {g:+.1%} outside {tgt:+.0%} ± {tol * 100:.1f} pp")

    # V-N4 fixtures
    if field == "Bhagyam":
        w = bhg019_waits(landing)
        if (w["wait_on_rig_days"], w["wait_on_material_days"]) != (38, 11):
            v.append(f"V-N4 BHG-019: waits {w['wait_on_rig_days']}/{w['wait_on_material_days']} != 38/11")
        st88 = status[(status.well_id == "BHG-088") & (status.start_date >= settings.AS_OF - timedelta(days=179))]
        if not ((st88.status == "SHUT_IN") & (st88.reason_code == "POWER_OUTAGE")).any():
            v.append("V-N4 BHG-088: no BHG-PAD-2 power outages in the 180-day window")
        if (st88.status.isin(["WAITING_ON_RIG", "UNDER_WORKOVER", "WAITING_ON_MATERIAL"])).any():
            v.append("V-N4 BHG-088: mechanical downtime inside the 180-day window")
    if field == "Raageshwari":
        r = rag014_residuals(landing)
        if r["max_abs_residual_pp"] > 5.0:
            v.append(f"V-N4 RAG-014: offset residual {r['max_abs_residual_pp']:.1f} pp > 5 pp")
    if field == "Aishwariya":
        d61 = daily[(daily.well_id == "ASH-061") & daily.is_producing]
        a = settings.AS_OF - timedelta(days=65)
        pre = d61[(d61.production_date < a) & (d61.production_date >= a - timedelta(days=30))]
        post = d61[(d61.production_date > settings.AS_OF - timedelta(days=14)) & (d61.production_date <= settings.AS_OF)]
        if not (post.thp_kgcm2.mean() > pre.thp_kgcm2.mean() + 2.0 and post.chp_kgcm2.mean() < pre.chp_kgcm2.mean() - 2.0):
            v.append("V-N4 ASH-061: no Jet-Pump GLV+WAX failure signature")
    return v


def check_asset(landing: Path) -> list[str]:
    v: list[str] = []
    missing = [t for t in ASSET_TABLES if not (landing / "asset" / f"{t}.parquet").exists()]
    if missing:
        return [f"asset: missing tables {missing}"]
    cat = load(landing, "asset", "job_catalogue")
    if "GLV_REPLACE" not in set(cat.job_code):
        v.append("K-2: GLV_REPLACE missing from job_catalogue")
    if "cost_band" not in cat.columns or not set(cat.cost_band) <= {"LOW", "MED", "HIGH"}:
        v.append("D-1: job_catalogue.cost_band missing / invalid")
    counts = ic_counts(landing)
    for i in range(1, 16):
        ic = f"IC-{i:02d}"
        if counts.get(ic, 0) < IC_MIN_ROWS:
            v.append(f"IC: {ic} has {counts.get(ic, 0)} non-censored rows < {IC_MIN_ROWS}")
    ft = load(landing, "asset", "field_targets")
    if ft.duplicated(["field", "month"]).any():
        v.append("field_targets: duplicate (field, month)")
    fac = load(landing, "asset", "facility_master")
    if set(fac.field) != set(FIELD_CONFIGS):
        v.append("facility_master: not every field has facilities")
    return v


def check_no_wall_clock() -> list[str]:
    """V-N3 (static part): no wall-clock reads in the generator package."""
    v = []
    root = Path(__file__).parent
    for p in sorted(root.rglob("*.py")):
        tree = ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in ("now", "today", "utcnow", "time_ns"):
                v.append(f"V-N3: wall-clock call .{node.attr}() in {p.relative_to(root)}:{node.lineno}")
    return v


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--field", default=None)
    ap.add_argument("--landing", default=str(settings.LANDING_DIR))
    a = ap.parse_args(argv)
    landing = Path(a.landing)
    if not landing.exists():
        print(f"no landing data at {landing}; run generate first", file=sys.stderr)
        return 2
    v: list[str] = []
    fields = list(FIELD_CONFIGS) if (a.field or "all").lower() == "all" else [resolve_field(a.field)]
    if None in fields:
        print(f"unknown field {a.field}", file=sys.stderr)
        return 2
    v += check_no_wall_clock()
    v += check_asset(landing)
    for f in fields:
        v += check_field(landing, f)
        print(f"  {f}: QTD gap {gap(landing, f, QTD):+.1%}, trailing-12m gap {gap(landing, f, T12M):+.1%}")
    if "Bhagyam" in fields:
        print(f"  BHG-019: {bhg019_waits(landing)}")
    if "Raageshwari" in fields:
        r = rag014_residuals(landing)
        print(f"  RAG-014 decline {r['rag014_decline']:+.1%}, max offset residual {r['max_abs_residual_pp']:.1f} pp")
    print(f"  IC counts: {ic_counts(landing)}")
    print(f"{len(v)} violations")
    for x in v:
        print(f"  [X] {x}")
    return 1 if v else 0


if __name__ == "__main__":
    raise SystemExit(main())
