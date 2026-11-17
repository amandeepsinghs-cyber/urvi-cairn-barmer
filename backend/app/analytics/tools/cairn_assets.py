"""Cairn Oil & Gas (Vedanta Limited) India asset overview for the map (Step C6.2).

Four Indian operating blocks of Cairn Oil & Gas (Vedanta Limited) at approximate public block
centres. Only the Rajasthan Block RJ-ON-90/1 (Barmer Basin: Mangala, Bhagyam, Aishwariya,
Raageshwari) carries live interactive telemetry; the other three blocks carry illustrative
position-only well tags [verify] with no production numbers behind them.
"""
from __future__ import annotations

import math
import random
from functools import lru_cache

SOURCE_NOTE = (
    "Block centres are approximate, from public Cairn Oil & Gas (Vedanta Limited) disclosures. "
    "Well tags outside Rajasthan Block RJ-ON-90/1 (Barmer Basin) are illustrative names and "
    "positions only [verify] — no data behind them."
)

# (asset_id, name, basin, lat, lng, offshore, tag prefix, n_tags, spread_deg)
_ASSETS = [
    ("BARMER", "Rajasthan Block (RJ-ON-90/1 — Barmer Basin)", "Barmer Basin", 25.958, 71.508, False, None, 0, 0.0),
    ("RAVVA", "Ravva (PKGM-1 — KG Offshore)", "Krishna-Godavari", 16.48, 82.18, True, "RV", 18, 0.09),
    ("CAMBAY", "Cambay (CB/OS-2 — Suvali Offshore)", "Cambay", 21.14, 72.62, True, "CB", 14, 0.08),
    ("JORHAT_OALP", "Jorhat OALP (AA-ONHP-2017/1 — North-East)", "North-East OALP", 26.75, 94.22, False, "JRH", 12, 0.10),
]


def _tags(asset_id: str, prefix: str, n: int, lat: float, lng: float, spread: float) -> list[dict]:
    rng = random.Random(f"cairn-{asset_id}")
    out = []
    for i in range(n):
        r = spread * math.sqrt(rng.random())
        a = rng.random() * 2 * math.pi
        out.append({
            "name": f"{prefix}-{rng.randint(1, 299):03d}" if i else f"{prefix}-001",
            "lat": round(lat + r * math.sin(a), 5),
            "lng": round(lng + r * math.cos(a) / max(math.cos(math.radians(lat)), 0.3), 5),
        })
    seen, uniq = set(), []
    for t in out:
        if t["name"] not in seen:
            seen.add(t["name"])
            uniq.append(t)
    return uniq


@lru_cache(maxsize=1)
def cairn_assets() -> dict:
    assets = []
    for aid, name, basin, lat, lng, offshore, prefix, n, spread in _ASSETS:
        live = aid == "BARMER"
        assets.append({
            "asset_id": aid,
            "name": name,
            "basin": basin,
            "lat": lat,
            "lng": lng,
            "offshore": offshore,
            "live": live,
            "fields": ["Mangala", "Bhagyam", "Aishwariya", "Raageshwari"] if live else [],
            "well_tags": [] if live else _tags(aid, prefix, n, lat, lng, spread),
        })
    return {
        "assets": assets,
        "n_assets": len(assets),
        "source_note": SOURCE_NOTE,
        "bbox": {"min_lat": 8.0, "max_lat": 29.5, "min_lng": 68.5, "max_lng": 97.5},
    }
