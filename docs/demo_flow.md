# Urvi — Cairn Oil & Gas (Vedanta Limited) CIO / COO Demo Script

> [!IMPORTANT]
> **Single-Agent, Multi-Tool Hybrid Architecture:** *Natural spoken & typed language in via Gemini ADK / Live → deterministic Python physics, offline ML models & numeric-grounding guards underneath — best of both worlds with minimal hallucination.*
>
> **Strict Chat Guardrails:**
> - **≤ 3–4 sentences per turn:** Chat remains crisp and executive-ready; full tables, timelines, CBL scans, and wellbore completions render on the right-hand canvas rather than dumping multi-section histories into chat.
> - **Zero currency:** No `₹` or USD point estimates in chat or UI; interventions use qualitative `LOW` / `MED` / `HIGH` cost bands and net BOPD / downtime metrics.
> - **Value from tool:** Every numeric figure (`P(success)`, BOPD rate, WHT, decline %, days of wait) is populated dynamically by backend analytical tools (`value from tool`) and verified by the post-model numeric-grounding guard (`AS_OF = 2026-09-23`, completely synthetic dataset).

---

## Portfolio & Map Setup (Before Starting)

- **Target Service:** `urvi-cairn-app` (GCP project `urvi-cairn-barmer-ai-agent`, region `us-central1`). Local fallback: `bash run_local.sh` on `:5180`.
- **India Portfolio Opening View:** Opens at India zoom showing **4 Cairn / Vedanta upstream blocks**:
  1. **Barmer (`Block RJ-ON-90/1`, Rajasthan)** — active, clickable live basin hub.
  2. **Ravva (`PKGM-1`, Andhra Pradesh offshore)** — non-clickable position marker.
  3. **Cambay (`CB/OS-2`, Gujarat offshore)** — non-clickable position marker.
  4. **Jorhat OALP (`AA-ONHP-2017/1`, Assam)** — non-clickable position marker.
- **Barmer Basin Scope:** Drilling into `Block RJ-ON-90/1` loads **460 synthetic wells** across four fields — **Mangala (`180`)**, **Bhagyam (`120`)**, **Aishwariya (`100`)**, and **Raageshwari (`60`)** — plus **MPT Nagana** (`MPT-NAGANA`) and **Raageshwari Gas Terminal** (`RGT-TERMINAL`).
- **Pre-Demo Check:** Confirm the right pane sits on the Map / Portfolio view (`India` zoom) and audio/mic permissions are granted if running Gemini Live voice.

---

## Part 1 — 11-Step Drill-Down Matrix (+ Case 12 Guardrail)

The canonical narrative moves top-down: **Portfolio Field Comparison → Underperforming Field (`Bhagyam`) → Cross-Basin Priority Queue → Hero Well Deep-Dive (`MNG-042`) → Diagnosis → Top-3 ML/Physics Recommendation → Counterfactual Defense (+ `RAG-014` Safety Veto) → Printable Cairn A4 Field Report**.

| Step | Stage | User Prompt | Expected Tool Call(s) | Target Canvas Tab | Key Verified Output / Canvas Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Field Compare | *"Compare Bhagyam with Mangala and other Barmer fields"* | `compare_fields` | `compare` | **Bhagyam `-17.7%`** QTD target gap vs **Mangala `+0.9%`**, **Aishwariya `-3.5%`**, **Raageshwari `-1.4%`**. |
| **2** | Sick Wells | *"Which wells in Bhagyam are sick?"* | `classify_well_health`, `attribute_decline` | `overview` | Flags Bhagyam sick/amber cohort: trace-heater waxy crude choking (`42°C` pour point / `59°C` WAT), PCP wear, `BHG-PAD-2` 33kV feeder outages, and rig waits (`BHG-019`, `BHG-088`). |
| **3** | Priority List | *"Show priority list of wells needing intervention"* | `rank_candidates` | `interventions` | Cross-field priority worklist across Mangala / Bhagyam / Aishwariya ranked by expected incremental oil, lift criticality, and cost band (`value from tool`). |
| **4** | Well Overview | *"Tell me about MNG-042"* | `well_profile` | `overview` | **`MNG-042`** (`Mangala`, `MNG-PAD-B`, `Fatehgarh_Lower`, Hydraulic `JET_PUMP`), current status, BOPD/water-cut KPIs, and recent anomaly badge (`value from tool`). |
| **5** | Production | *"Show production history for MNG-042"* | `plot_production` | `production` | Dual-axis BOPD vs water-cut / polymer-cut and wellhead temperature trend showing steep water/polymer breakthrough (`value from tool`). |
| **6** | Past Interventions | *"Show past interventions for MNG-042"* | `well_profile` | `interventions` | Workover timeline citing `WO-MNG-042-2019` failed `STRADDLE_PACKER` (`DOC-SCAN-MNG-042-2019`) and 2014 primary cement log (`DOC-CBL-MNG042-2014`). |
| **7** | Wellbore | *"Show wellbore diagram and completion details for MNG-042"* | `well_profile` | `wellbore` | Interactive tubulars, `JET_PUMP` BHA, perforations across `Fatehgarh_Lower` FM4/FM3 intervals, and CBL micro-annulus channel flag. |
| **8** | Diagnosis | *"Why is production declining on MNG-042?"* | `attribute_decline` | `diagnosis` | **HPAM polymer / water channelling** behind poorly cemented FM4/FM3 shale barrier (`WOR'` slope `> +0.30`), corroborated by `DOC-CBL-MNG042-2014` & `DOC-SCAN-MNG-042-2019`. |
| **9** | Recommendation | *"What should we do for MNG-042?"* | `recommend_next_best_action` | `recommendation` | **Top-3 card:** Rank 1 `CEMENT_SQUEEZE` (`IC-11`), Rank 2 `POLYMER_GEL`, **rejecting `CHOKE_BACK ✘`**; shows `ST-3` analogs & `ST-4` calibrated `P(success)` (`value from tool`). |
| **10** | Counterfactual | *"Why not wax removal for MNG-042?"* | `compare_interventions` | `compare` | Explains why `CEMENT_SQUEEZE` beats `WAX_HOTOIL` — WHT is normal and `DOC-CBL-MNG042-2014` + `DOC-SCAN-MNG-042-2019` prove zonal channelling, not wellbore wax (`value from tool`). *(Optional `RAG-014` safety veto follow-up below.)* |
| **11** | Field Dossier | *"Prepare me for the field"* | `build_well_dossier` (`/api/wells/MNG-042/report`) | `report` / A4 Print | Generates printable **Cairn Oil & Gas · Vedanta** A4 dossier (`/brand/cairn_vedanta_wordmark.svg`) with completion, diagnosis, SOP `IC-11`, and citations. |
| **12** | Guardrail Case | *"Tell me about MNG-042 and dump full history"* | `well_profile` only (`forbidden_tools: build_well_dossier`) | `overview` | Enforces `≤ 3–4 sentences` chat guardrail: summarizes `MNG-042` concisely and opens `overview` without dumping history or calling `build_well_dossier`. |

---

### Detailed Step Walkthroughs

#### Step 1 — Field Compare
- **Prompt:** *"Compare Bhagyam with Mangala and other Barmer fields"*
- **What Happens:** `compare_fields` renders side-by-side QTD oil vs target across all 4 Barmer fields (`compare` tab).
- **Executive Talking Point:** *"Across our 460 Barmer wells, Mangala is tracking `+0.9%` above target, Raageshwari is `-1.4%`, and Aishwariya is `-3.5%`, while **Bhagyam is lagging at `-17.7%` QTD**. We immediately isolate where management attention belongs."*

#### Step 2 — Sick Wells in Bhagyam
- **Prompt:** *"Which wells in Bhagyam are sick?"*
- **What Happens:** `classify_well_health` and `attribute_decline` filter Bhagyam (`120` wells) down to its impaired cohort (`overview` tab).
- **Executive Talking Point:** *"Bhagyam's `-17.7%` shortfall concentrates around four deterministic failure patterns: waxy crude trace-heater drops below Barmer's `42°C` pour point / `59°C` WAT, progressive cavity pump (PCP) wear, `BHG-PAD-2` 33kV feeder outages, and rig/material mobilization waits."*

#### Step 3 — Cross-Basin Priority List
- **Prompt:** *"Show priority list of wells needing intervention"*
- **What Happens:** `rank_candidates` evaluates active sick/amber wells across Barmer and displays the ranked workover queue (`interventions` tab, `value from tool` scores and `LOW`/`MED`/`HIGH` cost bands).
- **Executive Talking Point:** *"Rather than working the loudest ticket, Urvi ranks candidates by recoverable oil, failure mechanism confidence, and execution readiness — zero rupee guesses in chat, deterministic physics and calibrated `P(success)` underneath."*

#### Steps 4–7 — Hero Well Deep-Dive (`MNG-042`)
Run sequentially or jump directly via voice/text:
- **Step 4 (`well_profile` → `overview`):** *"Tell me about MNG-042"* → `Mangala`, pad `MNG-PAD-B`, `Fatehgarh_Lower`, Hydraulic `JET_PUMP` producer (`value from tool` rate, water cut, status).
- **Step 5 (`plot_production` → `production`):** *"Show production history for MNG-042"* → Visualizes the oil decline vs accelerating water/polymer cut (`value from tool`).
- **Step 6 (`well_profile` → `interventions`):** *"Show past interventions for MNG-042"* → Surfaces `WO-MNG-042-2019` (a failed `STRADDLE_PACKER` documented in scanned ticket `DOC-SCAN-MNG-042-2019`) alongside the 2014 cement bond log (`DOC-CBL-MNG042-2014`).
- **Step 7 (`well_profile` → `wellbore`):** *"Show wellbore diagram and completion details for MNG-042"* → Renders casing strings, `JET_PUMP` string, `Fatehgarh_Lower` FM4/FM3 perforations, and the compromised annular cement interval.

#### Step 8 — Root-Cause Diagnosis (`MNG-042`)
- **Prompt:** *"Why is production declining on MNG-042?"*
- **What Happens:** `attribute_decline` evaluates Chan diagnostic slopes (`WOR'` slope `> +0.30`), surface temperature stability, and historical CBL/scan documents (`diagnosis` tab).
- **Executive Talking Point:** *"This is not near-wellbore wax or jet-pump wear. `WOR'` slope `> +0.30`, `DOC-CBL-MNG042-2014`, and the failed `WO-MNG-042-2019` straddle packer (`DOC-SCAN-MNG-042-2019`) point directly to **HPAM polymer / water channelling** behind the poorly cemented FM4/FM3 shale barrier."*

#### Step 9 — Top-3 Recommendation (`MNG-042`)
- **Prompt:** *"What should we do for MNG-042?"*
- **What Happens:** `recommend_next_best_action` surfaces the top-3 table on the `recommendation` tab:
  - **Rank 1:** `CEMENT_SQUEEZE` (`IC-11`) — isolates the annular channel across FM4/FM3.
  - **Rank 2:** `POLYMER_GEL` (`IC-11`) — secondary gel conformance option.
  - **Rejected:** `CHOKE_BACK ✘` — explicitly suppressed because choking back cannot seal an annular behind-casing channel.
  - Shows `ST-3` historical analogs and `ST-4` calibrated `P(success)` and expected uplift (`value from tool`).

#### Step 10 — Counterfactual Defense (+ Optional `RAG-014` Safety Veto)
- **Prompt (Primary):** *"Why not wax removal for MNG-042?"*
- **What Happens:** `compare_interventions` contrasts `CEMENT_SQUEEZE` (`IC-11`) vs `WAX_HOTOIL` (`IC-04`) on `compare` (`value from tool`), citing `DOC-CBL-MNG042-2014` and `DOC-SCAN-MNG-042-2019` to prove hot-oiling treats the tubing string while leaving the behind-casing polymer/water channel untouched.
- **Optional Safety Veto Follow-Up (`RAG-014`):** *"What should we do on RAG-014, and why not hydraulic fracturing?"*
  - **What Happens:** Demonstrates Urvi's two-gate safety discipline on `Raageshwari` tight gas (`RAG-RDG-S`, `Raageshwari_Volcanics`, `NATURAL`):
    1. **Reservoir-Depletion Gate (`G-2`):** `RAG-014` shows `-63.9%` decline mirrored across offset neighbors `RAG-030`, `RAG-010`, `RAG-047`, and `RAG-060` (max offset residual `<= 5.0 pp`), recommending **`NO_JOB_JUSTIFIED`**.
    2. **Well-Integrity Gate:** Latest `ANNULUS` record in `barrier_tests` is **`FAIL`**, hard-blocking `IC-09` `HYDRAULIC_FRAC` regardless of stimulation upside.

#### Step 11 — Printable Cairn A4 Field Report
- **Prompt:** *"Prepare me for the field"*
- **What Happens:** Calls `build_well_dossier` / `/api/wells/MNG-042/report` and renders the print-ready A4 dossier branded with `/brand/cairn_vedanta_wordmark.svg` (**Cairn Oil & Gas · Vedanta Limited**), complete with wellbore schematic, `IC-11` execution checklist, and linked CBL/scan evidence.

#### Case 12 — Negative Guardrail Validation
- **Prompt:** *"Tell me about MNG-042 and dump full history"*
- **Expected Behavior:** Model uses `well_profile` only (`overview`), must **NOT** invoke `build_well_dossier`, and honors the **≤ 3–4 sentence** chat ceiling.

---

## Part 2 — CIO / COO Rehearsal Script (`2026-11-18`)

**Runbook Goal:** ~10–12 minutes total — 4 minutes hands-free Voice & Map Choreography (**Part A**), 6 minutes Technical, Physics & Counterfactual Q&A (**Part B**), 2 minutes Architecture & Production Close.

### Pre-Flight Setup (`T - 10 min`)
1. Open `urvi-cairn-app` in Chrome (`1440×900` or full display) with `India` zoom visible showing the **4 Cairn / Vedanta upstream blocks** (`Barmer RJ-ON-90/1` active; `Ravva`, `Cambay`, `Jorhat OALP` tagged).
2. Verify mic input for Gemini Live (`English` default) and keep keyboard ready for silent `uiCommands` fallback if room audio has echo.
3. Confirm persona badge reflects `COO / CIO` (`ED`) and synthetic banner is visible.

---

### Part A — Hands-Off Voice & UI Choreography (~4 min)

Run in sequence, pausing ~2s after each canvas transition for executives to read the UI:

| # | Spoken Voice Command | Expected UI / Agent Action | What to Point Out |
| :--- | :--- | :--- | :--- |
| **A1** | *"Hello Urvi"* / *"Who are you?"* | Greets in **English** by default (`≤ 3` sentences): introduces Urvi as Cairn Oil & Gas's Barmer Basin (`RJ-ON-90/1`) well-intervention & surveillance agent. | Instant voice response + single-agent ADK orchestration. |
| **A2** | *"Take me to Barmer"* *(or `"Barmer dikhao"`)* | Smooth zoom from India portfolio into **Barmer Basin (`460` wells)** across Mangala, Bhagyam, Aishwariya, Raageshwari + `MPT-NAGANA` & `RGT-TERMINAL`. | Four Cairn blocks at portfolio level; live telemetry & facilities inside Barmer. |
| **A3** | *"Only show non producing wells"* → *"Only show healthy wells"* → *"Show all wells"* | Filters map pins live: `red` (sick) → `green` (healthy) → all `460` wells restored. | Sub-second deterministic UI command path without LLM round-trip delay. |
| **A4** | *"Show MNG-PAD-B"* | Flies to pad `MNG-PAD-B` in Mangala and opens the **pad popup** listing health-tagged well buttons. | Pad-level grouping mirrors how Barmer field engineers dispatch crews. |
| **A5** | *(Optional click)* Click a red/amber well button inside `MNG-PAD-B` popup | Selects that well in the right-hand inspector while keeping map context. | Seamless voice + mouse multimodal control. |
| **A6** | *"Full screen"* → *"SCADA map"* → *"Satellite"* → *"Exit full screen"* | Expands map, switches to **SCADA** schematic overlay (`MPT-NAGANA`, `RGT-TERMINAL`, gathering lines), toggles **Satellite** imagery, then returns to split layout. | Surface facility topology meets satellite pad imagery. |
| **A7** | *"Open MNG zero four two wellbore"* | Loads `MNG-042` directly onto the **`wellbore` completion diagram** (`Fatehgarh_Lower`, `JET_PUMP`, FM4/FM3 perforations). | Natural spoken well ID parsing (`zero four two` → `MNG-042`). |
| **A8** | *(Optional)* *"Hindi mein baat karo"* | Switches Gemini Live spoken persona to natural Hindi / Hinglish for field-crew accessibility (switch back with *"Speak in English"*). | Multilingual inclusion for Rajasthan pad operators and engineers. |
| **A9** | *"Print the report"* | Opens the **Cairn Oil & Gas · Vedanta** A4 Field Report (`/api/wells/MNG-042/report`) and triggers browser print preview (`Cancel` after showing). | Ready-to-execute SOP `IC-11` pack for the rig / slickline supervisor. |
| **A10** | *"Show me the architecture"* → *"Show the target architecture"* | Opens Architecture modal/tab pointing directly to the top-line **Single-Agent, Multi-Tool Hybrid Architecture** banner, then switches to **Vedanta `asia-south1` Lakehouse** target state. | Clear path from synthetic Cloud Run pilot to Vedanta Lakehouse & PI/SAP integration. |

---

### Part B — Technical, Physics & Counterfactual Questions (`AS_OF = 2026-09-23`, ~6 min)

Ask live via voice or chat box; verify every cited figure matches the tool output (`value from tool`):

1. **Portfolio Triage (`Bhagyam` vs Basin):**
   - **Ask:** *"Compare Bhagyam with Mangala and other Barmer fields, and show which wells in Bhagyam are sick."*
   - **Look For:** `Bhagyam -17.7%` QTD target gap vs `Mangala +0.9%`, `Aishwariya -3.5%`, `Raageshwari -1.4%`; highlights waxy crude trace-heater choking (`42°C` pour point / `59°C` WAT), PCP wear, `BHG-PAD-2` power outages, and mobilization waits.

2. **Channelling vs Wax Counterfactual (`MNG-042` — Mangala, `MNG-PAD-B`, `Fatehgarh_Lower`, `JET_PUMP`):**
   - **Ask:** *"Why is production declining on MNG-042, what should we do, and why not wax removal?"*
   - **Look For:** Diagnoses HPAM polymer / water channelling behind poorly cemented FM4/FM3 shale (`WOR'` slope `> +0.30`), citing `DOC-CBL-MNG042-2014` and failed `WO-MNG-042-2019` `STRADDLE_PACKER` (`DOC-SCAN-MNG-042-2019`). Recommends Rank 1 `CEMENT_SQUEEZE` (`IC-11`), Rank 2 `POLYMER_GEL`, rejects `CHOKE_BACK ✘`, and proves why `WAX_HOTOIL` fails against annular channelling (`value from tool`).

3. **Surface Bottlenecks + Cold-Crude Choking (`BHG-019` — Bhagyam, `BHG-PAD-1`, `Fatehgarh_Upper`, `PCP`):**
   - **Ask:** *"Walk me through BHG-019 — why did it stay down so long and why did it drop again after restart?"*
   - **Look For:** Separates **non-productive wait time** (`38d` rig wait + `11d` material wait before `PUMP_OVERHAUL`) from the subsequent **trace-heater failure**, which caused waxy crude cooling — wellhead temperature dropped to **`40.8°C`** (below Barmer's `42°C` pour point / `59°C` WAT) and oil fell **`67%`** (`value from tool`).

4. **Electrical Power / SCADA Correlation (`BHG-088` — Bhagyam, `BHG-PAD-2`, `ESP`):**
   - **Ask:** *"Why is BHG-088 tripping repeatedly — is it downhole ESP wear or surface power?"*
   - **Look For:** Correlates downtime timestamps directly to scripted **`BHG-PAD-2` 33kV feeder outages**, preventing an unnecessary ESP pull (`IC-01`) when feeder restoration is the root fix (`value from tool`).

5. **Sand Influx vs Gas-Lift/Wax Compound Fault (`ASH-023` & `ASH-061` — Aishwariya):**
   - **Ask:** *"Compare what ASH-023 needs versus ASH-061 in Aishwariya."*
   - **Look For:**
     - **`ASH-023`** (`ASH-PAD-1`, `Fatehgarh_Upper`, `JET_PUMP`): sand influx diagnosis → **`IC-06` `SAND_CLEANOUT`** (`value from tool`).
     - **`ASH-061`** (`ASH-PAD-2`, `Fatehgarh_Lower`, `JET_PUMP`): compound **`GLV_PLUS_WAX`** signature → top-2 pair `{IC-07 Jet-Pump / gas-lift valve insert, IC-04 wax remediation}` (`value from tool`).

6. **Integrity Veto & "Do Nothing" Discipline (`RAG-014` — Raageshwari, `RAG-RDG-S`, `Raageshwari_Volcanics`, `NATURAL`):**
   - **Ask:** *"What should we do on RAG-014, and why shouldn't we run a multi-stage hydraulic frac?"*
   - **Look For:** Two independent safeguards:
     - **Reservoir-Depletion Gate (`G-2`):** `-63.9%` decline matches offset neighbors **`RAG-030`, `RAG-010`, `RAG-047`, `RAG-060`** (max offset residual `<= 5.0 pp`) → **`NO_JOB_JUSTIFIED`**.
     - **Barrier Veto:** Latest `ANNULUS` `barrier_tests` status is **`FAIL`**, hard-blocking **`IC-09` `HYDRAULIC_FRAC`** (`value from tool`).

---

## Pass Criteria (Rehearsal Sign-Off)

- [ ] All 4 Cairn / Vedanta India blocks render on initial load; clicking Barmer displays 460 wells + `MPT-NAGANA` + `RGT-TERMINAL`.
- [ ] Zero raw-number or currency hallucinations in chat; every figure matches tool output (`value from tool`) and stays within `≤ 3–4 sentences`.
- [ ] All Part A voice/UI transitions execute cleanly (`MNG-PAD-B` popup, SCADA/Satellite toggle, `MNG-042` wellbore, Cairn A4 report, Architecture target tab).
- [ ] `MNG-042` cites `DOC-CBL-MNG042-2014` & `DOC-SCAN-MNG-042-2019` and rejects `CHOKE_BACK ✘` / `WAX_HOTOIL`.
- [ ] `BHG-019` (`38d` + `11d`, `40.8°C`, `67%` drop), `BHG-088` (`BHG-PAD-2` 33kV feeder), `ASH-023` (`IC-06`), `ASH-061` (`{IC-07, IC-04}`), and `RAG-014` (`-63.9%`, `NO_JOB_JUSTIFIED`, `ANNULUS` `FAIL` veto on `IC-09`) all resolve deterministically.
- [ ] Case 12 negative guardrail does **not** call `build_well_dossier` or dump full history into chat.

---

## Fallback & Rollback Playbook

### Live Voice / Network Fallback
- **Voice mic drop or conference-room echo:** Immediately type the exact Part A/B commands into the agent chat box — local deterministic UI command routing (`uiCommands.ts`) and text Gemini ADK use the identical tool pipeline without audio capture.
- **Live Cloud Run latency:** Switch to the pre-warmed local container (`bash run_local.sh` at `http://localhost:5180`).

### Cloud Run Revision Rollback (`urvi-cairn-app`)
If a freshly pushed revision regresses before the CIO/COO session, list healthy revisions and shift 100% traffic back to the last verified revision:

```bash
gcloud run revisions list \
  --service urvi-cairn-app \
  --project urvi-cairn-barmer-ai-agent \
  --region us-central1

gcloud run services update-traffic urvi-cairn-app \
  --project urvi-cairn-barmer-ai-agent \
  --region us-central1 \
  --to-revisions <LAST_VERIFIED_REVISION>=100
```

---

## If Asked — Executive Q&A Cheat Sheet

| Question | Concise Answer |
| :--- | :--- |
| **Why a Single-Agent, Multi-Tool Hybrid instead of multi-agent or RAG-only?** | One Gemini ADK / Live agent handles spoken/typed intent cleanly (`< 1` orchestration hop), while deterministic Python physics (`WOR'` slope, `G-2` depletion gate, `barrier_tests` veto) and offline ML (`ST-4`) compute every number — eliminating arithmetic hallucination and ungrounded prose. |
| **Is any of this real Cairn / Vedanta proprietary data?** | **No.** All 460 wells, production curves, SCADA trips, CBLs, and SOP workovers (`AS_OF = 2026-09-23`) are synthetic proxies built strictly from public Barmer literature (`42°C` pour point / `59°C` WAT, HPAM polymer flooding, `Fatehgarh` / `Barmer_Hill` / `Raageshwari_Volcanics`). |
| **How does role-based access control work for field vs leadership?** | Configured via `WELLPULSE_RBAC_ENFORCE=1` across three Cairn personas: **`COO / CIO` (`ED`)** (portfolio + cross-field triage), **`Asset Manager — Barmer` (`ASSET_MANAGER`)** (field-scoped approvals & rig queues), and **`Production / Well Services Engineer` (`FIELD_ENGINEER`)** (pad/wellbore execution & A4 SOP packs). |
| **How do we move from synthetic Cloud Run to Vedanta production?** | Click **"Show the target architecture"** in the Architecture view: swap the synthetic `landing/` parquet adapters for read-only views on **Vedanta's `asia-south1` Lakehouse** (OSIsoft PI SCADA, SAP PM workovers, OpenWells/EDM wellbore data) behind Vedanta IAM & VPC Service Controls — zero core agent rewrite required. |
| **Why are rupee / dollar estimates hidden in chat?** | Cost per barrel and rig contract rates vary by tender and JV partner split; keeping cost as deterministic `LOW` / `MED` / `HIGH` bands alongside incremental BOPD avoids false precision in executive briefings. |
