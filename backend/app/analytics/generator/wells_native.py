"""Native well_master generator for Cairn Oil & Gas — Barmer Basin (same 24 columns as v0.4 contract).

Wells are placed around their pad cluster centre and rejection-sampled inside the field
boundary polygon (V-N1). Fixture wells get their scripted lift type, zone, cluster, and depth profile.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from .fields.base import FieldConfig
from .geometry import boundary_polygon, point_in_polygon

DEFAULT_ZONE_DEPTH_MD: dict[str, tuple[float, float, float, float]] = {
    "Fatehgarh_Upper": (890.0, 75.0, 760.0, 1020.0),
    "Fatehgarh_Lower": (1110.0, 110.0, 920.0, 1320.0),
    "Barmer_Hill": (830.0, 60.0, 720.0, 940.0),
    "Raageshwari_Volcanics": (3320.0, 190.0, 2950.0, 3720.0),
}

DEFAULT_ZONE_MD_TVD_RATIO: dict[str, tuple[float, float]] = {
    "Fatehgarh_Upper": (1.12, 1.25),
    "Fatehgarh_Lower": (1.12, 1.25),
    "Barmer_Hill": (1.15, 1.28),
    "Raageshwari_Volcanics": (1.07, 1.14),
}

# Pinned hero-well depth & completion profiles from docs/build.md Part I §7
HERO_WELL_PROFILES: dict[str, dict[str, object]] = {
    "MNG-042": {
        "perf_top_m": 1020.0,
        "perf_bottom_m": 1055.0,
        "total_depth_md_m": 1085.0,
        "total_depth_tvd_m": 885.0,
        "completion_date": date(2014, 6, 15),
        "spud_date": date(2014, 5, 10),
    },
    "BHG-019": {
        "perf_top_m": 535.0,
        "perf_bottom_m": 560.0,
        "total_depth_md_m": 585.0,
        "total_depth_tvd_m": 495.0,
    },
    "BHG-088": {
        "perf_top_m": 605.0,
        "perf_bottom_m": 635.0,
        "total_depth_md_m": 660.0,
        "total_depth_tvd_m": 550.0,
    },
    "ASH-023": {
        "perf_top_m": 1175.0,
        "perf_bottom_m": 1210.0,
        "total_depth_md_m": 1240.0,
        "total_depth_tvd_m": 1050.0,
    },
    "ASH-061": {
        "perf_top_m": 1370.0,
        "perf_bottom_m": 1408.0,
        "total_depth_md_m": 1440.0,
        "total_depth_tvd_m": 1220.0,
    },
    "RAG-014": {
        "perf_top_m": 3180.0,
        "perf_bottom_m": 3235.0,
        "total_depth_md_m": 3280.0,
        "total_depth_tvd_m": 3040.0,
    },
}

PUMPED_LIFTS = {"SRP", "ESP", "JET_PUMP", "PCP"}


def generate_native_well_master(cfg: FieldConfig) -> pd.DataFrame:
    rng = np.random.default_rng([cfg.seed, 1])
    n = cfg.n_wells
    well_ids = [f"{cfg.prefix}{i + 1:03d}" for i in range(n)]
    poly = boundary_polygon(cfg)

    cl_ids = [c.cluster_id for c in cfg.clusters]
    cl_w = np.array([c.weight for c in cfg.clusters], dtype=float)
    cluster_of = list(rng.choice(cl_ids, size=n, p=cl_w / cl_w.sum()))
    for fx in cfg.fixtures.values():
        if fx.cluster_id and fx.well_id in well_ids:
            cluster_of[well_ids.index(fx.well_id)] = fx.cluster_id
    cl_by_id = {c.cluster_id: c for c in cfg.clusters}

    zones_k = list(cfg.zones)
    zones_p = np.array([cfg.zones[z] for z in zones_k], dtype=float)
    zones = list(rng.choice(zones_k, size=n, p=zones_p / zones_p.sum()))

    lifts_k = list(cfg.lift_mix)
    lifts_p = np.array([cfg.lift_mix[k] for k in lifts_k], dtype=float)
    lifts = list(rng.choice(lifts_k, size=n, p=lifts_p / lifts_p.sum()))

    fixture_ids = set(cfg.fixtures)
    # Align Aishwariya ASH-ABH-3 tight pad with horizontal Barmer_Hill zone
    if "ASH-ABH-3" in cl_by_id and "Barmer_Hill" in cfg.zones:
        af_zones = [z for z in zones_k if z != "Barmer_Hill"]
        af_p = np.array([cfg.zones[z] for z in af_zones], dtype=float)
        af_p = af_p / af_p.sum() if len(af_zones) else np.array([1.0])
        for idx in range(n):
            if well_ids[idx] in fixture_ids:
                continue
            if cluster_of[idx] == "ASH-ABH-3":
                zones[idx] = "Barmer_Hill"
            elif zones[idx] == "Barmer_Hill" and len(af_zones):
                zones[idx] = str(rng.choice(af_zones, p=af_p))

    for fx in cfg.fixtures.values():
        if fx.well_id in well_ids:
            i = well_ids.index(fx.well_id)
            lifts[i] = fx.lift_type
            if fx.zone:
                zones[i] = fx.zone

    lats, lons = [], []
    for cid in cluster_of:
        c = cl_by_id[cid]
        for _ in range(200):
            lat = c.center[0] + rng.normal(0, c.spread_deg)
            lon = c.center[1] + rng.normal(0, c.spread_deg)
            if point_in_polygon(lat, lon, poly):
                break
        lats.append(round(float(lat), 6))
        lons.append(round(float(lon), 6))

    start_c, end_c = cfg.completion_window
    total_days = max(1, (end_c - start_c).days)
    completion = [start_c + timedelta(days=int(b * total_days)) for b in rng.beta(2.2, 4.0, size=n)]
    spud_lo, spud_hi = cfg.spud_lead_days
    spud = [c - timedelta(days=int(rng.integers(spud_lo, spud_hi + 1))) for c in completion]

    perf_top, perf_bot, td_md, td_tvd = [], [], [], []
    for i, z in enumerate(zones):
        wid = well_ids[i]
        mu, sd, lo, hi = cfg.zone_depths_md.get(
            z, DEFAULT_ZONE_DEPTH_MD.get(z, (1000.0, 100.0, 800.0, 1250.0))
        )
        ratio_lo, ratio_hi = cfg.zone_md_tvd_ratio.get(
            z, DEFAULT_ZONE_MD_TVD_RATIO.get(z, (1.12, 1.25))
        )
        if hi <= 850.0:
            # Shallow reservoir (e.g. Bhagyam): keep MD within [lo, hi] and TVD strictly < 700 m
            top_hi = max(lo + 10.0, hi - 45.0)
            top = round(float(np.clip(rng.normal(mu, sd), lo, top_hi)), 1)
            bot = round(top + float(rng.uniform(10.0, 24.0)), 1)
            md = round(min(hi, bot + float(rng.uniform(12.0, 24.0))), 1)
            ratio = float(rng.uniform(ratio_lo, ratio_hi))
            tvd = round(min(665.0, md / ratio), 1)
        elif ratio_lo >= 1.75:
            # Horizontal / high-angle lateral (e.g. Aishwariya Barmer_Hill ASH-ABH-3)
            top_hi = max(lo + 30.0, hi - 70.0)
            top = round(float(np.clip(rng.normal(mu, sd), lo, top_hi)), 1)
            bot = round(top + float(rng.uniform(18.0, 42.0)), 1)
            md = round(min(hi, bot + float(rng.uniform(15.0, 35.0))), 1)
            ratio = float(rng.uniform(ratio_lo, ratio_hi))
            tvd = round(float(np.clip(md / ratio, 950.0, 1220.0)), 1)
        else:
            top_hi = max(lo + 25.0, hi - 75.0)
            top = round(float(np.clip(rng.normal(mu, sd), lo, top_hi)), 1)
            bot = round(top + float(rng.uniform(14.0, 45.0)), 1)
            md = round(min(hi, bot + float(rng.uniform(15.0, 45.0))), 1)
            ratio = float(rng.uniform(ratio_lo, ratio_hi))
            tvd = round(md / ratio, 1)

        if wid in HERO_WELL_PROFILES:
            hp = HERO_WELL_PROFILES[wid]
            top = float(hp["perf_top_m"])
            bot = float(hp["perf_bottom_m"])
            md = float(hp["total_depth_md_m"])
            tvd = float(hp["total_depth_tvd_m"])
            if "completion_date" in hp:
                completion[i] = hp["completion_date"]
            if "spud_date" in hp:
                spud[i] = hp["spud_date"]

        perf_top.append(top)
        perf_bot.append(bot)
        td_md.append(md)
        td_tvd.append(tvd)

    psd, plunger, stroke, rod, ptype, vented = [], [], [], [], [], []
    for i, lt in enumerate(lifts):
        if lt in PUMPED_LIFTS:
            d = round(max(180.0, float(perf_top[i] - rng.uniform(30.0, 110.0))), 1)
            psd.append(d)
            if lt == "SRP":
                p = float(rng.choice([1.25, 1.50])) if d > 2000.0 else float(rng.choice([1.50, 1.75, 2.00]))
                plunger.append(p)
                stroke.append(float(rng.choice([64.0, 74.0, 86.0, 100.0])))
                rod.append(str(rng.choice(["C", "D", "K"], p=[0.20, 0.50, 0.30])))
                ptype.append(str(rng.choice(["INSERT", "TUBING"], p=[0.75, 0.25])))
                v = bool(rng.choice([False, True], p=[0.88, 0.12]))
                vented.append(False if well_ids[i] in fixture_ids else v)
            else:
                plunger.append(None)
                stroke.append(None)
                rod.append(None)
                ptype.append(None)
                vented.append(False)
        else:
            psd.append(None)
            plunger.append(None)
            stroke.append(None)
            rod.append(None)
            ptype.append(None)
            vented.append(False)

    tub_keys = list(cfg.tubing_mix_in) if cfg.tubing_mix_in else [3.5, 2.875]
    tub_w = np.array([cfg.tubing_mix_in[k] for k in tub_keys], dtype=float) if cfg.tubing_mix_in else np.array([0.85, 0.15])
    tubing = [float(x) for x in rng.choice(tub_keys, size=n, p=tub_w / tub_w.sum())]

    cas_keys = list(cfg.casing_mix_in) if cfg.casing_mix_in else [7.0, 9.625]
    cas_w = np.array([cfg.casing_mix_in[k] for k in cas_keys], dtype=float) if cfg.casing_mix_in else np.array([0.70, 0.30])
    casing = [float(x) for x in rng.choice(cas_keys, size=n, p=cas_w / cas_w.sum())]

    for i in range(n):
        if cluster_of[i] == "ASH-ABH-3" or (cfg.field == "Aishwariya" and zones[i] == "Barmer_Hill"):
            casing[i] = 5.5
            tubing[i] = 2.875

    n_idle = int(round(cfg.idle_fraction * n))
    candidates = [i for i, w in enumerate(well_ids) if w not in fixture_ids]
    idle = set(int(i) for i in rng.choice(candidates, size=n_idle, replace=False))

    return pd.DataFrame({
        "well_id": well_ids,
        "field": cfg.field,
        "asset": cfg.asset,
        "latitude": lats,
        "longitude": lons,
        "spud_date": spud,
        "completion_date": completion,
        "current_zone": zones,
        "perf_top_m": perf_top,
        "perf_bottom_m": perf_bot,
        "total_depth_md_m": td_md,
        "total_depth_tvd_m": td_tvd,
        "max_dls_deg_30m": [None] * n,
        "lift_type": lifts,
        "plunger_diameter_in": plunger,
        "stroke_length_in": stroke,
        "pump_setting_depth_m": psd,
        "rod_string_grade": rod,
        "pump_type": ptype,
        "casing_vented": vented,
        "tubing_size_in": tubing,
        "casing_size_in": casing,
        "status": ["IDLE" if i in idle else "ACTIVE" for i in range(n)],
        "cluster_id": cluster_of,
    })
