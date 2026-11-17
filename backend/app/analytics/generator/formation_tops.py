"""Formation tops generator for Barmer Basin subsurface stratigraphic layering.

Generates continuous, non-overlapping stratigraphic columns from the 7-unit
Barmer Basin lithostratigraphic sequence (docs/build.md Part I §2).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

LITHOLOGY_MAP: dict[str, str] = {
    "Thar_Alluvium_Kapurdi": "Quaternary aeolian Thar dune sand, calcrete and Eocene Kapurdi fuller's earth clay",
    "Akli_Thumbli": "Palaeocene-Eocene lignite-bearing carbonaceous shale and friable Thumbli sandstone",
    "Dharvi_Dungar": "Palaeocene lacustrine grey claystone and regional top-seal shale",
    "Barmer_Hill": "Palaeocene lacustrine siliceous porcellanite, diatomite and laminated mudstone",
    "Fatehgarh_Upper": "Upper Fatehgarh (FM1-FM2) sinuous meandering fluvial channel sandstone and siltstone",
    "Fatehgarh_Lower": "Lower Fatehgarh (FM3-FM5) stacked multi-storey braided channel and sheetflood sandstone",
    "Raageshwari_Volcanics": "Late Cretaceous Prithvi basaltic lava flows and Agni felsic pyroclastics",
}

FORMATION_ORDER: tuple[str, ...] = (
    "Thar_Alluvium_Kapurdi",
    "Akli_Thumbli",
    "Dharvi_Dungar",
    "Barmer_Hill",
    "Fatehgarh_Upper",
    "Fatehgarh_Lower",
    "Raageshwari_Volcanics",
)

NOMINAL_THICKNESS_RANGES: dict[str, tuple[float, float]] = {
    "Thar_Alluvium_Kapurdi": (45.0, 115.0),
    "Akli_Thumbli": (95.0, 260.0),
    "Dharvi_Dungar": (85.0, 250.0),
    "Barmer_Hill": (65.0, 190.0),
    "Fatehgarh_Upper": (75.0, 175.0),
    "Fatehgarh_Lower": (115.0, 260.0),
    "Raageshwari_Volcanics": (150.0, 500.0),
}

MIN_LAYER_THICKNESS_M = 18.0


def generate_formation_tops(wells: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Generate formation tops table for given wells.

    Columns:
        well_id, field, cluster_id, formation, top_md_m, bottom_md_m, lithology
    """
    rng = np.random.default_rng(seed)
    columns = [
        "well_id",
        "field",
        "cluster_id",
        "formation",
        "top_md_m",
        "bottom_md_m",
        "lithology",
    ]
    if wells.empty:
        return pd.DataFrame(columns=columns)

    records = []
    for _, row in wells.iterrows():
        wid = row["well_id"]
        fld = row["field"]
        cid = row["cluster_id"]
        current_zone = str(row["current_zone"])
        perf_top_m = float(row["perf_top_m"])
        perf_bottom_m = float(row["perf_bottom_m"])
        td_md_m = float(row["total_depth_md_m"])
        td_rounded = round(td_md_m, 1)

        # Draw nominal thicknesses in fixed order per well for deterministic RNG stream
        drawn_weights = [
            float(rng.uniform(*NOMINAL_THICKNESS_RANGES[f])) for f in FORMATION_ORDER
        ]
        offset = float(rng.uniform(12.0, 42.0))

        forms = list(FORMATION_ORDER)
        if current_zone in forms:
            z_idx = forms.index(current_zone)
        else:
            z_idx = 4
            forms[z_idx] = current_zone

        n_above = z_idx
        min_overburden = round(n_above * MIN_LAYER_THICKNESS_M, 1)
        max_offset = max(6.0, min(offset, perf_top_m - min_overburden))
        z_top = round(max(min_overburden, perf_top_m - max_offset), 1)

        # Partition [0.0, z_top] across the n_above overburden units with >= MIN_LAYER_THICKNESS_M each
        over_weights = np.array(drawn_weights[:n_above], dtype=float)
        over_weights = over_weights / over_weights.sum()
        rem_above = max(0.0, z_top - n_above * MIN_LAYER_THICKNESS_M)
        raw_thicks = MIN_LAYER_THICKNESS_M + rem_above * over_weights

        boundaries = [0.0]
        acc = 0.0
        for k in range(n_above - 1):
            acc += float(raw_thicks[k])
            b_k = round(acc, 1)
            # Enforce strict >= 15.0m thickness and leave room for remaining overburden layers
            min_b = round(boundaries[-1] + MIN_LAYER_THICKNESS_M, 1)
            max_b = round(z_top - (n_above - 1 - k) * MIN_LAYER_THICKNESS_M, 1)
            b_k = max(min_b, min(max_b, b_k))
            boundaries.append(b_k)
        boundaries.append(z_top)

        kept: list[tuple[str, float, float]] = []
        for k in range(n_above):
            kept.append((forms[k], boundaries[k], boundaries[k + 1]))

        # Target producing zone must strictly contain [perf_top_m, perf_bottom_m]
        rem_below_perf = round(td_rounded - perf_bottom_m, 1)
        if z_idx < len(forms) - 1 and rem_below_perf >= 28.0:
            pad_below = round(float(rng.uniform(6.0, max(7.0, rem_below_perf - MIN_LAYER_THICKNESS_M))), 1)
            z_bot = round(perf_bottom_m + pad_below, 1)
            if td_rounded - z_bot >= 16.0:
                kept.append((forms[z_idx], z_top, z_bot))
                kept.append((forms[z_idx + 1], z_bot, td_rounded))
            else:
                kept.append((forms[z_idx], z_top, td_rounded))
        else:
            kept.append((forms[z_idx], z_top, td_rounded))

        for form_name, top_m, bot_m in kept:
            records.append({
                "well_id": wid,
                "field": fld,
                "cluster_id": cid,
                "formation": form_name,
                "top_md_m": round(float(top_m), 1),
                "bottom_md_m": round(float(bot_m), 1),
                "lithology": LITHOLOGY_MAP.get(form_name, "Fluvial sandstone and claystone sequence"),
            })

    return pd.DataFrame(records, columns=columns)
