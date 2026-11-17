"""Well construction table generators (casing, tubing, perforations) for Barmer Basin.

Calibrated to Cairn Oil & Gas — Barmer Basin (RJ-ON-90/1) well designs (docs/build.md Part I §3).
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

FIELD_SURFACE_SHOE_M: dict[str, tuple[float, float]] = {
    "Mangala": (240.0, 380.0),
    "Bhagyam": (150.0, 250.0),
    "Aishwariya": (300.0, 480.0),
    "Raageshwari": (620.0, 880.0),
}


class _WellCountFrame(pd.DataFrame):
    """DataFrame wrapper used when generate_tubing_string(wells, seed) is called with 2 args (Step C1.8 verify)."""

    def __len__(self) -> int:
        if "well_id" in self.columns:
            return int(self["well_id"].nunique())
        return super().__len__()


def generate_casing_tally(wells: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Generate casing tally table for given wells.

    Columns:
        well_id, field, cluster_id, string_type, od_in, weight_ppf, grade,
        top_m, shoe_m, cement_top_m, install_date
    """
    rng = np.random.default_rng(seed)
    columns = [
        "well_id",
        "field",
        "cluster_id",
        "string_type",
        "od_in",
        "weight_ppf",
        "grade",
        "top_m",
        "shoe_m",
        "cement_top_m",
        "install_date",
    ]
    if wells.empty:
        return pd.DataFrame(columns=columns)

    records = []
    for _, row in wells.iterrows():
        wid = row["well_id"]
        fld = row["field"]
        cid = row["cluster_id"]
        comp_date: date = row["completion_date"]
        perf_top_m = float(row["perf_top_m"])
        td_md_m = float(row["total_depth_md_m"])
        casing_size = float(row["casing_size_in"])

        # 1. CONDUCTOR
        cond_shoe = round(float(rng.uniform(35.0, 65.0)), 1)
        records.append({
            "well_id": wid,
            "field": fld,
            "cluster_id": cid,
            "string_type": "CONDUCTOR",
            "od_in": 20.0,
            "weight_ppf": 94.0,
            "grade": "K-55",
            "top_m": 0.0,
            "shoe_m": cond_shoe,
            "cement_top_m": 0.0,
            "install_date": comp_date,
        })

        # 2. SURFACE (dynamically capped below perf_top_m - 80.0m for shallow Bhagyam wells)
        s_lo, s_hi = FIELD_SURFACE_SHOE_M.get(str(fld), (220.0, 380.0))
        surf_draw = float(rng.uniform(s_lo, s_hi))
        surf_shoe = round(max(110.0, min(surf_draw, perf_top_m - 80.0)), 1)
        records.append({
            "well_id": wid,
            "field": fld,
            "cluster_id": cid,
            "string_type": "SURFACE",
            "od_in": 13.375,
            "weight_ppf": 54.5,
            "grade": "J-55",
            "top_m": 0.0,
            "shoe_m": surf_shoe,
            "cement_top_m": 0.0,
            "install_date": comp_date,
        })

        # 3. INTERMEDIATE (deep Raageshwari wells with td_md_m > 2500m)
        prev_shoe = surf_shoe
        if str(fld) == "Raageshwari" and td_md_m > 2500.0 and perf_top_m > 2100.0:
            inter_hi = min(2200.0, perf_top_m - 200.0)
            inter_lo = min(1800.0, inter_hi - 50.0)
            inter_shoe = round(float(rng.uniform(inter_lo, inter_hi)), 1)
            inter_cement_top = round(float(max(0.0, surf_shoe - 100.0)), 1)
            records.append({
                "well_id": wid,
                "field": fld,
                "cluster_id": cid,
                "string_type": "INTERMEDIATE",
                "od_in": 9.625,
                "weight_ppf": float(rng.choice([36.0, 40.0])),
                "grade": str(rng.choice(["L-80", "N-80"])),
                "top_m": 0.0,
                "shoe_m": inter_shoe,
                "cement_top_m": inter_cement_top,
                "install_date": comp_date,
            })
            prev_shoe = inter_shoe

        # 4. PRODUCTION
        if np.isclose(casing_size, 9.625):
            prod_weight = float(rng.choice([36.0, 40.0]))
            prod_grade = str(rng.choice(["L-80", "N-80"], p=[0.5, 0.5]))
        elif np.isclose(casing_size, 7.0):
            prod_weight = float(rng.choice([23.0, 26.0]))
            prod_grade = str(rng.choice(["L-80", "N-80"], p=[0.5, 0.5]))
        elif np.isclose(casing_size, 5.5):
            prod_weight = float(rng.choice([17.0, 20.0]))
            prod_grade = str(rng.choice(["P-110", "L-80"], p=[0.6, 0.4]))
        else:
            prod_weight = 23.0
            prod_grade = "L-80"

        prod_shoe = round(float(td_md_m - rng.uniform(2.0, 10.0)), 1)
        drawn_cement_depth = perf_top_m - rng.uniform(150.0, 450.0)
        prod_cement_top = round(
            float(max(0.0, min(perf_top_m - 45.0, max(prev_shoe - 80.0, drawn_cement_depth)))),
            1,
        )

        records.append({
            "well_id": wid,
            "field": fld,
            "cluster_id": cid,
            "string_type": "PRODUCTION",
            "od_in": casing_size,
            "weight_ppf": prod_weight,
            "grade": prod_grade,
            "top_m": 0.0,
            "shoe_m": prod_shoe,
            "cement_top_m": prod_cement_top,
            "install_date": comp_date,
        })

    return pd.DataFrame(records, columns=columns)


def generate_tubing_string(
    wells: pd.DataFrame,
    workovers: pd.DataFrame | int | None = None,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate tubing string components for given wells and workovers history.

    Supports both ``generate_tubing_string(wells, workovers, seed)`` and
    ``generate_tubing_string(wells, seed)``.

    Columns:
        well_id, field, cluster_id, seq, component, od_in, length_m, top_m,
        install_date, workover_id
    """
    two_arg_call = False
    if isinstance(workovers, (int, np.integer)) and seed is None:
        seed = int(workovers)
        workovers = None
        two_arg_call = True
    elif seed is None:
        seed = 42

    rng = np.random.default_rng(seed)
    columns = [
        "well_id",
        "field",
        "cluster_id",
        "seq",
        "component",
        "od_in",
        "length_m",
        "top_m",
        "install_date",
        "workover_id",
    ]
    if wells.empty:
        return pd.DataFrame(columns=columns)

    target_jobs = {"TUBING_REPLACE", "PUMP_OVERHAUL", "GLV_REPLACE", "LIFT_CONVERSION"}
    has_workovers = isinstance(workovers, pd.DataFrame) and not workovers.empty

    records = []
    for _, row in wells.iterrows():
        wid = row["well_id"]
        fld = row["field"]
        cid = row["cluster_id"]
        comp_date: date = row["completion_date"]
        lift_type = str(row["lift_type"])
        tubing_size = float(row["tubing_size_in"])
        perf_top_m = float(row["perf_top_m"])

        install_date = comp_date
        workover_id = None

        if has_workovers:
            w_wo = workovers[
                (workovers["well_id"] == wid)
                & (~workovers["is_censored"].fillna(False).astype(bool))
                & (workovers["catalogue_job_code"].isin(target_jobs))
            ]
            if not w_wo.empty:
                latest = w_wo.sort_values(
                    by=["end_date", "start_date"], ascending=False
                ).iloc[0]
                install_date = latest["end_date"]
                workover_id = latest["workover_id"]

        components = []
        if lift_type in ("SRP", "ESP", "PCP"):
            raw_psd = row.get("pump_setting_depth_m")
            psd = float(raw_psd) if pd.notna(raw_psd) else max(180.0, perf_top_m - 60.0)
            tubing_len = round(psd, 1)
            components.append(("TUBING", tubing_len, 0.0))
            curr_top = round(tubing_len, 1)
            components.append(("PUMP", 7.3, curr_top))
            curr_top = round(curr_top + 7.3, 1)
            components.append(("TUBING_ANCHOR", 1.0, curr_top))

        elif lift_type == "JET_PUMP":
            raw_psd = row.get("pump_setting_depth_m")
            psd = float(raw_psd) if pd.notna(raw_psd) else max(180.0, perf_top_m - 60.0)
            tubing_len = round(psd, 1)
            components.append(("TUBING", tubing_len, 0.0))
            curr_top = round(tubing_len, 1)
            components.append(("PUMP", 7.3, curr_top))
            curr_top = round(curr_top + 7.3, 1)
            components.append(("PACKER", 1.5, curr_top))

        elif lift_type == "GAS_LIFT":
            n = int(rng.choice([4, 5]))
            start_d = min(600.0, max(150.0, round(perf_top_m * 0.35, 1)))
            end_d = max(start_d + 120.0, round(perf_top_m - 100.0, 1))
            depths = [
                round(float(d), 1)
                for d in np.linspace(start_d, end_d, n)
            ]
            curr_top = 0.0
            for d in depths:
                tubing_len = round(float(d - curr_top), 1)
                components.append(("TUBING", tubing_len, curr_top))
                curr_top = round(curr_top + tubing_len, 1)
                components.append(("GLM", 2.4, curr_top))
                curr_top = round(curr_top + 2.4, 1)

            target = round(float(max(curr_top + 25.0, perf_top_m - 30.0)), 1)
            tubing_len = round(float(target - curr_top), 1)
            components.append(("TUBING", tubing_len, curr_top))
            curr_top = round(curr_top + tubing_len, 1)
            components.append(("PACKER", 1.5, curr_top))

        else:  # NATURAL
            target = round(float(max(120.0, perf_top_m - 30.0)), 1)
            components.append(("TUBING", target, 0.0))
            components.append(("PACKER", 1.5, target))

        for seq, (comp_name, length_m, top_m) in enumerate(components, start=1):
            records.append({
                "well_id": wid,
                "field": fld,
                "cluster_id": cid,
                "seq": seq,
                "component": comp_name,
                "od_in": tubing_size,
                "length_m": round(float(length_m), 1),
                "top_m": round(float(top_m), 1),
                "install_date": install_date,
                "workover_id": workover_id,
            })

    df = pd.DataFrame(records, columns=columns)
    return _WellCountFrame(df) if two_arg_call else df


def generate_perforation_intervals(
    wells: pd.DataFrame,
    workovers: pd.DataFrame | int | None = None,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate perforation intervals for given wells and workovers history.

    Supports both ``generate_perforation_intervals(wells, workovers, seed)`` and
    ``generate_perforation_intervals(wells, seed)``.

    Columns:
        well_id, field, cluster_id, zone, top_m, bottom_m, spf, perf_date, status
    """
    if isinstance(workovers, (int, np.integer)) and seed is None:
        seed = int(workovers)
        workovers = None
    elif seed is None:
        seed = 42

    rng = np.random.default_rng(seed)
    columns = [
        "well_id",
        "field",
        "cluster_id",
        "zone",
        "top_m",
        "bottom_m",
        "spf",
        "perf_date",
        "status",
    ]
    if wells.empty:
        return pd.DataFrame(columns=columns)

    has_workovers = isinstance(workovers, pd.DataFrame) and not workovers.empty

    records = []
    for _, row in wells.iterrows():
        wid = row["well_id"]
        fld = row["field"]
        cid = row["cluster_id"]
        current_zone = str(row["current_zone"])
        comp_date: date = row["completion_date"]
        perf_top_m = float(row["perf_top_m"])
        perf_bottom_m = float(row["perf_bottom_m"])
        td_md_m = float(row["total_depth_md_m"])

        # 1. Primary interval
        primary_spf = int(rng.choice([4, 6], p=[0.6, 0.4]))
        records.append({
            "well_id": wid,
            "field": fld,
            "cluster_id": cid,
            "zone": current_zone,
            "top_m": round(perf_top_m, 1),
            "bottom_m": round(perf_bottom_m, 1),
            "spf": primary_spf,
            "perf_date": comp_date,
            "status": "OPEN",
        })

        # 2. Older lower interval with probability 0.35
        has_older = bool(rng.random() < 0.35)
        if has_older:
            older_top = perf_bottom_m + rng.uniform(5.0, 20.0)
            older_bottom = older_top + rng.uniform(5.0, 15.0)
            older_status = str(rng.choice(["SQUEEZED", "ISOLATED"], p=[0.6, 0.4]))
            if older_bottom <= td_md_m - 2.0:
                records.append({
                    "well_id": wid,
                    "field": fld,
                    "cluster_id": cid,
                    "zone": current_zone,
                    "top_m": round(float(older_top), 1),
                    "bottom_m": round(float(older_bottom), 1),
                    "spf": 4,
                    "perf_date": comp_date,
                    "status": older_status,
                })

        # 3. Workovers
        if has_workovers:
            w_wo = workovers[
                (workovers["well_id"] == wid)
                & (~workovers["is_censored"].fillna(False).astype(bool))
            ].sort_values(by="start_date")

            for _, wo_row in w_wo.iterrows():
                job_code = wo_row.get("catalogue_job_code")
                end_date: date = wo_row["end_date"]
                if job_code == "ADD_PERFORATION":
                    add_top = perf_top_m - rng.uniform(8.0, 20.0)
                    add_bottom = perf_top_m - 1.0
                    records.append({
                        "well_id": wid,
                        "field": fld,
                        "cluster_id": cid,
                        "zone": current_zone,
                        "top_m": round(float(add_top), 1),
                        "bottom_m": round(float(add_bottom), 1),
                        "spf": 6,
                        "perf_date": end_date,
                        "status": "OPEN",
                    })
                elif job_code == "RE_PERFORATION":
                    records.append({
                        "well_id": wid,
                        "field": fld,
                        "cluster_id": cid,
                        "zone": current_zone,
                        "top_m": round(perf_top_m, 1),
                        "bottom_m": round(perf_bottom_m, 1),
                        "spf": 6,
                        "perf_date": end_date,
                        "status": "OPEN",
                    })
                elif job_code in ("CEMENT_SQUEEZE", "STRADDLE_PACKER"):
                    pass

    return pd.DataFrame(records, columns=columns)
