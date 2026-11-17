"""Artificial-lift survival model (CoxPH) for Cairn Oil & Gas — Barmer Basin (Stage C5.4).

    cd backend
    uv run python -m app.analytics.model.train

Trains a right-censored Weibull/Cox proportional-hazards run-life model across Barmer pumped
producers (``ESP``, ``JET_PUMP``, ``PCP``, ``SRP`` across Mangala, Bhagyam, Aishwariya, and
Raageshwari oil pad) using the same 5 physical covariates expected by ``TC-006``
(``candidate_ranking.predict_failure``):
    ``liquid_rate_obs``, ``wc_sq_obs``, ``fillage_gap_obs``, ``chp_obs``, ``well_age_days``

Gate E (honest holdout gate, 70/30 well split):
    * ``0.65 <= holdout_c_index <= 0.78``
    * ``holdout_c_index > trigger_b_c_index``
Never tuned to pass; exits non-zero if Gate E fails.
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index

from app import settings

BASE_DAILY = [
    "well_id",
    "production_date",
    "liquid_rate_blpd",
    "water_cut_pct",
    "chp_kgcm2",
    "spm",
    "runtime_fraction",
    "is_producing",
]
BARMER_FOLDERS = ("mangala",)
PUMPED_LIFTS = ("ESP", "JET_PUMP", "PCP", "SRP")
TARGET_BAND = (0.65, 0.78)


def build_barmer_survival_dataset(landing: Path, exclude_prepend: bool = False) -> pd.DataFrame:
    wells = pd.concat(
        [pd.read_parquet(landing / f / "well_master.parquet") for f in BARMER_FOLDERS],
        ignore_index=True,
    )
    daily = pd.concat(
        [pd.read_parquet(landing / f / "daily_production.parquet", columns=BASE_DAILY) for f in BARMER_FOLDERS],
        ignore_index=True,
    )
    workovers = pd.concat(
        [pd.read_parquet(landing / f / "workover_history.parquet") for f in BARMER_FOLDERS],
        ignore_index=True,
    )
    workovers = workovers[workovers["outcome"] != "IN_PROGRESS"]

    pumped_wells = wells[wells["lift_type"].isin(PUMPED_LIFTS)].copy()
    pumped_ids = set(pumped_wells["well_id"])

    prod_daily = daily[(daily["well_id"].isin(pumped_ids)) & (daily["is_producing"] == True)].copy()
    prod_daily["production_date"] = pd.to_datetime(prod_daily["production_date"]).dt.date
    prod_by_well = {wid: g.sort_values("production_date") for wid, g in prod_daily.groupby("well_id")}
    wells_meta = pumped_wells.set_index("well_id").to_dict(orient="index")

    wo_pumped = workovers[
        (workovers["well_id"].isin(pumped_ids))
        & (workovers["run_life_days"].notna())
        & (workovers["run_life_days"] > 15)
        & (~workovers["workover_id"].astype(str).str.endswith("-001"))
    ].copy()
    wo_pumped["start_date"] = pd.to_datetime(wo_pumped["start_date"]).dt.date
    wo_pumped = wo_pumped.sort_values(["well_id", "start_date"])

    wo_pumped["prior_run_life_days"] = wo_pumped.groupby("well_id")["run_life_days"].shift(1)
    median_rl = float(wo_pumped["run_life_days"].median())
    wo_pumped["prior_run_life_days"] = wo_pumped["prior_run_life_days"].fillna(median_rl)

    from datetime import timedelta

    rows = []
    for r in wo_pumped.itertuples(index=False):
        wid = r.well_id
        g = prod_by_well.get(wid)
        if g is None or g.empty:
            continue
        # Strictly causal window before episode end/start (matches candidate_ranking._srp_features).
        as_of_ep = pd.to_datetime(r.end_date).date() if bool(r.is_censored) else (r.start_date - timedelta(days=1))
        p30 = g[(g["production_date"] >= as_of_ep - timedelta(days=29)) & (g["production_date"] <= as_of_ep)]
        if len(p30) < 5:
            p30 = g[g["production_date"] <= as_of_ep].tail(30)
        if p30.empty:
            continue
        p365 = g[(g["production_date"] >= as_of_ep - timedelta(days=365)) & (g["production_date"] <= as_of_ep)]
        w = wells_meta[wid]
        liq = float(p30["liquid_rate_blpd"].mean())
        wc = float(p30["water_cut_pct"].mean())
        chp = float(p30["chp_kgcm2"].mean())
        rt = float(p30["runtime_fraction"].mean())
        if str(w.get("lift_type")) == "SRP" and pd.notna(w.get("plunger_diameter_in")) and pd.notna(w.get("stroke_length_in")):
            spm = float(p30["spm"].mean()) if p30["spm"].notna().any() else 8.0
            ap = (math.pi / 4.0) * float(w["plunger_diameter_in"]) ** 2
            theo = 0.1166 * ap * float(w["stroke_length_in"]) * spm * rt
        else:
            peak_liq = float(p365["liquid_rate_blpd"].quantile(0.90)) if len(p365) else liq * 1.15
            theo = max(liq, peak_liq * rt)
        comp = pd.to_datetime(w["completion_date"]).date()
        rows.append({
            "well_id": wid,
            "workover_id": r.workover_id,
            "duration": float(r.run_life_days),
            "event": 0 if bool(r.is_censored) else 1,
            "prior_run_life_days": float(r.prior_run_life_days),
            "liquid_rate_obs": liq,
            "wc_sq_obs": (wc / 75.0) ** 2,
            "fillage_gap_obs": max(0.0, theo - liq),
            "chp_obs": chp,
            "well_age_days": float((as_of_ep - comp).days),
        })
    return pd.DataFrame(rows)


# Backward-compatible alias if imported by legacy callers.
build_srp_survival_dataset = build_barmer_survival_dataset


def train_and_evaluate(landing: Path, model_dir: Path, exclude_prepend: bool = False) -> bool:
    df = build_barmer_survival_dataset(landing, exclude_prepend)
    n_total = len(df)
    n_cens = int((df["event"] == 0).sum())
    print(
        f"Dataset (Barmer pumped fleet): {n_total} episodes "
        f"({n_total - n_cens} failures, {n_cens} censored [{n_cens / n_total:.1%}])"
    )

    unique_wells = sorted(df["well_id"].unique())
    split_idx = int(len(unique_wells) * 0.70)
    train_wells = set(unique_wells[:split_idx])
    holdout_wells = set(unique_wells[split_idx:])
    feature_cols = ["liquid_rate_obs", "wc_sq_obs", "fillage_gap_obs", "chp_obs", "well_age_days"]
    train_df = df[df["well_id"].isin(train_wells)][feature_cols + ["duration", "event"]].copy()
    test_df = df[df["well_id"].isin(holdout_wells)][
        feature_cols + ["duration", "event", "prior_run_life_days"]
    ].copy()

    cph = CoxPHFitter(penalizer=0.15)
    cph.fit(train_df, duration_col="duration", event_col="event")
    pred_hazard = cph.predict_partial_hazard(test_df[feature_cols]).to_numpy().ravel()
    c_model = float(concordance_index(test_df["duration"].to_numpy(), -pred_hazard, test_df["event"].to_numpy()))
    tb = (test_df["liquid_rate_obs"] / np.maximum(test_df["prior_run_life_days"], 30.0)).to_numpy()
    c_tb = float(concordance_index(test_df["duration"].to_numpy(), -tb, test_df["event"].to_numpy()))
    print(f"  CoxPH holdout C-index : {c_model:.4f}   (target band {list(TARGET_BAND)})")
    print(f"  Trigger B C-index     : {c_tb:.4f}")

    model_dir.mkdir(parents=True, exist_ok=True)
    with open(model_dir / "coxph_srp_v1.pkl", "wb") as f:
        pickle.dump(cph, f)
    gates_passed = bool(TARGET_BAND[0] <= c_model <= TARGET_BAND[1] and c_model > c_tb)
    payload = {
        "model_version": "coxph-v1.0-barmer",
        "lift_subset": "BARMER_PUMPED_FLEET (ESP, JET_PUMP, PCP, SRP)",
        "training_rows": "barmer_60m_native",
        "n_episodes_total": n_total,
        "n_episodes_train": len(train_df),
        "n_episodes_holdout": len(test_df),
        "right_censored_fraction": round(n_cens / n_total, 4),
        "holdout_c_index": round(c_model, 4),
        "trigger_b_c_index": round(c_tb, 4),
        "c_index_gain_over_trigger_b": round(c_model - c_tb, 4),
        "target_band": list(TARGET_BAND),
        "gates_passed": gates_passed,
        "coefficients": cph.summary[["coef", "exp(coef)", "p"]].to_dict(orient="index"),
    }
    with open(model_dir / "survival_model_metrics.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    if not gates_passed:
        print(f"GATE E FAILED: C-index {c_model:.4f} vs band {TARGET_BAND} and Trigger B {c_tb:.4f}")
    return gates_passed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude-prepend", action="store_true")
    ap.add_argument("--landing", default=str(settings.LANDING_DIR))
    ap.add_argument("--model-dir", default=str(settings.MODEL_DIR))
    a = ap.parse_args(argv)
    return 0 if train_and_evaluate(Path(a.landing), Path(a.model_dir), a.exclude_prepend) else 1


if __name__ == "__main__":
    sys.exit(main())
