"""C-R9: warm the slow analytics caches in the background so the first voice question is not a 9-20 s pause.

Measured 2026-11-19: compare_fields QTD 20.5 s cold vs 1 ms warm (lru_cache on _field_row); next_best_action
1.1 s cold (model load) vs 0.2 s warm; Cloud Run first answer to "which field is underperforming" waited 10 s.
Runs in a daemon thread at startup, never blocks /api/health or the first request; failures are logged only.
Disable with WELLPULSE_WARM_CACHES=0 (tests).
"""
from __future__ import annotations

import logging
import os
import threading
import time

logger = logging.getLogger("wellpulse.warmup")

_PERIODS = ("QTD", "MTD", "YTD", "L12M")
_FIELDS = ("Mangala", "Bhagyam", "Aishwariya", "Raageshwari")
_HERO_WELLS = ("MNG-042", "BHG-019", "BHG-088", "ASH-023", "ASH-061", "RAG-014")


def _step(label: str, fn) -> None:
    t0 = time.perf_counter()
    try:
        fn()
        logger.info("warmup %s ok in %.0f ms", label, (time.perf_counter() - t0) * 1000)
    except Exception as e:  # noqa: BLE001 - warmup is best-effort
        logger.warning("warmup %s failed: %s: %s", label, type(e).__name__, e)


def warm_caches() -> None:
    from app.analytics.tools.field_performance import compare_fields
    from app.analytics.tools.health import classify_well_health
    from app.analytics.tools.nba import recommend_next_best_action
    from app.analytics.tools.well_profile import well_profile

    t0 = time.perf_counter()
    for p in _PERIODS:
        _step(f"compare_fields {p}", lambda p=p: compare_fields(period=p))
    for f in _FIELDS:
        _step(f"classify_well_health {f}", lambda f=f: classify_well_health(f))
    for w in _HERO_WELLS:
        _step(f"next_best_action {w}", lambda w=w: recommend_next_best_action(w, top_k=3))
        _step(f"well_profile {w}", lambda w=w: well_profile(w))
    print(f"[✓] Analytics caches warmed in {time.perf_counter() - t0:.1f}s (voice answers no longer wait on cold caches)")


def start_background_warmup() -> threading.Thread | None:
    if os.getenv("WELLPULSE_WARM_CACHES", "1") == "0":
        return None
    th = threading.Thread(target=warm_caches, name="cache-warmup", daemon=True)
    th.start()
    return th
