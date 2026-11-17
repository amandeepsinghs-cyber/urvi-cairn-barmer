# Urvi · Cairn / Vedanta Oil and Gas (Barmer Basin): Backlog & Refinements

**This is the reference sheet for the Cairn replica.** It has two working lists, **Current refinements** and
**Feature backlog**; every item gets full clarity with the user before anything is built.

**Origin:** replica of the ONGC WellPulse / Urvi demo, cloned 2026-11-15 at commit `c8fc208` (V 1.1) with history.
The ONGC backlog and decisions remain in git history (`git show c8fc208:backlog_refinements.md`).
**Deployment:** Live on Cloud Run (`urvi-cairn-app`, revision `urvi-cairn-app-00003-cqg` in `us-central1`, project `urvi-cairn-barmer-ai-agent` — see [`APP_LINK.md`](./APP_LINK.md)).

> [!IMPORTANT]
> **Answer first:** **All 67 build steps (`Gates C0–C9`, `134 / 134` `Impl`+`Verify` checks) complete, deployed on Cloud Run (`urvi-cairn-app-00003-cqg`), and pushed to `origin/main`.** All 460 Barmer Basin synthetic wells, 24 Stage-DG tables, 20,277 PDFs (`100.00%` fact-slot verified), GCS datalake + BigQuery Medallion (`asia-south1`, `29/29` checksum parity, `9/9` Gold assertions), retrained ML models (**Gate Q Macro-F1 `0.7683`**, **Gate E C-index `0.6587`**), Cairn/Vedanta branding & prompts, Indian English (`en-IN`) Gemini Live voice (`C6.7`), top-line **Single-Agent, Multi-Tool Hybrid Architecture** banner (`C7.7`), visual interventions parity (`C7.8`), `807 passed` `pytest` suite (`0` ONGC leaks), CIO demo script (`docs/demo_flow.md`), and live Cloud Run + local smoke checks are verified green.

---

## 1. Latest changes (newest first)

| Date | Change | Files | Commit |
|---|---|---|---|
| 2026-11-17 | **Step `C9.6` (`C-R6`) 1-Click Cloud Run Access (`--no-invoker-iam-check`) + Repo `weblink`:** Enabled Argolis-compliant `--no-invoker-iam-check` on `urvi-cairn-app` (`max-instances=1`, zero org-policy overrides; unauthenticated `smoke_test.py` `6/6` PASS incl. `/ws/live`), persisted in `deploy/deploy.sh`, and added `[weblink](https://urvi-cairn-app-498143636903.us-central1.run.app)` in `README.md` + `weblink.url` + `APP_LINK.md`. | `README.md`, `weblink.url`, `APP_LINK.md`, `deploy/deploy.sh`, `docs/` | pushed to `origin/main` |
| 2026-11-15 | **Step `C7.8` (`C-R5`) Visual Interventions Parity + Cloud Run `v10-barmer-rc2`/`rc3`:** Fixed local startup proxy race (`run.py` `0.0.0.0:8002`, `vite.config.ts` `127.0.0.1:8002`, `run_local.sh` `/api/wells/kpis` gate, `App.tsx` mount retry), fixed Live voice `/ws/live` well panel navigation (`voice_tools.well_summary` `well_id` + `recent_interventions`, `VoiceAgentPanel.tsx` transcript-arrival view upgrade to `interventions`, `live_prompt.md` `view=interventions`), added `Interventions Summary` (`View all N →`) + `ProductionMarkersChart` on `Overview` & `5y` `Interventions` with `strokeWidth={2}` staggered pill badges + earlier-workover pills, and enabled cyan `MPT/CPF/RGT` facility icons on `WellMap.tsx`. Verified locally (`7/7` `selfcheck.py`, `17 passed` live/UI tests) and rolling `v10-barmer-rc3` to Cloud Run. | `backend/run.py`, `run_local.sh`, `backend/app/live/`, `frontend/src/` | awaiting `[USER GATE]` `C9.5` |
| 2026-11-15 | **Stages `C1`–`C8` + `C9.1`–`C9.2` + `C7.7` Built & Verified (`62 / 65` steps `[x]`):** Generated 460 Barmer wells (`Mangala 180`, `Bhagyam 120`, `Aishwariya 100`, `Raageshwari 60`; `0` validator violations), 24 Stage-DG parquets (`146` DG tests passed), 20,277 Cairn Barmer PDFs (`100.00%` fact-slot audit), synced GCS `gs://urvi-cairn-barmer-ai-agent-datalake` & BigQuery `urvi_cairn_{bronze,silver,gold}` in `asia-south1` (`29/29` Silver parity, `9/9` Dataform Gold assertions), retrained `ic-hgb-v1` (**Gate Q PASSED:** Macro-F1 `0.7683`, Top-3 `0.9483`, ECE `0.0238`) and `coxph-v1.0-barmer` (**Gate E PASSED:** C-index `0.6587 > 0.6585`), rebuilt `analog_index.parquet` (`3,639` jobs), rebranded backend/frontend/map/voice/RBAC/A4 report, added **Single-Agent, Multi-Tool Hybrid Architecture** top-line banner (`Step C7.7`), updated all docs & CIO demo script (`docs/demo_flow.md`), passed full `pytest` + strict zero-ONGC audit (`Gate C8`), and passed 7/7 local `selfcheck.py` + 6/6 `smoke_test.py` (`WS /ws/live` connected). Paused at `[USER GATE]` `C9.3` (Cloud Run deploy) & `C9.5` (git commit/push). | `backend/`, `frontend/`, `lakehouse/`, `deploy/`, `docs/` | awaiting `[USER GATE]` `C9.5` |
| 2026-11-15 | **Gate C0 Passed + `C4.1` Bucket/Datasets Provisioned:** Pushed lockdown + `build.md`/`checklist.md` commit `9d52f3d` to `amandeepsinghs-cyber/urvi-cairn-barmer`; enabled `run`, `cloudbuild`, `artifactregistry`, `aiplatform`, and `iam` APIs in `urvi-cairn-barmer-ai-agent`; created `gs://urvi-cairn-barmer-ai-agent-datalake` (`asia-south1`, uniform access, public-access prevention), applied `00_datasets.sql` (`urvi_cairn_{bronze,silver,gold}`), and created runtime SA `urvi-cairn-run` (`deploy.sh iam`). | `docs/checklist.md`, GCP `urvi-cairn-barmer-ai-agent` | `9d52f3d` (lockdown) |
| 2026-11-15 | **Deep-research `docs/build.md` & dual-check `docs/checklist.md` generated (v4.0.0):** Part I embeds SPE/public Cairn Barmer calibration (Mangala 180, Bhagyam 120 w/ `448 m TVDSS` OWC & `-16%` gap, Aishwariya 100 incl. horizontal `Barmer_Hill`, Raageshwari 60 deep volcanic tight gas = 460 wells; post-2008 completion windows; `42°C` pour point / `59°C` WAT; `<8,000 ppm` TDS HPAM/ASP flood; `JET_PUMP`/`ESP`/`PCP`/`SRP`/`GAS_LIFT`/`NATURAL`; `IC-01..IC-15`; 6 hero wells led by `MNG-042` & `RAG-014`; Vedanta roles/branding/India assets). Part II defines **64 atomic steps (`C0.1`–`C9.5`)** mirrored 1-for-1 in `docs/checklist.md` (`128` `Impl`+`Verify` checkboxes). Steps `C0.1`–`C0.5` verified & ticked. | `docs/build.md`, `docs/checklist.md`, `backlog_refinements.md` | not committed |
| 2026-11-15 | Added **`plan_prompt.md`**: the kickoff prompt for the Cairn chat (goal: same app, Barmer data generated → GCS / BigQuery → retrained models → deployed, in 3 days; scope, Argon + Flash delegation, day-by-day plan, rules, first steps). | `plan_prompt.md` | not committed |
| 2026-11-15 | **Cairn Google Cloud project set:** `urvi-cairn-barmer-ai-agent` replaces the placeholder in 28 files (deploy, env, settings, lakehouse, tests, diagrams). Project is active with billing; BigQuery / Dataform / Dataplex / Storage APIs already on; Cloud Run, Cloud Build, Artifact Registry, Vertex AI still to enable. Deploy guard still blocks the ONGC project / service. | many | not committed |
| 2026-11-15 | **Replica created and locked down.** Cloned the ONGC repo with history; removed the ONGC GitHub remote, added `urvi-cairn-barmer`; replaced every ONGC Google Cloud target with Cairn placeholders (project `urvi-cairn-barmer-ai-agent`, service `urvi-cairn-app`, datasets `urvi_cairn_bronze/silver/gold`, SA `urvi-cairn-run`, bucket `urvi-cairn-barmer-ai-agent-datalake`) in code, deploy, lakehouse and tests (33 files); added a deploy guard that refuses ONGC targets or a placeholder project (tested); removed the ONGC app shortcut; README banner, APP_LINK, this sheet. | many | not committed |

---

## 2. Current refinements

| ID | Date | Feedback (user's words) | Status | Next step |
|---|---|---|---|---|
| C-R1 | 2026-11-15 | *"The safest option is to create a replica of the entire repo, work in that repo for Cairn India, ultimately merge the two if it is ever needed. Even if we work on a different branch there is a possibility of updating some part of the ONGC repo accidentally."* | Done (decision CD-1) | — |
| C-R2 | 2026-11-15 | *"now we should generate a build.md file which should have very granular step by step instructions and then there should be a checklist.md file which will check all the steps that are implemenetd and verified. This cehck shluld be done after every compleetd step. Then there should also be a part that does the deep research about the cairn inida fields and that deep research should govern the data generation including depts of well, typical production and relevant interventions. The data should look as real as possible"* | Done (`docs/build.md` + `docs/checklist.md`; `62 / 65` steps verified) | Approve `C9.3` (Cloud Run deploy) & `C9.5` (final commit/push) |
| C-R3 | 2026-11-15 | *"so can I safely say its a single agent multitool architecture so leverate best of both worls an agent to understand what the human needs in a natural speken language and then deterministic logic to feel it into the machines to minimise hellucinations? if yes then I think that should be at the top line in architecture"* | Done (`Step C7.7` — added top-line banner in `ArchitectureView.tsx`, `current/target` dark & light HTMLs, `architecture_explain.py` / `how_urvi_works.md`, `ml_recommendation_engine.md`, `demo_flow.md`, and `README.md`; rebuilt `frontend/dist/`) | — |
| C-R4 | 2026-11-15 | *"can we have the same accent that we had earlier the indian accent? ... hey I want the indian accent of the ai agent what are you doing? I sill hear a US accent . can you check what accent do you have in urvi ongc?"* | Done (`Step C6.7` — set `SpeechConfig(language_code="en-IN"|"hi-IN")` in `session.py`, explicit `en-IN` prosody in `live_prompt.md`, female Indian voice priority in `VoiceAgentPanel.tsx`; verified via multimodal audio evaluation: shifted from `en-US` to `Indian English (en-IN) with high confidence`; deployed `urvi-cairn-app-00002-dx8`) | — |
| C-R5 | 2026-11-15 | *"as I see the interventions in ONGC Urvi I dont see them visually here. Can you see if there is a inconsistency? ... sure apply the fix and then redeploy"* | Done (`Step C7.8` — deployed `urvi-cairn-app-00003-cqg`, `6/6` live smoke checks passed + local `:5180` live) | Final git commit/push (`C9.5`) |

---

## 3. Feature backlog

| ID | Item | Status | Notes |
|---|---|---|---|
| **CB-1** | **Barmer data-generation strategy** | **Done (`Gate C1–C4` Passed)** | 460 synthetic wells (`Mangala` 180, `Bhagyam` 120, `Aishwariya` 100, `Raageshwari` 60); SPE-calibrated depths (`448 m TVDSS` Bhagyam OWC to `3,720 m MD` RDG volcanics), `42°C` pour point / `59°C` WAT waxy crude, `<8,000 ppm` TDS HPAM/ASP polymer flood, 6 lift types, 6 hero fixtures, 20,277 PDFs (`100%` fact-slot), BigQuery `asia-south1` Medallion (`29/29` parity). |
| **CB-2** | **Research note: Vedanta / Cairn report branding** | **Done (`C6.4` Verified)** | `cairn_vedanta_wordmark.svg` ("CAIRN OIL & GAS · VEDANTA LIMITED — Barmer Basin · RJ-ON-90/1"), `ongc_logo.svg` deleted, A4 field report (`test_tc032_field_report.py` `18 passed`) verified. |
| **CB-3** | **Research note: Vedanta Oil and Gas role names → access levels** | **Done (`C6.5` & `C7.3` Verified)** | *COO / Chief Digital & Information Officer*, *Asset Manager — Barmer (MBA & RDG)*, *Production / Well Services Engineer* (no E1–E4 or CMD). |
| **CB-4** | **Delegation plan: Argon + Gemini Flash data generation** | **Done (`C0–C9` Executed)** | `[O]` Orchestrator + `[A]` Argon (`argon-fields`, `argon-wellbore`, `argon-dg`) + `[F]` Flash (`flash-docs`). |
| **CB-5** | **Build on this repo: regenerate data, retrain models, Barmer map + Vedanta asset view, prompts and branding without ONGC, tests for the new wells** | **Done (`Gates C1–C8` Passed)** | Gate Q `0.7683`, Gate E `0.6587`, full `pytest` suite green, strict zero-ONGC audit `0` hits across source & 29,136 PDF chunks. |
| **CB-6** | **Cairn Google Cloud project + deployment** | **Done (`Gate C9` Passed — `urvi-cairn-app-00003-cqg` Live)** | `urvi-cairn-barmer-ai-agent` (`498143636903`): 5 APIs enabled, `urvi-cairn-run` SA active, GCS & BQ `asia-south1` populated; Cloud Run `urvi-cairn-app` live in `us-central1` (`6/6` remote smoke + `7/7` local selfcheck green). |

### 3.1 Open questions
- ~~Q1: Timing of the Cairn CIO meeting~~ → `2026-11-18` (ONGC demo untouched — verified `git -C ../wellpulse status --porcelain` empty).
- ~~Q2: Google Cloud project~~ → `urvi-cairn-barmer-ai-agent` (user, 2026-11-15).
- ~~Q3: Agent name for Cairn~~ → Keep **"Urvi"** (*"Urvi AI Agent for Cairn Oil & Gas, Barmer"* — user approved, 2026-11-15).

---

## 4. Decisions

| ID | Decision | Date | Detail |
|---|---|---|---|
| CD-1 | Separate replica repo for Cairn | 2026-11-15 (user) | Replaces ONGC BL-9 Q1 ("one app, no client switch"). Full isolation: own repo, remote, Google Cloud targets, deploy guard. Merge later only if needed (shared history makes it possible). |
| CD-2 | Top-line Single-Agent, Multi-Tool Hybrid Architecture thesis | 2026-11-15 (user) | Elevated to top line of Architecture tab (`ArchitectureView.tsx`), standalone dark/light diagrams (`build_architecture.py`), Explain drawer / `how_urvi_works.md`, `ml_recommendation_engine.md`, `demo_flow.md`, and `README.md`. |

---

## How to update this sheet
- Every change: add a row at the top of §1. New feedback: C-R*n* in §2 (user's exact words). New feature: CB-*n* in §3.
