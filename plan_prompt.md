# Plan prompt: Urvi for Cairn Oil & Gas (Barmer Basin)

_Paste the prompt below into a new chat to start the Cairn work. Written 2026-11-15; the Cairn CIO meeting is 3 days away (2026-11-18)._

---

**Context.** I'm working exclusively in `/usr/local/google/home/amandeepsinghs/o&g agentic transformation/Oil & Gas Agent Portfolio/cloud_run_apps/urvi_cairn_barmer`. It's a full replica, with git history, of my ONGC "Urvi AI Agent on WellPulse" demo, made for **Cairn Oil & Gas (Vedanta Oil and Gas Ltd), Barmer Basin, Rajasthan**. **Never touch** the ONGC repo `../wellpulse` or the ONGC Google Cloud project `workover-operations-agentic-ai`. Read `backlog_refinements.md` and the README banner first.

**Goal (deadline: Cairn CIO meeting in 3 days).** Keep **everything the same as the ONGC app**: features, UI, voice, agent, tools, recommendation engine, architecture tab, docs structure. **Only the data changes:** generate synthetic Barmer data, push it to GCS and BigQuery in the Cairn project, retrain the models on it, and deploy a working app so that talking to Urvi feels like talking about their own fields.

**Current state.** The replica is locked down:
- GitHub remote `amandeepsinghs-cyber/urvi-cairn-barmer`
- Google Cloud project `urvi-cairn-barmer-ai-agent`: service `urvi-cairn-app`, bucket `urvi-cairn-barmer-ai-agent-datalake`, BigQuery datasets `urvi_cairn_bronze/silver/gold`, runtime SA `urvi-cairn-run`
- `deploy/deploy.sh` refuses ONGC targets
- **Everything is uncommitted and nothing is pushed.**
- In the Cairn project, BigQuery, Dataform, Dataplex and Storage are on. **Cloud Run, Cloud Build, Artifact Registry, Vertex AI and IAM are still off.**

**Scope: what to change.**
1. **Fields and data:**
   - Replace Geleki / Lakwa / Lakhmani with **Mangala, Bhagyam, Aishwariya** (plus a 4th if sensible, e.g. Raageshwari gas or a satellite field).
   - New field configs in the generator, with realistic synthetic well counts, clusters / well pads, coordinates in the Barmer area, formations, and lift mix (e.g. ESP, jet pump, PCP, SRP).
   - Waxy crude (wax and hot-oil jobs, heated flowlines), polymer flood behaviour, water-cut trends, workover catalogue and outcomes.
   - Same 60-month window and the same tables as today, including the document corpus (completion reports, workover reports, SOPs) and the extra synthetic tables (tubing tally, deviation, integrity).
   - Calibrate to **public** facts only. Mark anything uncertain **[verify]**.
   - Everything is labelled synthetic.
2. **Data platform:** load the landing data and documents to `gs://urvi-cairn-barmer-ai-agent-datalake` (`bronze/`, `documents/`), apply the DDL, run Bronze → Silver → Gold (MERGE, Dataform) in `urvi_cairn_*` (asia-south1).
3. **Models:**
   - Rebuild features for the new fields and lift types; the feature code currently hard-codes the Assam fields, zones and lift types.
   - Retrain the intervention classifier and the failure model, and rebuild the look-alike index.
   - Keep the same pass/fail gates; never tune just to pass. Pin new demo wells for the story.
4. **App identity:**
   - Urvi's prompts and voice prompt become "Urvi AI Agent for Cairn Oil & Gas, Barmer"; **no ONGC name or logo anywhere**.
   - The India map shows Vedanta / Cairn assets (public approximate locations) instead of ONGC assets.
   - Update the screen-command field list, field selector and greetings (English default).
   - Field report branding: Cairn / Vedanta if an approved logo is available, else a text wordmark.
   - Update the architecture diagrams and Explain text (Barmer fields; the Target view's data sources become Vedanta's systems, generic unless confirmed).
   - Update docs: README, `how_urvi_works.md`, `ml_recommendation_engine.md` numbers, demo script.
5. **Tests:** replace tests and fixtures pinned to Assam wells (e.g. GK-129) with equivalent Barmer demo wells. The suite must be green, plus the all-wells recommendation test.
6. **Deploy:**
   - Enable the missing APIs and create the service account (`deploy.sh iam`).
   - Build, deploy and run the smoke test to `urvi-cairn-app` (us-central1, because Gemini Live isn't available in India; demo data is synthetic).

**Delegation (my requirement).** Data generation is done by **Argon and Gemini Flash** workers under a clear delegation plan, following the pattern in `docs/DELEGATION.md`:
- **Argon:** generators and consistency tests.
- **Flash:** document templates and prose.
- **You (orchestrator):** architecture, leakage rules, gates and review.

**Plan for 3 days** (propose adjustments, then I approve once and you execute in batches):
- **Day 1:** the Barmer data strategy (one page: fields, well counts, lift mix, phenomena, demo hero wells with their story) + delegation plan → I approve → generate the data, validate it, push to GCS and BigQuery.
- **Day 2:** retrain the models and pass the gates; swap app identity (prompts, map, branding, field lists); update tests; local run.
- **Day 3:** deploy, smoke test, **demo script for the CIO** (Barmer storyline: field compare → sick wells → priority list → a hero well → recommendation → why-not → field report → architecture), rehearse, fix.

**Rules.**
- Discuss the plan before executing; after I approve, batch the work.
- Never commit, push or deploy without my explicit OK.
- Never touch the ONGC repo or project.
- Log every change in `backlog_refinements.md` (latest changes, refinements, backlog).
- Communicate answer first and concise, with risks called out.

**First, before anything else:**
1. Confirm the current state.
2. Ask me for OK to commit and push the lockdown as the first commit.
3. Ask me for OK to enable the missing APIs.
4. Propose the Barmer data strategy and delegation plan.

Open question from me: keep the agent name "**Urvi**" (default: yes).

---

## Notes
- **Biggest risk:** the model retraining gates on new data. If a gate fails, report it; never tune to pass.
- **Local run:** stop any dev server still running from the ONGC folder (ports 5180 / 8002) before running this copy locally.
