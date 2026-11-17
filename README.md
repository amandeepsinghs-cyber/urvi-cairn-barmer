> [!IMPORTANT]
> **This repository is the Cairn / Vedanta Oil and Gas (Barmer Basin) replica of the ONGC WellPulse / Urvi demo.**
> Created 2026-11-15 from the ONGC repo at commit `c8fc208` (V 1.1), with full git history so the two can be merged later
> if ever needed. **It must never touch the ONGC demo:** the GitHub remote is `amandeepsinghs-cyber/urvi-cairn-barmer`,
> every Google Cloud target is a Cairn placeholder (`urvi-cairn-barmer-ai-agent`, service `urvi-cairn-app`, datasets
> `urvi_cairn_*`), and `deploy/deploy.sh` refuses to run against the ONGC project / service or while the project is a
> placeholder. Start with [`plan_prompt.md`](./plan_prompt.md) (kickoff prompt) and [`backlog_refinements.md`](./backlog_refinements.md). The documentation below covers the
> Barmer Basin (`RJ-ON-90/1`) Cairn Oil & Gas implementation.

# Urvi AI Agent: Barmer Basin Well Operations & Voice AI Platform
## Barmer Basin (`RJ-ON-90/1`, Rajasthan • Cairn Oil & Gas / Vedanta Limited)

> **Single-Agent, Multi-Tool Hybrid Architecture:** Natural spoken & typed language in (Gemini ADK / Live) → deterministic engineering physics, ML models & numeric-grounding guards underneath — best of both worlds with minimal hallucination.

**Urvi** is an industrial operations intelligence and Voice AI platform tailored for **Cairn Oil & Gas (Vedanta Limited)** across the **Barmer Basin (`RJ-ON-90/1`, Rajasthan)**. It manages **460 synthetic wells** spanning four producing assets — **Mangala (180)**, **Bhagyam (120)**, **Aishwariya (100)**, and **Raageshwari (60)** — across a **60-month window (`2021-10-01` to `2026-09-30`)**.

Built for Barmer's distinct operating physics — high-pour-point waxy crude (**42°C pour point / 59°C WAT**), **HPAM polymer & ASP chemical floods**, **MPT Nagana** (Mangala Processing Terminal) & **RGT** (Raageshwari Gas Terminal) gathering networks, and **6 lift systems** (`JET_PUMP`, `ESP`, `PCP`, `SRP`, `GAS_LIFT`, `NATURAL`) — Urvi pairs high-resolution **Aerial Satellite Mapping** (`MNG-001..180`, `BHG-001..120`, `ASH-001..100`, `RAG-001..060`) with 4-tier operational health screening, 60-month telemetry drilldowns, causal decline attribution, multimodal intervention ranking, and a tool-grounded Voice + Text AI copilot.

---

## Documentation

> Detailed architecture, build gates, and Barmer domain specifications live in [`docs/`](./docs):

| Doc | Purpose |
|---|---|
| [`backlog_refinements.md`](./backlog_refinements.md) | Latest changes, open refinements (`R-n`), and backlog (`BL-n`) |
| [`docs/how_urvi_works.md`](./docs/how_urvi_works.md) | Plain-English walkthrough of the architecture (mirrors the UI Architecture Explain panel) |
| [`docs/ml_recommendation_engine.md`](./docs/ml_recommendation_engine.md) | ML and recommendation engine: classifier, survival trigger, multimodal success engine, and counterfactual scoring |
| [`docs/data_access_plan.md`](./docs/data_access_plan.md) | Cairn Oil & Gas (Vedanta Limited) data sources (AVEVA/OSIsoft PI, SAP S/4HANA, WellView) and India data residency (`asia-south1`) |
| [`docs/v05_change_brief.md`](./docs/v05_change_brief.md) | Answer-canvas, multimodal success scorer, field report, and data-gap closure design brief |
| [`verbatim.md`](./verbatim.md) | Source of truth: verbatim user requirements |
| [`docs/BRD.md`](./docs/BRD.md) | Business requirements, personas, and success metrics |
| [`docs/features.md`](./docs/features.md) | Feature catalogue (`F-01`…`F-26`) |
| [`docs/BDD.md`](./docs/BDD.md) | Gherkin acceptance scenarios |
| [`docs/SDD.md`](./docs/SDD.md) | Software design; authoritative route table and layout |
| [`docs/build.md`](./docs/build.md) | Stage-by-stage Barmer build instructions and verification gates |
| [`docs/checklist.md`](./docs/checklist.md) | Live conversion and verification progress tracker |
| [`docs/DELEGATION.md`](./docs/DELEGATION.md) | Multi-agent task split and fact-slot rules |
| [`docs/EXECUTION_PLAN.md`](./docs/EXECUTION_PLAN.md) | Autonomous execution policy, milestones, and verification rules |
| [`docs/CONSISTENCY_REPORT.md`](./docs/CONSISTENCY_REPORT.md) | Doc-set alignment record |

---

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │      Urvi Web Application (Vite)       │
                      │       React 18 · Tailwind (:5180)      │
                      └───────────────────┬────────────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
        ┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
        │ Satellite GIS Map │   │ 60-Month Curves   │   │  Voice AI Copilot │
        │ (460 Barmer Wells)│   │(Recharts BOPD/psi)│   │ (Gemini Live/ADK) │
        │ 🟢 🟡 🔴 Triage   │   │  Pads, MPT & RGT  │   │ Context Injection │
        └───────────────────┘   └───────────────────┘   └───────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │    FastAPI Backend Server (:8002)      │
                      │  • 460-Well Barmer Synthetic Lakehouse │
                      │  • BigQuery urvi_cairn_{bronze,silver, │
                      │    gold} (asia-south1) + GCS + Parquet │
                      │  • ADK Gemini Agent + ML Scorers       │
                      └────────────────────────────────────────┘
```

- **Cloud Run Service:** `urvi-cairn-app` (`us-central1` for synthetic Gemini Live demo; `asia-south1` Mumbai target for production data)
- **Cloud Storage:** `gs://urvi-cairn-barmer-ai-agent-datalake`
- **BigQuery Lakehouse (`asia-south1`):** `urvi_cairn_bronze`, `urvi_cairn_silver`, `urvi_cairn_gold`

---

## Quickstart (Local Run)

Launch both the backend API server and frontend client with a single command:

```bash
chmod +x run_local.sh
./run_local.sh
```

- **Dashboard UI**: [http://localhost:5180](http://localhost:5180)
- **FastAPI Documentation**: [http://localhost:8002/docs](http://localhost:8002/docs)
- **API Health Check**: [http://localhost:8002/api/health](http://localhost:8002/api/health)

---

## Project Structure

```
urvi_cairn_barmer/
├── docs/                        # Engineering specs, Barmer build plan, data access plan
│   ├── BRD.md                   # Business Requirements Document
│   ├── BDD.md                   # Behavior-Driven Development (Gherkin Scenarios)
│   ├── SDD.md                   # Software Design Document & System Architecture
│   ├── features.md              # Feature Catalog
│   ├── data_access_plan.md      # Cairn/Vedanta India Data Residency Plan (asia-south1)
│   ├── build.md                 # Barmer Basin Build Guide & Gates
│   └── checklist.md             # Phased Delivery & Verification Tracker
├── backend/                     # Python FastAPI Service (:8002)
│   ├── app/
│   │   ├── agent/               # ADK Copilot, RBAC, UI control, number grounding
│   │   ├── analytics/           # 460-well Barmer generator, ML scorers, PDF docs_pdf
│   │   ├── api/                 # REST routers (/api/wells, /api/fields, /api/chat, /api/geo)
│   │   ├── data_access/         # Parquet + BigQuery (urvi_cairn_*) repository adapters
│   │   ├── live/                # Gemini Live bidirectional voice session proxy
│   │   └── data/                # Landing parquets (mangala, bhagyam, aishwariya, raageshwari) & PDFs
│   └── tests/                   # Unit, integration, BDD, golden contracts, and agent evals
├── frontend/                    # React 18 + Vite + Tailwind Client (:5180)
│   ├── public/brand/            # Cairn Oil & Gas / Vedanta brand assets
│   ├── public/architecture/     # Auto-generated Current & Target architecture SVGs + narrative
│   └── src/
│       ├── agent/               # Voice/text UI command bus (uiCommands.ts)
│       ├── components/map/      # Leaflet GIS Map (India blocks + Barmer Basin drill-down)
│       ├── components/decision/ # Health buckets, priority queue, SHAP attribution, NBA
│       ├── components/well/     # Wellbore diagram, offset decline, printable Field Report
│       └── components/agent/    # Voice + Text Copilot with waveform, TTS, and artifact cards
├── deploy/                      # Cloud Run deployment, BigQuery DDL, smoke tests
├── run_local.sh                 # Unified local startup script
└── README.md                    # Landing documentation
```

---

## Core Capabilities

1. **Geospatial Health Prioritization & Barmer Asset Topology**:
   - **India Block Overview → Barmer Basin Drill-Down**: Displays Cairn/Vedanta India blocks (`Barmer`, `Ravva`, `Cambay`, `Jorhat`) with live drill-down into `RJ-ON-90/1` pads (`MNG-PAD-*`, `BHG-PAD-*`, `ASH-PAD-*`, `ASH-ABH-3`, `RAG-RDG-*`, `RAG-OIL-1`) and central facilities (`MPT-NAGANA`, `BHG-CPF`, `ASH-CPF`, `RGT-TERMINAL`).
   - 🟢 **Healthy / Optimal**, 🟡 **Needs Attention** (wax deposition, lift wear, HPAM polymer channelling, sand influx), 🔴 **Not Producing** (failed lift/heater/feeder trips).
2. **60-Month Multi-Field Telemetry (`2021-10-01`..`2026-09-30`)**:
   - Daily time series across **460 synthetic wells** in **Fatehgarh Lower**, **Fatehgarh Upper**, **Barmer Hill**, and **Raageshwari Volcanics** formations.
   - Tracks Oil (BOPD), Gas (MCFD), Water Cut (%), Wellhead & Tubing/Casing Pressures, Wellhead Temperature (critical for `42°C` pour-point / `59°C` WAT waxy crude monitoring), and Lift Telemetry across all **6 lift types** (`JET_PUMP`, `ESP`, `PCP`, `SRP`, `GAS_LIFT`, `NATURAL`).
3. **Chronological Workover, Integrity & Hazard Records**:
   - Workover logs (`IC-01`..`IC-15`), tubing tallies, minimum-curvature deviation surveys (including `Barmer_Hill` horizontal laterals), wellhead pressure ratings, annular barrier tests (e.g., `RAG-014` safety veto), fluid hazards (`H2S`, `CO2`, wax WAT, HPAM breakthrough), and fishing records.
4. **Question-Driven Answer Canvas & Multimodal Success Engine**:
   - Dynamic middle canvas renders the exact engineering view requested (`overview`, `production`, `interventions`, `wellbore`, `pressures`, `diagnosis`, `recommendation`, `compare`, `nearby`) while keeping conversational answers concise (≤ 3 sentences).
   - Ranks top-3 candidate interventions (`P(success)` calibrated via mechanism classifier + field base rates + `k=5` analog wells, deferred bbl ÷ rig-days, qualitative cost bands `LOW`/`MED`/`HIGH`) alongside counterfactual defenses (`MNG-042`, `BHG-019`, `ASH-023`, `ASH-061`, `RAG-014`).
5. **Printable A4 Field Report & SOP Corpus**:
   - Server-rendered A4 Field Report (`GET /api/wells/{id}/report`) with Cairn Oil & Gas (Vedanta Limited) branding, wellbore schematic, and job program, backed by 14 Barmer-specific SOPs (`IC-01`..`IC-14`) and synthetic well dossiers/CBL scans (`MNG-042` `DOC-CBL-MNG042-2014` / `DOC-SCAN-MNG-042-2019`).
6. **Tool-Grounded Voice & Text AI Copilot**:
   - ADK agent on `gemini-3.8-flash` (Vertex AI ADC) + Gemini Live voice interface (`english`, `hinglish`, `hindi`) with strict number-grounding verification and Vedanta RBAC personas (*COO / CIO*, *Asset Manager — Barmer*, *Production / Well Services Engineer*).

---

### Core API Routes

| Method | Route | Description | Contract |
|---|---|---|---|
| `GET` | `/api/geo/cairn-assets` | Cairn / Vedanta India blocks overview + Barmer live hub | `ED-6` |
| `GET` | `/api/fields/{field}/priority` | Ranked intervention candidates (`Mangala`, `Bhagyam`, `Aishwariya`, `Raageshwari`) | `TC-005` |
| `GET` | `/api/wells/{id}/recommendations?k=3` | Top-3 ranked candidate interventions with calibrated `P(success)`, analogs, and SHAP drivers | `TC-030` |
| `GET` | `/api/wells/{id}/similar` | Look-alike analog wells (`k=5`) on standardised feature space | `TC-031` |
| `GET` | `/api/wells/{id}/report` | Printable A4 HTML field report with wellbore SVG and Cairn branding | `TC-032` |
| `GET` | `/api/wells/{id}/tubing-tally` | Joint-by-joint tubing tally for completion architecture | `TC-033` |
| `GET` | `/api/wells/{id}/deviation` | Directional deviation survey stations (MD, Inc, Azi, TVD) | `TC-033` |
| `GET` | `/api/wells/{id}/integrity` | Barrier tests and wellhead ratings for well integrity review | `TC-033` |

