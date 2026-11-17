"""Build-time artefact self-check and 7-route HTTP/WS smoke check for Urvi Cairn Barmer.

Modes:
1. No arguments (inside Docker build stage from ``/app/backend``):
       python /tmp/selfcheck.py
   Verifies required data/model/geodata artefacts and imports ``app.main``.
2. With ``base_url`` argument (local/remote 7-route smoke test, Step C9.1):
       uv run python ../deploy/selfcheck.py http://127.0.0.1:8002
   Checks:
     1) GET /api/health
     2) GET /api/wells (len == 460)
     3) GET /api/geo/cairn-assets
     4) GET /api/fields/compare
     5) GET /api/wells/MNG-042/recommendations
     6) GET /api/wells/MNG-042/report ("Cairn" in HTML, no "ONGC")
     7) WS  /ws/live handshake
"""
from __future__ import annotations

import asyncio
import json
import ssl
import sys
import urllib.request
from pathlib import Path

ROOT = Path("app")
REQUIRED = [
    "data/landing/asset/field_targets.parquet",
    "data/index/corpus_manifest.json",
    "data/index/document_index.parquet",
    "data/index/doc_chunks.parquet",
    "data/index/tfidf.pkl",
    "analytics/model/coxph_srp_v1.pkl",
    "analytics/model/intervention_classifier_v1.pkl",
    "analytics/config/triggers.yaml",
    "data/geodata/mangala_boundary.geojson",
    "data/geodata/bhagyam_boundary.geojson",
    "data/geodata/aishwariya_boundary.geojson",
    "data/geodata/raageshwari_boundary.geojson",
]


def _http_get(url: str, timeout: float = 30.0) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "urvi-cairn-selfcheck/1.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


async def _ws_check(base: str, timeout: float = 20.0) -> bool:
    import websockets

    ws_url = base.replace("https://", "wss://", 1).replace("http://", "ws://", 1) + "/ws/live?language=english&screen=smoke"
    async with websockets.connect(ws_url, open_timeout=timeout, max_size=None) as ws:
        for _ in range(6):
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            if isinstance(raw, bytes):
                continue
            msg = json.loads(raw)
            if msg.get("type") == "status" and msg.get("status") in ("connecting", "connected", "fallback"):
                return True
    return False


def run_http_selfcheck(base_url: str) -> int:
    import time
    import urllib.error

    base = base_url.rstrip("/")
    checks: list[tuple[str, bool, str]] = []

    # 1. /api/health (wait up to 25s for uvicorn cold startup)
    st, body = 0, ""
    for _ in range(25):
        try:
            st, body = _http_get(f"{base}/api/health", timeout=5.0)
            if st == 200:
                break
        except (urllib.error.URLError, OSError):
            time.sleep(1.0)
    checks.append(("GET /api/health", st == 200, f"HTTP {st}"))

    # 2. /api/wells == 460
    st, body = _http_get(f"{base}/api/wells")
    wells = json.loads(body) if st == 200 else []
    checks.append(("GET /api/wells == 460", st == 200 and len(wells) == 460, f"len={len(wells)}"))

    # 3. /api/geo/cairn-assets
    st, body = _http_get(f"{base}/api/geo/cairn-assets")
    checks.append(
        (
            "GET /api/geo/cairn-assets",
            st == 200 and "Barmer" in body and "ONGC" not in body,
            f"HTTP {st}",
        )
    )

    # 4. /api/fields/compare
    st, body = _http_get(f"{base}/api/fields/compare")
    comp = json.loads(body) if st == 200 else {}
    checks.append(
        (
            "GET /api/fields/compare",
            st == 200 and comp.get("status") == "OK",
            f"status={comp.get('status')}",
        )
    )

    # 5. /api/wells/MNG-042/recommendations
    st, body = _http_get(f"{base}/api/wells/MNG-042/recommendations")
    rec = json.loads(body) if st == 200 else {}
    inner = rec.get("data", {}) if isinstance(rec.get("data"), dict) else {}
    cands = (
        rec.get("recommendations")
        or rec.get("candidates")
        or inner.get("recommendations")
        or inner.get("candidates")
        or []
    )
    checks.append(
        (
            "GET /api/wells/MNG-042/recommendations",
            st == 200 and len(cands) >= 1,
            f"candidates={len(cands)}",
        )
    )

    # 6. /api/wells/MNG-042/report
    st, body = _http_get(f"{base}/api/wells/MNG-042/report")
    checks.append(
        (
            "GET /api/wells/MNG-042/report",
            st == 200 and "Cairn" in body and "ONGC" not in body,
            f"HTTP {st}, len={len(body)}",
        )
    )

    # 7. WS /ws/live
    try:
        ws_ok = asyncio.run(_ws_check(base))
        checks.append(("WS /ws/live", ws_ok, "handshake OK" if ws_ok else "no status frame"))
    except Exception as exc:  # noqa: BLE001
        checks.append(("WS /ws/live", False, f"{type(exc).__name__}: {exc}"))

    failed = 0
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        if not ok:
            failed += 1
    print(f"[selfcheck] {len(checks) - failed}/{len(checks)} HTTP/WS checks passed")
    return 1 if failed else 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1].startswith(("http://", "https://")):
        return run_http_selfcheck(sys.argv[1])

    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    n_parquet = len(list((ROOT / "data/landing").rglob("*.parquet")))
    n_pdf = len(list((ROOT / "data/docs_pdf").rglob("*.pdf")))
    print(f"[selfcheck] landing parquet={n_parquet} pdfs={n_pdf} missing={missing}")
    if missing or n_parquet == 0 or n_pdf == 0:
        print("[selfcheck] FAILED: data/model artefacts missing", file=sys.stderr)
        return 1
    sys.path.insert(0, ".")
    import app.main  # noqa: F401  (import smoke; no network: data is local parquet)

    print("[selfcheck] app.main imports OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
