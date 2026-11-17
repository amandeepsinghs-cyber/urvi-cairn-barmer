"""Stage DG generator: tubing_tally and deviation_survey (Slice 1 — Barmer Basin).

Generates synthetic data-gap tables for Cairn Oil & Gas Barmer fields
(Mangala, Bhagyam, Aishwariya, Raageshwari):
(a) tubing_tally: joint-by-joint tubing tally derived from CURRENT tubing_string rows
(b) deviation_survey: directional survey stations every 30m to TD using minimum curvature,
    supporting both S-shaped directional MBA/RDG pad wells (MD/TVD ~ 1.12-1.28) and
    horizontal Barmer_Hill wells in Aishwariya (MD/TVD ~ 1.9-2.3, lateral inc ~ 86-90 deg).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from .common import FieldContext, well_rng

# Exposed constant listing wells with no tubing_string rows
NO_TUBING_WELLS: list[str] = []

# Nominal API Spec 5CT tubing dimensions keyed by od_in
API_NOMINAL: dict[float, dict[str, float]] = {
    2.375: {"id_in": 1.995, "drift_in": 1.901, "weight_ppf": 4.7},
    2.875: {"id_in": 2.441, "drift_in": 2.347, "weight_ppf": 6.5},
    3.5:   {"id_in": 2.992, "drift_in": 2.867, "weight_ppf": 9.3},
}

# Mapping of component names from tubing_string to standardized component_type
COMPONENT_MAP: dict[str, str] = {
    "GLM": "GL_MANDREL",
    "GL_MANDREL": "GL_MANDREL",
    "PUMP": "PUMP",
    "ESP": "ESP_ASSEMBLY",
    "ESP_PUMP": "ESP_ASSEMBLY",
    "ESP_ASSEMBLY": "ESP_ASSEMBLY",
    "JET_PUMP": "JET_PUMP",
    "JET_PUMP_CAVITY": "JET_PUMP",
    "PCP": "PCP_STATOR",
    "PCP_STATOR": "PCP_STATOR",
    "TUBING_ANCHOR": "TUBING_ANCHOR",
    "PACKER": "PACKER",
    "SEAT_NIPPLE": "SEAT_NIPPLE",
    "SEATING_NIPPLE": "SEAT_NIPPLE",
    "NIPPLE": "SEAT_NIPPLE",
    "SLIDING_SLEEVE": "SLIDING_SLEEVE",
    "PUP": "PUP",
}


def _split_tubing_segment(
    top_m: float,
    length_m: float,
    rng: np.random.Generator,
) -> list[tuple[str, float, float, float]]:
    """Split a TUBING row into joints (9.15 - 9.75 m) and a final PUP."""
    target_bottom = round(top_m + length_m, 2)
    curr_top = round(top_m, 2)
    rem = round(target_bottom - curr_top, 2)
    if rem <= 0.0:
        return []
    items: list[tuple[str, float, float, float]] = []

    # Leave room for a pup of at least 0.3m.
    # While rem > 9.75 + 1.5, we can safely pick a joint in [9.15, 9.75].
    while rem > 9.75 + 1.5:
        j_len = round(float(rng.uniform(9.15, 9.75)), 2)
        curr_bot = round(curr_top + j_len, 2)
        items.append(("TUBING_JOINT", curr_top, curr_bot, j_len))
        curr_top = curr_bot
        rem = round(target_bottom - curr_top, 2)

    # When remaining length is enough for another joint and a pup of >= 0.3m
    if rem >= 9.15 + 0.3:
        max_j = min(9.75, rem - 0.3)
        if max_j >= 9.15:
            j_len = round(float(rng.uniform(9.15, max_j)), 2)
            curr_bot = round(curr_top + j_len, 2)
            items.append(("TUBING_JOINT", curr_top, curr_bot, j_len))
            curr_top = curr_bot

    pup_len = round(target_bottom - curr_top, 2)
    if pup_len > 0.0:
        items.append(("PUP", curr_top, target_bottom, pup_len))
    return items


def _min_curv_step(
    md1: float,
    md2: float,
    inc1_deg: float,
    inc2_deg: float,
    azi1_deg: float,
    azi2_deg: float,
) -> tuple[float, float]:
    """Calculate TVD increment and DLS (deg/30m) between two survey stations."""
    d_md = md2 - md1
    if d_md <= 0.0:
        return 0.0, 0.0

    i1 = np.radians(inc1_deg)
    i2 = np.radians(inc2_deg)
    a1 = np.radians(azi1_deg)
    a2 = np.radians(azi2_deg)

    cos_beta = np.cos(i1) * np.cos(i2) + np.sin(i1) * np.sin(i2) * np.cos(a2 - a1)
    cos_beta = float(np.clip(cos_beta, -1.0, 1.0))
    beta = float(np.arccos(cos_beta))

    if beta < 1e-7:
        rf = 1.0
    else:
        rf = (2.0 / beta) * np.tan(beta / 2.0)

    d_tvd = (d_md / 2.0) * (np.cos(i1) + np.cos(i2)) * rf
    dls = float(np.degrees(beta)) * (30.0 / d_md)
    return float(d_tvd), dls


def _integrate_tvd(stations: np.ndarray, incs: np.ndarray, azi_deg: float) -> float:
    """Integrate total TVD at final station using minimum curvature."""
    tvd_accum = 0.0
    for idx in range(1, len(stations)):
        dt, _ = _min_curv_step(
            stations[idx - 1], stations[idx],
            incs[idx - 1], incs[idx],
            azi_deg, azi_deg,
        )
        tvd_accum += dt
    return tvd_accum


def _s_well_incs(
    stations: np.ndarray,
    kop: float,
    br: float,
    td_md: float,
    i_max: float,
) -> np.ndarray:
    """Build-hold-drop S-shaped inclination profile for directional pad wells."""
    build_len = max(30.0, 30.0 * (i_max / br))
    eob = min(kop + build_len, td_md * 0.55)
    sod = max(eob + 30.0, td_md * 0.84)
    i_end = 0.65 * i_max

    test_incs = np.zeros_like(stations)
    if eob > kop:
        mb = (stations > kop) & (stations < eob)
        test_incs[mb] = (stations[mb] - kop) / (eob - kop) * i_max
    mh = (stations >= eob) & (stations <= sod)
    test_incs[mh] = i_max
    if td_md > sod:
        md_drop = stations > sod
        test_incs[md_drop] = i_max - (stations[md_drop] - sod) / (td_md - sod) * (i_max - i_end)
    return test_incs


def _horizontal_incs(
    stations: np.ndarray,
    u: float,
    td_tvd: float,
    td_md: float,
    inc_lat: float,
) -> np.ndarray:
    """Build-and-lateral inclination profile for Barmer_Hill horizontal wells (~86-90 deg)."""
    kop = u * 0.72 * td_tvd
    build_len = max(180.0, u * 0.85 * td_tvd)
    eob = min(kop + build_len, td_md - 60.0)
    kop = min(kop, max(30.0, eob - 180.0))

    test_incs = np.zeros_like(stations)
    if eob > kop:
        mb = (stations > kop) & (stations < eob)
        test_incs[mb] = (stations[mb] - kop) / (eob - kop) * inc_lat
    mh = stations >= eob
    test_incs[mh] = inc_lat
    return test_incs


def generate(ctx: FieldContext) -> dict[str, pd.DataFrame]:
    """Generate business DataFrames for tubing_tally and deviation_survey."""
    field = ctx.field
    wm = ctx.t("well_master")
    ts = ctx.t("tubing_string")

    # Track wells with no tubing_string rows
    wm_well_ids = set(wm["well_id"])
    ts_well_ids = set(ts["well_id"])
    missing_tubing = sorted(list(wm_well_ids - ts_well_ids))
    global NO_TUBING_WELLS
    NO_TUBING_WELLS = missing_tubing

    # ---------------------------------------------------------
    # (a) tubing_tally: grain well x joint
    # ---------------------------------------------------------
    tally_rows: list[dict[str, object]] = []

    # Process each well present in tubing_string in deterministic order
    well_ids_with_ts = sorted(ts["well_id"].unique())
    for well_id in well_ids_with_ts:
        w_ts = ts[ts["well_id"] == well_id]
        if w_ts.empty:
            continue

        # Filter to CURRENT tubing_string rows (latest install_date set)
        max_install_date = w_ts["install_date"].max()
        curr_ts = w_ts[w_ts["install_date"] == max_install_date].sort_values("seq")

        # Deterministic per-well RNG for grade and joint lengths
        rng_tally = well_rng(well_id, "tubing_tally")
        well_grade = str(rng_tally.choice(["J-55", "N-80"]))

        joint_no = 1
        running_top: float | None = None
        for _, row in curr_ts.iterrows():
            cluster_id = row["cluster_id"]
            comp = str(row["component"]).strip()
            od_raw = float(row["od_in"])
            od = round(od_raw, 3)

            if od in API_NOMINAL:
                nom = API_NOMINAL[od]
                id_in = nom["id_in"]
                drift_in = nom["drift_in"]
                weight_ppf = nom["weight_ppf"]
                grade = well_grade
            else:
                id_in = np.nan
                drift_in = np.nan
                weight_ppf = np.nan
                grade = "UNKNOWN"

            row_top = round(float(row["top_m"]), 2)
            row_bot = round(float(row["top_m"]) + float(row["length_m"]), 2)
            seg_top = row_top if running_top is None else running_top
            seg_len = round(row_bot - seg_top, 2)
            if seg_len <= 0.0:
                continue

            if comp == "TUBING":
                sub_items = _split_tubing_segment(seg_top, seg_len, rng_tally)
                for ctype, top_md, bot_md, length in sub_items:
                    tally_rows.append({
                        "well_id": well_id,
                        "field": field,
                        "cluster_id": cluster_id,
                        "joint_no": joint_no,
                        "component_type": ctype,
                        "top_md_m": top_md,
                        "bottom_md_m": bot_md,
                        "length_m": length,
                        "od_in": od,
                        "id_in": id_in,
                        "drift_in": drift_in,
                        "grade": grade,
                        "weight_ppf": weight_ppf,
                    })
                    joint_no += 1
                    running_top = bot_md
            else:
                ctype = COMPONENT_MAP.get(comp, comp)
                top_md = seg_top
                length = seg_len
                bot_md = round(top_md + length, 2)
                tally_rows.append({
                    "well_id": well_id,
                    "field": field,
                    "cluster_id": cluster_id,
                    "joint_no": joint_no,
                    "component_type": ctype,
                    "top_md_m": top_md,
                    "bottom_md_m": bot_md,
                    "length_m": length,
                    "od_in": od,
                    "id_in": id_in,
                    "drift_in": drift_in,
                    "grade": grade,
                    "weight_ppf": weight_ppf,
                })
                joint_no += 1
                running_top = bot_md

    df_tally = pd.DataFrame(tally_rows)
    if df_tally.empty:
        df_tally = pd.DataFrame(columns=[
            "well_id", "field", "cluster_id", "joint_no", "component_type",
            "top_md_m", "bottom_md_m", "length_m", "od_in", "id_in",
            "drift_in", "grade", "weight_ppf",
        ])

    # ---------------------------------------------------------
    # (b) deviation_survey: grain well x station
    # ---------------------------------------------------------
    survey_rows: list[dict[str, object]] = []

    wm_sorted = wm.sort_values("well_id")
    for _, row in wm_sorted.iterrows():
        well_id = str(row["well_id"])
        cluster_id = row["cluster_id"]
        zone = str(row.get("current_zone") or "")
        td_md = float(row["total_depth_md_m"])
        td_tvd = float(row["total_depth_tvd_m"])
        max_dls = float(row["max_dls_deg_30m"]) if pd.notna(row.get("max_dls_deg_30m")) else np.nan

        rng_dev = well_rng(well_id, "deviation_survey")
        azi_deg = round(float(rng_dev.uniform(0.0, 360.0)), 2)

        stations_list = list(np.arange(0.0, td_md, 30.0))
        if not stations_list or (td_md - stations_list[-1]) > 1e-3:
            stations_list.append(td_md)
        stations = np.array(stations_list)

        md_tvd_ratio = td_md / max(td_tvd, 1.0)
        is_horizontal = (zone == "Barmer_Hill" and md_tvd_ratio >= 1.45) or (md_tvd_ratio >= 1.55)

        if (td_md - td_tvd) < 5.0 or md_tvd_ratio < 1.008:
            # Near-vertical well profile: slight random walk with inclination < 2.8 degrees
            incs = np.zeros_like(stations)
            inc_cur = 0.0
            for i in range(1, len(stations)):
                inc_cur = np.clip(inc_cur + float(rng_dev.uniform(-0.3, 0.3)), 0.05, 2.8)
                incs[i] = round(inc_cur, 2)
        elif is_horizontal:
            # Horizontal Barmer_Hill well profile: builds to 86.5 - 89.5 deg lateral
            inc_lat = round(float(rng_dev.uniform(86.5, 89.5)), 2)

            def _sim_horiz(u_val: float) -> float:
                test_incs = _horizontal_incs(stations, u_val, td_tvd, td_md, inc_lat)
                return _integrate_tvd(stations, test_incs, azi_deg) - td_tvd

            f_lo, f_hi = _sim_horiz(0.01), _sim_horiz(0.99)
            if f_lo * f_hi < 0.0:
                u_sol = float(brentq(_sim_horiz, 0.01, 0.99))
                incs = _horizontal_incs(stations, u_sol, td_tvd, td_md, inc_lat)
            else:
                # Fallback: solve for lateral inclination directly if extreme MD/TVD
                u_fixed = 0.45
                def _sim_horiz_inc(deg_val: float) -> float:
                    test_incs = _horizontal_incs(stations, u_fixed, td_tvd, td_md, deg_val)
                    return _integrate_tvd(stations, test_incs, azi_deg) - td_tvd
                inc_sol = float(brentq(_sim_horiz_inc, 45.0, 89.9))
                incs = _horizontal_incs(stations, u_fixed, td_tvd, td_md, inc_sol)
        else:
            # S-shaped directional MBA / RDG pad well profile (build -> hold -> drop)
            kop_choice = float(rng_dev.choice([60.0, 90.0, 120.0, 150.0]))
            kop = min(kop_choice, round(td_md * 0.08, 1))
            default_br = 3.5 if td_md < 900.0 else 2.2
            br = default_br if np.isnan(max_dls) else min(default_br, max(0.5, max_dls - 0.1))

            def _sim_swell(i_deg: float) -> float:
                test_incs = _s_well_incs(stations, kop, br, td_md, i_deg)
                return _integrate_tvd(stations, test_incs, azi_deg) - td_tvd

            i_sol = float(brentq(_sim_swell, 0.1, 82.0))
            incs = _s_well_incs(stations, kop, br, td_md, i_sol)

        cur_tvd = 0.0
        survey_rows.append({
            "well_id": well_id,
            "field": field,
            "cluster_id": cluster_id,
            "md_m": 0.0,
            "inc_deg": 0.0,
            "azi_deg": azi_deg,
            "tvd_m": 0.0,
            "dls_deg_30m": 0.0,
        })

        for i in range(1, len(stations)):
            dt, dls = _min_curv_step(
                stations[i - 1], stations[i],
                incs[i - 1], incs[i],
                azi_deg, azi_deg,
            )
            cur_tvd += dt
            # TVD is monotonic non-decreasing and bounded by MD
            tvd_val = min(round(cur_tvd, 2), round(stations[i], 2))
            survey_rows.append({
                "well_id": well_id,
                "field": field,
                "cluster_id": cluster_id,
                "md_m": round(float(stations[i]), 2),
                "inc_deg": round(float(incs[i]), 2),
                "azi_deg": azi_deg,
                "tvd_m": tvd_val,
                "dls_deg_30m": round(float(dls), 2),
            })

    df_survey = pd.DataFrame(survey_rows)
    if df_survey.empty:
        df_survey = pd.DataFrame(columns=[
            "well_id", "field", "cluster_id", "md_m", "inc_deg", "azi_deg",
            "tvd_m", "dls_deg_30m",
        ])

    return {
        "tubing_tally": df_tally,
        "deviation_survey": df_survey,
    }
