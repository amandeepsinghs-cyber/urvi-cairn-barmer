# Cairn Oil & Gas (Barmer Basin) — Step-by-Step Implementation & Verification Checklist (`checklist.md`)
## Urvi AI Agent for Cairn Oil & Gas · Vedanta Limited (Block RJ-ON-90/1, Rajasthan)

**Document Version:** 4.0.0 (Cairn Barmer Replica — 64-Step Dual-Check Tracker)  
**Date:** 2026-11-15 · **CIO Meeting Deadline:** 2026-11-18  
**Authoritative Build Guide:** [`build.md`](./build.md) (Part I Deep Research Spec · Part II 64 Atomic Steps)  
**Companion Docs:** [`backlog_refinements.md`](../backlog_refinements.md) · [`plan_prompt.md`](../plan_prompt.md) · [`DELEGATION.md`](./DELEGATION.md)  
*(Inherited ONGC checklist remains permanently preserved in git history at `git show c8fc208:docs/checklist.md`.)*

---

> [!IMPORTANT]
> **Mandatory Step-by-Step Verification Law (Enforced After Every Single Completed Step):**
> 1. Every atomic step `Ck.m` in [`docs/build.md`](./build.md) has **TWO checkboxes** below:
>    - **`[Ck.m · Impl]`** — Code / configuration / document written within declared file ownership (`[O]` Orchestrator, `[A]` Argon, `[F]` Gemini Flash).
>    - **`[Ck.m · Verify]`** — Exact verification command from `docs/build.md` executed by `[O]` in the main workspace, exited `0`, with measured output recorded inline under *Evidence*.
> 2. **Zero Batch Drift on Verification:** Never move to step `Ck.(m+1)` until **both** `[Ck.m · Impl]` and `[Ck.m · Verify]` are checked `[x]`.
> 3. **User Approval Gates (`[USER GATE]`):** Pause and obtain explicit user OK before `C0.7` (initial lockdown commit/push), `C0.8` (enable 5 GCP APIs & IAM SA), `C4.1` (GCS/BQ cloud resource creation), `C9.3` (Cloud Run deploy), and `C9.5` (final git push).
> 4. **Honest ML Gates:** If `C5.3` (Gate Q) or `C5.4` (Gate E) fails, mark `BLOCKED` and report exact metrics to the user immediately — **never relax thresholds or tune to pass**.

---

## Progress Summary

| Stage | Scope | Steps | Impl Checked | Verify Checked | Gate Status |
|---|---|---|---|---|---|
| **C0** | Deep Research Lock, Lockdown Commit & GCP Preflight | `C0.1`–`C0.8` (8) | `6 / 8` | `6 / 8` | ⏳ In Progress |
| **C1** | Core Barmer 60-Month Synthetic Data Engine (`460` Wells) | `C1.1`–`C1.12` (12) | `0 / 12` | `0 / 12` | ⬜ Pending |
| **C2** | Stage-DG Wellbore, Deviation, Integrity, Hazards & GeoJSONs | `C2.1`–`C2.5` (5) | `0 / 5` | `0 / 5` | ⬜ Pending |
| **C3** | Barmer PDF Corpus (`D01–D11`), SOPs & 100% Fact-Slot Audit | `C3.1`–`C3.5` (5) | `0 / 5` | `0 / 5` | ⬜ Pending |
| **C4** | GCS Lakehouse & BigQuery Medallion (`asia-south1`) | `C4.1`–`C4.6` (6) | `0 / 6` | `0 / 6` | ⬜ Pending |
| **C5** | ML Feature Rebuild, Retraining (Gate Q & E) & Analog Index | `C5.1`–`C5.5` (5) | `0 / 5` | `0 / 5` | ⬜ Pending |
| **C6** | Backend Tools, Cairn Branding, Prompts, Voice & RBAC | `C6.1`–`C6.6` (6) | `0 / 6` | `0 / 6` | ⬜ Pending |
| **C7** | Frontend Map, Voice Controls, Persona UI, Architecture & Docs | `C7.1`–`C7.6` (6) | `0 / 6` | `0 / 6` | ⬜ Pending |
| **C8** | Test Suite, Golden Schemas, Eval Migration & Zero-ONGC Audit | `C8.1`–`C8.6` (6) | `0 / 6` | `0 / 6` | ⬜ Pending |
| **C9** | Local Rehearsal, Cloud Run Deploy & CIO Demo Script | `C9.1`–`C9.5` (5) | `0 / 5` | `0 / 5` | ⬜ Pending |
| **TOTAL** | **Full Cairn Oil & Gas (Barmer Basin) Build** | **64 Steps** | **`6 / 64`** | **`6 / 64`** | — |

---

## Stage C0 · Deep Research Lock, Repo Lockdown Commit & GCP Preflight (Day 1 AM)

- [x] **[C0.1 · Impl]** `[O]` Author Barmer Basin stratigraphy (7 units), 4-field portfolio (`Mangala` 180, `Bhagyam` 120, `Aishwariya` 100, `Raageshwari` 60 = 460 wells), post-2008 completion windows, pad coordinates, and true depth/casing laws in `docs/build.md` Part I §§1–3.
- [x] **[C0.1 · Verify]** `[O]` Run `C0.1` assertion check on `docs/build.md` (`448 m TVDSS`, `Raageshwari_Volcanics`, `MPT-NAGANA`, `RGT-TERMINAL`, `2008-06-01`). · *Evidence:* `C0.1 OK (exit 0, 2026-11-15)`

- [x] **[C0.2 · Impl]** `[O]` Author waxy crude rheology (`42°C` pour point, `59°C` WAT, Bhagyam biodegradation `15–500 cP`), `<8,000 ppm` TDS low-salinity HPAM/ASP EOR rules, and 6-lift telemetry table (`JET_PUMP`, `ESP`, `PCP`, `SRP`, `GAS_LIFT`, `NATURAL`) in `docs/build.md` Part I §§4–5.
- [x] **[C0.2 · Verify]** `[O]` Run `C0.2` assertion check on `docs/build.md` (`42.0°C`, `59.0°C`, `HPAM`, all 6 lifts, `-0.16` Bhagyam bias). · *Evidence:* `C0.2 OK (exit 0, 2026-11-15)`

- [x] **[C0.3 · Impl]** `[O]` Author Barmer workover catalogue (`IC-01..IC-15`, cost bands, rig-days, `>= 45` training episode floor) and 6 scripted hero wells (`MNG-042`, `BHG-019`, `BHG-088`, `ASH-023`, `ASH-061`, `RAG-014`) in `docs/build.md` Part I §§6–7.
- [x] **[C0.3 · Verify]** `[O]` Run `C0.3` assertion check verifying `IC-01..IC-15` and all 6 hero well IDs in `docs/build.md`. · *Evidence:* `C0.3 OK (exit 0, 2026-11-15)`

- [x] **[C0.4 · Impl]** `[O]` Author Cairn / Vedanta identity, `cairn_vedanta_wordmark.svg` spec, Vedanta upstream personas, 4 Cairn India upstream asset map locations (`Barmer`, `Ravva`, `Cambay`, `Jorhat OALP`), and `[verify]` markers in `docs/build.md` Part I §8.
- [x] **[C0.4 · Verify]** `[O]` Run `C0.4` assertion check on `docs/build.md` (`Urvi AI Agent for Cairn Oil & Gas, Barmer`, `Ravva`, `Cambay`, `[verify]`). · *Evidence:* `C0.4 OK (exit 0, 2026-11-15)`

- [x] **[C0.5 · Impl]** `[O]` Generate 1-to-1 synchronized `docs/checklist.md` (64 steps × 2 checks) and log update in `backlog_refinements.md` (§1, §2 `C-R2`, §3 `CB-1..CB-4`).
- [x] **[C0.5 · Verify]** `[O]` Run `C0.5` regex parity script confirming `build.md` steps == `checklist.md` `Impl` == `checklist.md` `Verify` == `64`. · *Evidence:* `C0.5 OK: 64/64 steps synced (exit 0, 2026-11-15)`

- [x] **[C0.6 · Impl]** `[O]` Execute local port preflight (`:5180`, `:8002`), `deploy/deploy.sh plan` target guard check, and `cd backend && uv sync --frozen`.
- [x] **[C0.6 · Verify]** `[O]` Confirm zero listeners on `:5180`/`:8002`, `deploy.sh plan` exits `0`, and `uv run python -c "import fastapi, pandas, sklearn"` passes. · *Evidence:* `C0.6 OK — 0 listeners, deploy.sh plan exit 0, uv synced 103 pkgs (2026-11-15)`

- [ ] **[C0.7 · Impl]** `[O]` **`[USER GATE]`** After explicit user OK, stage, commit, and push initial Cairn lockdown + `plan_prompt.md` + `docs/build.md` + `docs/checklist.md` + `backlog_refinements.md` to `amandeepsinghs-cyber/urvi-cairn-barmer` (`main`).
- [ ] **[C0.7 · Verify]** `[O]` Confirm `git remote -v` has only `urvi-cairn-barmer`, `git status --porcelain` is empty, and `origin/main` is synced. · *Evidence:* `pending`

- [ ] **[C0.8 · Impl]** `[O]` **`[USER GATE]`** After explicit user OK, enable `run`, `cloudbuild`, `artifactregistry`, `aiplatform`, and `iam` APIs in `urvi-cairn-barmer-ai-agent` and run `bash deploy/deploy.sh iam`.
- [ ] **[C0.8 · Verify]** `[O]` Confirm all 5 GCP APIs enabled and `urvi-cairn-run@urvi-cairn-barmer-ai-agent.iam.gserviceaccount.com` exists. · *Evidence:* `pending`

### Gate C0 Sign-Off
- [ ] **Gate C0 Passed:** Deep research locked (`C0.1`–`C0.5`), local `uv` env ready (`C0.6`), Commit #1 pushed (`C0.7`), 5 GCP APIs + `urvi-cairn-run` SA active (`C0.8`).

---

## Stage C1 · Core Barmer 60-Month Synthetic Data Engine (`460 Wells` · Day 1)

- [ ] **[C1.1 · Impl]** `[O]` Extend `FieldConfig` in `backend/app/analytics/generator/fields/base.py` with `completion_window`, `surface_shoe_m`, `casing_mix_in`, `tubing_mix_in`, `zone_depths_md`, `zone_md_tvd_ratio`, and Barmer `primary_reservoirs`.
- [ ] **[C1.1 · Verify]** `[O]` Run `C1.1` import & dataclass field assertion in `backend/`. · *Evidence:* `pending`

- [ ] **[C1.2 · Impl]** `[A]` Implement `MANGALA` (`MNG-001..180`, seed `5101`, `MPT-NAGANA`, `55% JET_PUMP / 35% ESP / 5% PCP / 5% SRP`, hero `MNG-042`) in `backend/app/analytics/generator/fields/mangala.py` (`[O]` hero review).
- [ ] **[C1.2 · Verify]** `[O]` Run `C1.2` assertion check (`n_wells==180`, lift sum `1.0`, `MNG-042` fixture present). · *Evidence:* `pending`

- [ ] **[C1.3 · Impl]** `[A]` Implement `BHAGYAM` (`BHG-001..120`, seed `5202`, shallow `OWC 448 m TVDSS`, `target_bias=-0.16`, `40% PCP / 35% ESP / 15% JET_PUMP / 10% SRP`, heroes `BHG-019` & `BHG-088`) in `backend/app/analytics/generator/fields/bhagyam.py` (`[O]` hero review).
- [ ] **[C1.3 · Verify]** `[O]` Run `C1.3` assertion check (`n_wells==120`, `target_bias==-0.16`, `BHG-019` & `BHG-088` present). · *Evidence:* `pending`

- [ ] **[C1.4 · Impl]** `[A]` Implement `AISHWARIYA` (`ASH-001..100`, seed `5303`, AF + horizontal `ASH-ABH-3` `Barmer_Hill`, fixtures `ASH-023` & `ASH-061`) in `backend/app/analytics/generator/fields/aishwariya.py` (`[O]` hero review).
- [ ] **[C1.4 · Verify]** `[O]` Run `C1.4` assertion check (`n_wells==100`, `ASH-023` & `ASH-061` present). · *Evidence:* `pending`

- [ ] **[C1.5 · Impl]** `[A]` Implement `RAAGESHWARI` (`RAG-001..060`, seed `5404`, `RGT-TERMINAL`, deep `Raageshwari_Volcanics` `2,950–3,720 m MD`, hero `RAG-014`) in `raageshwari.py`, wire `fields/__init__.py`, and delete `geleki.py`, `lakwa.py`, `lakhmani.py`.
- [ ] **[C1.5 · Verify]** `[O]` Run `C1.5` check (`list(FIELD_CONFIGS)==['Mangala','Bhagyam','Aishwariya','Raageshwari']`, total wells `== 460`). · *Evidence:* `pending`

- [ ] **[C1.6 · Impl]** `[A]` Refactor `backend/app/analytics/generator/wells_native.py` for post-2008 completion dates, field-zone MD/TVD profiles, tubular sizes, and 6 lift types.
- [ ] **[C1.6 · Verify]** `[O]` Run `C1.6` check (`460` wells, `completion_date >= 2008`, Bhagyam `total_depth_tvd_m < 700 m`). · *Evidence:* `pending`

- [ ] **[C1.7 · Impl]** `[A]` Refactor `backend/app/analytics/generator/formation_tops.py` for the 7-unit Barmer stratigraphic column (`Thar_Alluvium_Kapurdi` → `Raageshwari_Volcanics`).
- [ ] **[C1.7 · Verify]** `[O]` Run `C1.7` check confirming strictly contiguous positive layer thicknesses across all 460 wells. · *Evidence:* `pending`

- [ ] **[C1.8 · Impl]** `[A]` Refactor `backend/app/analytics/generator/construction.py` for dynamic shallow surface shoes (`< perf_top_m - 80 m`), deep RDG intermediate casing, and 6-lift downhole strings.
- [ ] **[C1.8 · Verify]** `[O]` Run `C1.8` check confirming `SURFACE` shoe `< perf_top_m - 50 m` and valid `tubing_string` / `perforation_intervals` across all 4 fields. · *Evidence:* `pending`

- [ ] **[C1.9 · Impl]** `[A]` Update `catalogue.py`, `pressure_surveys.py`, `telemetry.py`, `operations_events.py`, `hierarchy.py`, and `targets.py` for Barmer lift/reservoir physics and desert/pad events.
- [ ] **[C1.9 · Verify]** `[O]` Run `C1.9` check confirming `IC-01..IC-15` coverage and zero `ONGC` strings in `job_catalogue`. · *Evidence:* `pending`

- [ ] **[C1.10 · Impl]** `[O]` Generalize `simulate.py` & `native.py` across 6 lift types (`>= 45` episodes per `IC` class) and implement the 6 Barmer hero fixtures in `fixtures.py`.
- [ ] **[C1.10 · Verify]** `[O]` Run `C1.10` Mangala simulation smoke test confirming `MNG-042` and 60-month `daily_production` output. · *Evidence:* `pending`

- [ ] **[C1.11 · Impl]** `[O]` Update `generate.py` (+ Barmer `well_run`, `draft_plan`, `decision_log`), delete `landing/{geleki,lakwa,lakhmani}/`, and run `generate --field all`.
- [ ] **[C1.11 · Verify]** `[O]` Confirm 4 Barmer folders + `asset/` materialized (`460` wells) and legacy Assam folders absent. · *Evidence:* `pending`

- [ ] **[C1.12 · Impl]** `[O]` Update `validate.py` (`V-N1..V-N7`) and `pin_targets.py` for Barmer fields & hero wells.
- [ ] **[C1.12 · Verify]** `[O]` Run `uv run python -m app.analytics.generator.validate` (`0` violations) and `pin_targets`. · *Evidence:* `pending`

### Gate C1 Sign-Off
- [ ] **Gate C1 Passed:** All 460 Barmer wells, 60-month core parquets, and asset tables generated and `generator.validate` exits `0` (`backlog_refinements.md` updated).

---

## Stage C2 · Stage-DG Wellbore, Deviation, Integrity & Hazard Tables + GeoJSONs (Day 1 PM)

- [ ] **[C2.1 · Impl]** `[A]` Update `dg/common.py` and `dg/tubing_deviation.py` for Barmer pad S-wells and `ASH-ABH-3` `Barmer_Hill` horizontals (`tubing_tally`, `deviation_survey`).
- [ ] **[C2.1 · Verify]** `[O]` Run `dg --field mangala` and verify `tubing_tally` & `deviation_survey` schema + `100% is_synthetic`. · *Evidence:* `pending`

- [ ] **[C2.2 · Impl]** `[A]` Update `dg/integrity.py` (`barrier_tests`, `wellhead_rating` `3k/5k/10k psi`, plus `RAG-014` failed annular barrier + frac-rating veto fixture).
- [ ] **[C2.2 · Verify]** `[O]` Run `dg --field raageshwari` and verify `RAG-014` `FAIL` record in `barrier_tests.parquet`. · *Evidence:* `pending`

- [ ] **[C2.3 · Impl]** `[A]` Update `dg/hazards_fishing.py` (`fluid_hazards` `42°C` waxy crude / polymer ppm / RDG CO2; `fishing_records` on failed jobs) and run `dg --field all`.
- [ ] **[C2.3 · Verify]** `[O]` Confirm all `24` DG parquets (`4 fields × 6 tables`) exist, non-empty, and `100% is_synthetic=True`. · *Evidence:* `pending`

- [ ] **[C2.4 · Impl]** `[A]` Generate `mangala`, `bhagyam`, `aishwariya`, and `raageshwari` `*_boundary.geojson` files, update `tools/geodata.py`, and delete Assam GeoJSONs.
- [ ] **[C2.4 · Verify]** `[O]` Confirm `load_field_geojson` loads all 4 Barmer polygons and `geleki_boundary.geojson` is removed. · *Evidence:* `pending`

- [ ] **[C2.5 · Impl]** `[O]` Port `test_dg_tubing_deviation.py`, `test_dg_integrity.py`, and `test_dg_hazards_fishing.py` to the 4 Barmer fields (`460` wells).
- [ ] **[C2.5 · Verify]** `[O]` Run `pytest` on all 3 Stage-DG consistency test suites (`0` failures). · *Evidence:* `pending`

### Gate C2 Sign-Off
- [ ] **Gate C2 Passed:** All 24 Stage-DG parquets, 4 Barmer GeoJSONs, and DG unit consistency suites green (`backlog_refinements.md` updated).

---

## Stage C3 · Barmer PDF Document Corpus (`D01–D11`), SOPs & Fact-Slot Audit (Day 1 PM)

- [ ] **[C3.1 · Impl]** `[F]` Rewrite `templates/sop/IC-01.yaml..IC-14.yaml` for Cairn Barmer operations (HOCU wax flush, wireline Jet-Pump insert, HPAM gel squeeze, ABH/RDG prop-frac) (`[O]` review).
- [ ] **[C3.1 · Verify]** `[O]` Confirm zero ONGC/Assam tokens in `sop/` and `load_all_sops()` returns all 14 SOPs. · *Evidence:* `pending`

- [ ] **[C3.2 · Impl]** `[F]` Rewrite `templates/hero_text.yaml` for `MNG-042`, `BHG-019`, `BHG-088`, `ASH-023`, `ASH-061`, and `RAG-014` using `{{slot}}` tokens only (`[O]` review).
- [ ] **[C3.2 · Verify]** `[O]` Confirm zero Assam well IDs/tokens and valid YAML structure in `hero_text.yaml`. · *Evidence:* `pending`

- [ ] **[C3.3 · Impl]** `[F]` Update `docs_pdf/{facts,render,validate,show,ir,index}.py`, `templates/{d08_rca,d09_field_study,d10_monthly}.py`, and `slot_catalogue/D01..D11.json` for Cairn Barmer (`[O]` review).
- [ ] **[C3.3 · Verify]** `[O]` Confirm grep finds `0` ONGC/Assam tokens across `backend/app/analytics/docs_pdf/`. · *Evidence:* `pending`

- [ ] **[C3.4 · Impl]** `[O]` Build, scanify (10% D1/D5 + `MNG-042` scanned CBL), validate, and index the full Barmer PDF corpus (`uv run python -m app.analytics.docs_pdf.build --field all`).
- [ ] **[C3.4 · Verify]** `[O]` Confirm `docs_pdf.build --field all` exits `0` and populates `data/docs_pdf/` and `data/index/`. · *Evidence:* `pending`

- [ ] **[C3.5 · Impl]** `[O]` Execute standalone fact-slot digit audit across `HERO`, `SOP`, and `--full` corpus.
- [ ] **[C3.5 · Verify]** `[O]` Confirm `docs_pdf.validate --type HERO`, `--type SOP`, and `--full` all exit `0` (`0` unauthorized digits). · *Evidence:* `pending`

### Gate C3 Sign-Off
- [ ] **Gate C3 Passed:** Full D01–D11 Barmer PDF corpus rendered, scanified, BM25-indexed, and 100% fact-slot validated (`backlog_refinements.md` updated).

---

## Stage C4 · GCS Lakehouse & BigQuery Medallion Pipeline (`asia-south1` · Day 1 Eve)

- [ ] **[C4.1 · Impl]** `[O]` **`[USER GATE]`** Provision `gs://urvi-cairn-barmer-ai-agent-datalake` in `asia-south1` with uniform bucket-level access and public-access prevention.
- [ ] **[C4.1 · Verify]** `[O]` Run `gcloud storage buckets describe` confirming `ASIA-SOUTH1` and uniform access `True`. · *Evidence:* `pending`

- [ ] **[C4.2 · Impl]** `[A]` Update `lakehouse/config.py`, `lakehouse/load/{doc_chunks,dossier_facts}.py`, `lakehouse/dataform/definitions/gold/*.sqlx`, and regenerate `lakehouse/ddl/*.sql` via `generate_ddl.py`.
- [ ] **[C4.2 · Verify]** `[O]` Confirm `generate_ddl.py` exits `0` and zero ONGC/Assam tokens remain in `lakehouse/`. · *Evidence:* `pending`

- [ ] **[C4.3 · Impl]** `[O]` Upload Barmer landing parquets (`bronze_upload.py`) and PDF corpus (`documents_upload.py`) to `gs://urvi-cairn-barmer-ai-agent-datalake`.
- [ ] **[C4.3 · Verify]** `[O]` Confirm `--dry-run` + live uploads exit `0` and objects exist under `bronze/` & `documents/`. · *Evidence:* `pending`

- [ ] **[C4.4 · Impl]** `[O]` Create `urvi_cairn_{bronze,silver,gold}` datasets (`00_datasets.sql`), dry-run, and apply `10..40` DDL files via `apply_ddl.py`.
- [ ] **[C4.4 · Verify]** `[O]` Confirm `apply_ddl.py --dry-run-only` & `apply_ddl.py` exit `0` and all 3 datasets exist in `asia-south1`. · *Evidence:* `pending`

- [ ] **[C4.5 · Impl]** `[O]` Run `bronze_to_silver.py` MERGE, `doc_chunks.py`, and `dossier_facts.py` loaders into BigQuery.
- [ ] **[C4.5 · Verify]** `[O]` Confirm `bronze_to_silver.py --check-only` reports 100% row-count parity and doc/dossier tables are populated. · *Evidence:* `pending`

- [ ] **[C4.6 · Impl]** `[O]` Compile and execute Dataform Gold models (`@dataform/cli@3.0.25`) in `lakehouse/dataform/`.
- [ ] **[C4.6 · Verify]** `[O]` Confirm Dataform run + `field_kpi_monthly_reconciles` assertion succeed and `urvi_cairn_silver.well_master` counts `180 / 120 / 100 / 60` (`460` total). · *Evidence:* `pending`

### Gate C4 Sign-Off
- [ ] **Gate C4 Passed:** GCS datalake + BigQuery Bronze/Silver/Gold Medallion live in `asia-south1` with 100% row parity (`backlog_refinements.md` updated).

---

## Stage C5 · ML Feature Engineering, Model Retraining & Look-Alike Index (Day 2 AM)

- [ ] **[C5.1 · Impl]** `[O]` Refactor `backend/app/analytics/model/features.py` for Barmer `FIELDS` (4), `ZONES` (4), and `LIFT_TYPES` (6) with strict `< s` causal truncation.
- [ ] **[C5.1 · Verify]** `[O]` Confirm `build_features('MNG-042', date(2026,9,23))` returns `status=='OK'` with `field_Mangala` and `lift_JET_PUMP`. · *Evidence:* `pending`

- [ ] **[C5.2 · Impl]** `[O]` Port `backend/tests/unit/test_features_no_leakage.py` to Barmer wells (`MNG-042`, `BHG-019`, `ASH-023`, `RAG-014`).
- [ ] **[C5.2 · Verify]** `[O]` Run `pytest tests/unit/test_features_no_leakage.py -q` (`0` failures — zero temporal/target leakage proven before training). · *Evidence:* `pending`

- [ ] **[C5.3 · Impl]** `[O]` Update `train_classifier.py` & `intervention_classifier.py` for Barmer (`ASH-023` & `ASH-061` fixtures, `leave_aishwariya_out`) and retrain `intervention_classifier_v1.pkl`.
- [ ] **[C5.3 · Verify]** `[O]` Confirm **Gate Q passes honestly** (`0.70 <= macro_f1 <= 0.92`, `top3 >= 0.90`, `+0.05` over baseline, `ece <= 0.08`, `min_support >= 30`). · *Evidence:* `pending`

- [ ] **[C5.4 · Impl]** `[O]` Update `train.py` & `candidate_ranking.py::predict_failure` for Barmer pumped producers and retrain CoxPH survival model (`coxph_srp_v1.pkl`).
- [ ] **[C5.4 · Verify]** `[O]` Confirm **Gate E passes honestly** (`0.65 <= holdout_c_index <= 0.78` and `holdout_c_index > trigger_b_c_index`). · *Evidence:* `pending`

- [ ] **[C5.5 · Impl]** `[O]` Rebuild `analog_index.parquet` (`success_engine.py --build-index`) across all 460 Barmer wells.
- [ ] **[C5.5 · Verify]** `[O]` Verify deterministic top-3 recommendations & engineering plausibility on `MNG-042`, `BHG-019`, `ASH-023`, `ASH-061`, and `RAG-014`. · *Evidence:* `pending`

### Gate C5 Sign-Off
- [ ] **Gate C5 Passed:** Features leakage-free, Intervention Classifier Gate Q passed honestly, Lift Survival Model Gate E passed honestly, and 460-well Analog Index rebuilt (`backlog_refinements.md` updated).

---

## Stage C6 · Backend Tools, Cairn Branding, Prompts, Voice & RBAC (Day 2 PM)

- [ ] **[C6.1 · Impl]** `[O]` Update `backend/app/data_access/{adapters,parquet_repo,bigquery_repo}.py` (`BASIN = "Barmer Basin (RJ-ON-90/1)"`, retired prefix handling).
- [ ] **[C6.1 · Verify]** `[O]` Confirm `BASIN` contains `"Barmer"` and `get_repo().list_wells()` returns `460` wells. · *Evidence:* `pending`

- [ ] **[C6.2 · Impl]** `[O]` Replace India asset map data (`ongc_assets.py` / `cairn_assets.py` & `api/asset.py`) with Cairn/Vedanta's 4 blocks (`RJ-ON-90/1 Barmer`, `Ravva`, `Cambay`, `Jorhat OALP`).
- [ ] **[C6.2 · Verify]** `[O]` Confirm `GET /api/geo/cairn-assets` returns `200` with `Barmer` & `Ravva` and zero `ONGC` strings. · *Evidence:* `pending`

- [ ] **[C6.3 · Impl]** `[O]` Clean all remaining `backend/app/analytics/tools/*.py` modules of `Assam`/`Geleki`/`Lakwa`/`Lakhmani`/`Nazira` strings and docstrings.
- [ ] **[C6.3 · Verify]** `[O]` Confirm grep finds `0` Assam/ONGC tokens across `backend/app/analytics/tools/` (excl. `field_report.py` handled in `C6.4`). · *Evidence:* `pending`

- [ ] **[C6.4 · Impl]** `[F]` Create `frontend/public/brand/cairn_vedanta_wordmark.svg`, delete `ongc_logo.svg`, and rebrand `backend/app/analytics/tools/field_report.py` (`[O]` review).
- [ ] **[C6.4 · Verify]** `[O]` Confirm `ongc_logo.svg` deleted, `cairn_vedanta_wordmark.svg` exists, and `build_field_report('MNG-042')` passes sidecar validation with `"Cairn"` branding and zero `"ONGC"`. · *Evidence:* `pending`

- [ ] **[C6.5 · Impl]** `[O]` Update RBAC role titles & API docstrings in `backend/app/agent/rbac.py` and `backend/app/api/{me,analytics_wells,docs,dossier,fields,wells}.py` to Vedanta upstream roles.
- [ ] **[C6.5 · Verify]** `[O]` Confirm `GET /api/me` returns `200` with Cairn/Vedanta persona metadata and zero `"ONGC"`. · *Evidence:* `pending`

- [ ] **[C6.6 · Impl]** `[O]` Rebrand `backend/app/agent/{prompt,router,runner,ui_control,adk_tools,adk_tools_ext,fake_llm,callbacks}.py` and `backend/app/live/{live_prompt.md,session,voice_tools,fallback}.py` to *"Urvi AI Agent for Cairn Oil & Gas, Barmer"* (`MNG|BHG|ASH|RAG`).
- [ ] **[C6.6 · Verify]** `[O]` Confirm zero ONGC/Assam tokens across `agent/`, `live/`, `api/` and `build_system_prompt()` contains `"Cairn Oil & Gas"` and `"Mangala"`. · *Evidence:* `pending`

### Gate C6 Sign-Off
- [ ] **Gate C6 Passed:** Backend tools, A4 field report, RBAC roles, ADK chat agent, and Gemini Live voice prompts 100% rebranded to Cairn Barmer (`backlog_refinements.md` updated).

---

## Stage C7 · Frontend Map, Voice Controls, Persona UI, Architecture Tab & Docs (Day 2 PM)

- [ ] **[C7.1 · Impl]** `[F]` Update `frontend/src/components/map/WellMap.tsx` & `frontend/src/api/asset.ts` for `/api/geo/cairn-assets`, `BARMER_DRILL_BOUNDS`, and Barmer pads/MPT/RGT (`[O]` review).
- [ ] **[C7.1 · Verify]** `[O]` Confirm zero ONGC/Assam tokens in `WellMap.tsx` & `asset.ts` and `npx tsc --noEmit` exits `0`. · *Evidence:* `pending`

- [ ] **[C7.2 · Impl]** `[F]` Update `App.tsx`, `uiCommands.ts`, `api/chat.ts`, `VoiceAgentPanel.tsx` (English default greeting), `FieldHistoryChart.tsx`, and `FieldReportOverlay.tsx` (`[O]` review).
- [ ] **[C7.2 · Verify]** `[O]` Confirm zero ONGC/Assam tokens in modified UI files and `npx tsc --noEmit` exits `0`. · *Evidence:* `pending`

- [ ] **[C7.3 · Impl]** `[F]` Update `PersonaPicker.tsx`, `state/persona.tsx`, `i18n/strings.ts`, and `api/decision.ts` to Vedanta titles (removing `CMD` / ONGC).
- [ ] **[C7.3 · Verify]** `[O]` Confirm zero `ONGC`/`CMD` tokens in persona/i18n modules and `npx tsc --noEmit` exits `0`. · *Evidence:* `pending`

- [ ] **[C7.4 · Impl]** `[F]` Update `frontend/scripts/{build_architecture,architecture_explain}.py` for Barmer fields & Vedanta target enterprise sources (`[verify]`) and regenerate `frontend/public/architecture/*` (`[O]` review).
- [ ] **[C7.4 · Verify]** `[O]` Run `build_architecture.py` and confirm zero ONGC/Assam/WellPulse project tokens in `frontend/public/architecture/`. · *Evidence:* `pending`

- [ ] **[C7.5 · Impl]** `[O]` Compile production frontend bundle (`cd frontend && npm run build`).
- [ ] **[C7.5 · Verify]** `[O]` Confirm `npm run build` exits `0` and `grep -ri "ongc" frontend/dist/` finds `0` matches. · *Evidence:* `pending`

- [ ] **[C7.6 · Impl]** `[F]` Update `README.md` (preserving isolation banner), `docs/how_urvi_works.md`, `docs/ml_recommendation_engine.md` (exact Barmer ML metrics), and `docs/data_access_plan.md` (`[O]` review).
- [ ] **[C7.6 · Verify]** `[O]` Confirm zero `Geleki`/`Lakwa`/`Lakhmani`/`Sivasagar`/`GK-129` strings in those 4 docs. · *Evidence:* `pending`

### Gate C7 Sign-Off
- [ ] **Gate C7 Passed:** Frontend UI, India/Barmer GIS map, voice screen controls, Vedanta personas, Architecture tab, `frontend/dist/`, and core docs compiled cleanly with zero ONGC leaks (`backlog_refinements.md` updated).

---

## Stage C8 · Full Test Suite, Golden Schemas, Eval Migration & Zero-ONGC Audit (Day 2 Eve)

- [ ] **[C8.1 · Impl]** `[A]` Update `backend/tests/golden/{routes,capture}.py` to Barmer targets (`MNG-042`, `BHG-019`, `ASH-023`) and recapture `backend/tests/golden/*.schema.json`.
- [ ] **[C8.1 · Verify]** `[O]` Confirm `python -m tests.golden.capture` exits `0` and zero `GK-`/`LKW-`/`LKM-`/`Assam` strings remain in `tests/golden/`. · *Evidence:* `pending`

- [ ] **[C8.2 · Impl]** `[A]` Migrate all 41 unit test modules in `backend/tests/unit/` (incl. `test_contracts_mangala.py` & `test_ed6_cairn_assets.py`) from Assam fixtures to Barmer equivalents (`[O]` review).
- [ ] **[C8.2 · Verify]** `[O]` Run `pytest tests/unit/ --ignore=tests/unit/test_bl12_all_wells.py -q` (`0` failures). · *Evidence:* `pending`

- [ ] **[C8.3 · Impl]** `[O]` Update & run `backend/tests/unit/test_bl12_all_wells.py` across all **460 Barmer wells**.
- [ ] **[C8.3 · Verify]** `[O]` Confirm `pytest tests/unit/test_bl12_all_wells.py -q` passes `460/460` wells (`0.05 <= p_success <= 0.95`, zero currency tokens). · *Evidence:* `pending`

- [ ] **[C8.4 · Impl]** `[A]` Migrate `backend/tests/integration/{test_backend_parity,test_demo_flow}.py` and `backend/tests/bdd/{test_agent_bdd.py,features/*.feature}` to Barmer fields & hero wells (`[O]` review).
- [ ] **[C8.4 · Verify]** `[O]` Run `pytest tests/integration/ tests/bdd/ -q` (`0` failures, including BigQuery parity against `urvi_cairn_silver`). · *Evidence:* `pending`

- [ ] **[C8.5 · Impl]** `[F]` Migrate `backend/tests/eval/{README.md,canvas_routing_v05.json,wellpulse-eval.json,datasets/v04-dataset.json}` to Barmer wells & clean legacy ONGC eval results (`[O]` review).
- [ ] **[C8.5 · Verify]** `[O]` Confirm valid JSON parsing and zero ONGC/Assam tokens across all eval datasets. · *Evidence:* `pending`

- [ ] **[C8.6 · Impl]** `[O]` Execute full backend `pytest` suite and repo-wide zero-ONGC runtime/UI leak audit.
- [ ] **[C8.6 · Verify]** `[O]` Confirm `uv run pytest -q` (`0` failures) AND repo-wide grep across `backend/app/`, `frontend/src/`, `frontend/public/`, `lakehouse/dataform/` returns `0` hits. · *Evidence:* `pending`

### Gate C8 Sign-Off
- [ ] **Gate C8 Passed:** Full `pytest` suite green (incl. 460-well stress test & BigQuery parity) and strict zero-ONGC audit passed (`backlog_refinements.md` updated).

---

## Stage C9 · Local Rehearsal, Cloud Run Deployment & CIO Demo Script (Day 3)

- [ ] **[C9.1 · Impl]** `[O]` Update `deploy/selfcheck.py` & `run_local.sh` for Cairn Barmer endpoints (`460` wells, `MNG-042` recommendations & Cairn report, `/ws/live`).
- [ ] **[C9.1 · Verify]** `[O]` Start local uvicorn server on `:8002`, pass 7/7 `selfcheck.py` checks, and stop cleanly. · *Evidence:* `pending`

- [ ] **[C9.2 · Impl]** `[F]` Author pinned 7-act Cairn CIO Demo Script (`docs/demo_flow.md`) and `docs/pinned_values.md` (`[O]` number-pin audit against live tool outputs).
- [ ] **[C9.2 · Verify]** `[O]` Confirm `demo_flow.md` & `pinned_values.md` contain `MNG-042` / `BHG-019` / `RAG-014` pinned numbers and zero ONGC/Assam strings. · *Evidence:* `pending`

- [ ] **[C9.3 · Impl]** `[O]` **`[USER GATE]`** After explicit user OK, run `bash deploy/deploy.sh build` and `bash deploy/deploy.sh deploy` to deploy `urvi-cairn-app` (`us-central1`, `urvi-cairn-barmer-ai-agent`).
- [ ] **[C9.3 · Verify]** `[O]` Confirm `gcloud run services describe urvi-cairn-app` shows ready URL & revision in `us-central1`. · *Evidence:* `pending`

- [ ] **[C9.4 · Impl]** `[O]` Run live Cloud Run smoke test (`bash deploy/deploy.sh smoke`) and record live URL & revision in `APP_LINK.md` and `backlog_refinements.md`.
- [ ] **[C9.4 · Verify]** `[O]` Confirm `deploy.sh smoke` passes 7/7 against live `https://urvi-cairn-app-...` URL and `APP_LINK.md` is updated. · *Evidence:* `pending`

- [ ] **[C9.5 · Impl]** `[O]` **`[USER GATE]`** After explicit user OK, perform final audit of `docs/checklist.md` + `../wellpulse` untouched check, commit, and push to `origin/main`.
- [ ] **[C9.5 · Verify]** `[O]` Confirm 100% of `C0`–`C9` steps checked `[x]`, `../wellpulse` untouched, and `origin/main` up to date. · *Evidence:* `pending`

### Gate C9 Sign-Off
- [ ] **Gate C9 Passed:** `urvi-cairn-app` live on Cloud Run, 7/7 smoke green, CIO demo script rehearsed & pinned, and repo synced.
