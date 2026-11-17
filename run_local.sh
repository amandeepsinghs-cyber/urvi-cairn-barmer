#!/usr/bin/env bash
# ==============================================================================
# Urvi Cairn Barmer: Local Platform Launcher
# Boots FastAPI Backend (port 8002) and React+Vite Frontend (port 5180)
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

echo "======================================================================"
echo "     Urvi AI Agent — Cairn Oil & Gas (Barmer Basin RJ-ON-90/1)        "
echo "======================================================================"

# 1. Check prerequisites (uv only for Python, npm only for the frontend: D-14)
command -v uv >/dev/null 2>&1 || { echo "[!] Error: uv is required (https://docs.astral.sh/uv/)."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "[!] Error: node is required."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "[!] Error: npm is required."; exit 1; }

# 2. Sync backend environment from the lockfile (creates backend/.venv if needed)
echo "[*] Syncing backend environment with uv (uv.lock)..."
(cd "${BACKEND_DIR}" && uv sync --frozen)

# 3. Ensure the Barmer landing dataset exists (committed; regenerate only if missing, D-18)
if [ ! -f "${BACKEND_DIR}/app/data/landing/asset/field_targets.parquet" ]; then
    echo "[*] Generating synthetic landing data (Mangala, Bhagyam, Aishwariya, Raageshwari; 2021-10-01..2026-09-30)..."
    (cd "${BACKEND_DIR}" && uv run python -m app.analytics.generator.generate --field all --start 2021-10-01 --end 2026-09-30)
fi

# 3b. Ensure the synthetic PDF corpus + search index exist (git-ignored, ~3 min; Stage O, D-18)
if [ ! -f "${BACKEND_DIR}/app/data/index/corpus_manifest.json" ]; then
    echo "[*] Building synthetic document corpus (D1..D11 + SOPs) and search index..."
    (cd "${BACKEND_DIR}" && uv run python -m app.analytics.docs_pdf.build)
fi

# 4. Check Frontend dependencies
if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
    echo "[*] Installing frontend npm dependencies..."
    (cd "${FRONTEND_DIR}" && npm install)
fi

# 5. Clean up any existing background tasks on exit
cleanup() {
    echo ""
    echo "[*] Shutting down Urvi Cairn Barmer services..."
    if [ -n "${BACKEND_PID}" ]; then
        kill "${BACKEND_PID}" 2>/dev/null || true
    fi
    if [ -n "${FRONTEND_PID}" ]; then
        kill "${FRONTEND_PID}" 2>/dev/null || true
    fi
    echo "[✓] All Urvi Cairn Barmer services terminated."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 6. Launch Backend
echo "[*] Starting FastAPI Backend on http://localhost:8002..."
(cd "${BACKEND_DIR}" && exec uv run --frozen python run.py) &
BACKEND_PID=$!

# Wait for backend health + 460-well fleet readiness before launching Vite
echo "[*] Waiting for backend to load 460 Barmer wells..."
BACKEND_READY=0
for i in {1..60}; do
    if ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
        echo "[!] Backend exited unexpectedly during startup."
        exit 1
    fi
    if curl -sf http://127.0.0.1:8002/api/wells/kpis >/dev/null 2>&1; then
        echo "[✓] Backend is healthy and 460 Barmer wells are ready!"
        BACKEND_READY=1
        break
    fi
    sleep 0.5
done
if [ "${BACKEND_READY}" -ne 1 ]; then
    echo "[!] Backend did not become ready within 30s."
    exit 1
fi

# 7. Launch Frontend
echo "[*] Starting React + Vite Frontend on http://localhost:5180 (dual-stack IPv6/IPv4)..."
(cd "${FRONTEND_DIR}" && npm run dev -- --host "::" --port 5180) &
FRONTEND_PID=$!

echo "======================================================================"
echo "[✓] Urvi Cairn Barmer is live and running!"
echo "    • Operations Dashboard: http://localhost:5180"
echo "    • Backend API / Docs:   http://localhost:8002/docs"
echo "======================================================================"
echo "Press Ctrl+C to stop all services."

wait
