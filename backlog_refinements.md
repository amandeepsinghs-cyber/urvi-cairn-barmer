# Urvi · Cairn / Vedanta Oil and Gas (Barmer Basin): Backlog & Refinements

**This is the reference sheet for the Cairn replica.** It has two working lists, **Current refinements** and
**Feature backlog**; every item gets full clarity with the user before anything is built.

**Origin:** replica of the ONGC WellPulse / Urvi demo, cloned 2026-11-15 at commit `c8fc208` (V 1.1) with history.
The ONGC backlog and decisions remain in git history (`git show c8fc208:backlog_refinements.md`).
**Deployment:** none yet (see [`APP_LINK.md`](./APP_LINK.md)).

> [!IMPORTANT]
> **Answer first:** Clarity phase. The repo is isolated from ONGC (own GitHub remote, Cairn placeholders for every Google
> Cloud target, deploy guard). Next: the four pre-build documents for Barmer (BL-9 deliverables), then the build.

---

## 1. Latest changes (newest first)

| Date | Change | Files | Commit |
|---|---|---|---|
| 2026-11-15 | **Deep-research `docs/build.md` & dual-check `docs/checklist.md` generated (v4.0.0):** Part I embeds SPE/public Cairn Barmer calibration (Mangala 180, Bhagyam 120 w/ `448 m TVDSS` OWC & `-16%` gap, Aishwariya 100 incl. horizontal `Barmer_Hill`, Raageshwari 60 deep volcanic tight gas = 460 wells; post-2008 completion windows; `42°C` pour point / `59°C` WAT; `<8,000 ppm` TDS HPAM/ASP flood; `JET_PUMP`/`ESP`/`PCP`/`SRP`/`GAS_LIFT`/`NATURAL`; `IC-01..IC-15`; 6 hero wells led by `MNG-042` & `RAG-014`; Vedanta roles/branding/India assets). Part II defines **64 atomic steps (`C0.1`–`C9.5`)** mirrored 1-for-1 in `docs/checklist.md` (`128` `Impl`+`Verify` checkboxes). Steps `C0.1`–`C0.5` verified & ticked. | `docs/build.md`, `docs/checklist.md`, `backlog_refinements.md` | not committed |
| 2026-11-15 | Added **`plan_prompt.md`**: the kickoff prompt for the Cairn chat (goal: same app, Barmer data generated → GCS / BigQuery → retrained models → deployed, in 3 days; scope, Argon + Flash delegation, day-by-day plan, rules, first steps). | `plan_prompt.md` | not committed |
| 2026-11-15 | **Cairn Google Cloud project set:** `urvi-cairn-barmer-ai-agent` replaces the placeholder in 28 files (deploy, env, settings, lakehouse, tests, diagrams). Project is active with billing; BigQuery / Dataform / Dataplex / Storage APIs already on; Cloud Run, Cloud Build, Artifact Registry, Vertex AI still to enable. Deploy guard still blocks the ONGC project / service. | many | not committed |
| 2026-11-15 | **Replica created and locked down.** Cloned the ONGC repo with history; removed the ONGC GitHub remote, added `urvi-cairn-barmer`; replaced every ONGC Google Cloud target with Cairn placeholders (project `urvi-cairn-barmer-ai-agent`, service `urvi-cairn-app`, datasets `urvi_cairn_bronze/silver/gold`, SA `urvi-cairn-run`, bucket `urvi-cairn-barmer-ai-agent-datalake`) in code, deploy, lakehouse and tests (33 files); added a deploy guard that refuses ONGC targets or a placeholder project (tested); removed the ONGC app shortcut; README banner, APP_LINK, this sheet. | many | not committed |

---

## 2. Current refinements

| ID | Date | Feedback (user's words) | Status | Next step |
|---|---|---|---|---|
| C-R1 | 2026-11-15 | *"The safest option is to create a replica of the entire repo, work in that repo for Cairn India, ultimately merge the two if it is ever needed. Even if we work on a different branch there is a possibility of updating some part of the ONGC repo accidentally."* | Done (decision CD-1) | — |
| C-R2 | 2026-11-15 | *"now we should generate a build.md file which should have very granular step by step instructions and then there should be a checklist.md file which will check all the steps that are implemenetd and verified. This cehck shluld be done after every compleetd step. Then there should also be a part that does the deep research about the cairn inida fields and that deep research should govern the data generation including depts of well, typical production and relevant interventions. The data should look as real as possible"* | Done (`docs/build.md` v4.0.0 + `docs/checklist.md` v4.0.0; `C0.1`–`C0.5` verified) | Approve `C0.7` (Commit #1) & `C0.8` (5 GCP APIs + IAM) to start Stage C1 |

---

## 3. Feature backlog

| ID | Item | Status | Notes |
|---|---|---|---|
| **CB-1** | **Barmer data-generation strategy** | **Specified (`docs/build.md` Part I §§1–7)** | 460 synthetic wells (`Mangala` 180, `Bhagyam` 120, `Aishwariya` 100, `Raageshwari` 60); SPE-calibrated depths (`448 m TVDSS` Bhagyam OWC to `3,720 m MD` RDG volcanics), `42°C` pour point / `59°C` WAT waxy crude, `<8,000 ppm` TDS HPAM/ASP polymer flood, 6 lift types (`JET_PUMP`, `ESP`, `PCP`, `SRP`, `GAS_LIFT`, `NATURAL`), 6 hero fixtures. |
| **CB-2** | **Research note: Vedanta / Cairn report branding** | **Specified (`docs/build.md` Part I §8)** | `cairn_vedanta_wordmark.svg` ("CAIRN OIL & GAS · VEDANTA LIMITED — Barmer Basin · RJ-ON-90/1") replacing `ongc_logo.svg`; `[verify]` swap if official corporate SVG supplied. |
| **CB-3** | **Research note: Vedanta Oil and Gas role names → access levels** | **Specified (`docs/build.md` Part I §8)** | *COO / Chief Digital & Information Officer*, *Asset Manager — Barmer (MBA & RDG)*, *Production / Well Services Engineer* (no E1–E4 or CMD). |
| **CB-4** | **Delegation plan: Argon + Gemini Flash data generation** | **Specified (`docs/build.md` §0.1 & Part II)** | `[O]` Orchestrator (contracts, ML gates, reviews) + `[A]` Argon (`gemini-launch-candidate-high` via `swarm`, generators/DG/tests) + `[F]` Flash (`Model="flash"`, zero-digit PDF prose/SOPs/UI scaffolds). |
| CB-5 | Build on this repo: regenerate data, retrain models, Barmer map + Vedanta asset view, prompts and branding without ONGC, tests for the new wells | After CB-1…CB-4 | Many tests and fixtures are pinned to Assam wells (GK-129 etc.); they will be replaced, not deleted blindly. |
| CB-6 | Cairn Google Cloud project + deployment | **Project set 2026-11-15:** `urvi-cairn-barmer-ai-agent` (number 498143636903, active, billing on) | Wired into deploy, env, settings, lakehouse and tests. Before the first deploy, enable Cloud Run, Cloud Build, Artifact Registry, Vertex AI and IAM APIs and create the runtime service account (`deploy.sh iam`). Not done yet. |

### 3.1 Open questions
- Q1: Timing of the Cairn CIO meeting (and the ONGC CMD demo, which must stay untouched).
- ~~Q2: Google Cloud project~~ → `urvi-cairn-barmer-ai-agent` (user, 2026-11-15).
- Q3: Agent name for Cairn: keep "Urvi" or a different name?

---

## 4. Decisions

| ID | Decision | Date | Detail |
|---|---|---|---|
| CD-1 | Separate replica repo for Cairn | 2026-11-15 (user) | Replaces ONGC BL-9 Q1 ("one app, no client switch"). Full isolation: own repo, remote, Google Cloud targets, deploy guard. Merge later only if needed (shared history makes it possible). |

---

## How to update this sheet
- Every change: add a row at the top of §1. New feedback: C-R*n* in §2 (user's exact words). New feature: CB-*n* in §3.
