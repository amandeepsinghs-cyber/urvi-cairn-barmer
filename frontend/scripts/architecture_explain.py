"""Plain-English explanation of the Urvi architecture (BL-8 follow-up).

Single source of truth for:
* the **Explain** panel in the app's Architecture tab (``public/architecture/explain-{current,target}.json``), and
* ``docs/how_urvi_works.md``.

Badges match the diagrams: ① … main path (typed question), Ⓐ … voice path, D1 … data path.
Keep facts in sync with the code (agent/runner.py, live/voice_tools.py) and with docs/ml_recommendation_engine.md.
"""
from __future__ import annotations

# Each section: heading + optional "body" (paragraphs), "steps" (badge, title, text), "table" (cols, rows).
EXPLAIN: dict[str, dict] = {
    "current": {
        "title": "How Urvi works today (V 1.0 demo)",
        "intro": ("Urvi is one AI agent with a set of engineering tools. The AI model understands the question and "
                  "decides which tools to call; the tools do the calculations on well data; the model then explains "
                  "the result in a few sentences. The model never invents numbers."),
        "sections": [
            {
                "heading": "Three ways a request is handled",
                "table": {
                    "cols": ["You say or type", "What handles it", "AI involved?"],
                    "rows": [
                        ["A plain screen command, e.g. \"full screen\", \"GGS three dikhao\", \"show me the architecture\"",
                         "A rule-based parser in the browser changes the screen directly", "No"],
                        ["A typed question, e.g. \"Which field is underperforming?\"",
                         "The ADK agent: one agent on Gemini 3.8 Flash with 34 tools", "Yes"],
                        ["A spoken question (Live voice)",
                         "Gemini 3.8 Live through our Live proxy, with 13 voice tools (ADK is not used for voice)", "Yes"],
                    ],
                },
            },
            {
                "heading": "A typed question, step by step",
                "steps": [
                    ["1", "You ask", "You type in the Urvi panel. The browser checks whether it is a plain screen command; "
                     "if not, it sends the question to the Urvi API, with the screen context (field, well, language)."],
                    ["2", "Urvi API", "A Python web service (FastAPI) on Cloud Run receives the request at /api/chat. "
                     "It also serves the web app itself."],
                    ["3", "ADK agent", "The API hands the question to the agent, built with Google's Agent Development Kit "
                     "(ADK). There is one agent, named \"wellpulse\". Its instructions describe the 5-level drill-down "
                     "(field → health → priority list → well → next best action) and which tool answers what."],
                    ["4", "Gemini 3.8 Flash", "The agent sends the question and the tool list to Gemini. Gemini replies "
                     "with the tool(s) to call, e.g. compare_fields. After the tools run, it gets their results back and "
                     "writes a short answer (2–4 sentences)."],
                    ["5", "Tools", "Each tool is ordinary Python code: decline attribution, well health, ranking, next best "
                     "action, document search, and so on. Several tools can be called in one turn."],
                    ["6", "Well data", "The tools read the well tables (production, pressures, completion, job history) "
                     "through the data access layer. In the demo these are synthetic parquet files packed into the app."],
                    ["7", "Answer + screen", "The answer goes back to the browser together with screen actions, so the "
                     "matching view opens (chart, completion diagram, recommendation). A guard checks that every number "
                     "in the answer appears in a tool result; any other number is masked."],
                ],
            },
            {
                "heading": "A spoken question, step by step",
                "steps": [
                    ["A", "Audio in", "The browser streams your microphone (16 kHz) over a WebSocket to the Gemini Live "
                     "proxy on our server, and plays Urvi's spoken reply (24 kHz). You can interrupt at any time."],
                    ["B", "Gemini 3.8 Live", "The proxy connects to Gemini Live, a speech-to-speech model. It hears the "
                     "question, decides which voice tool to call, and speaks the answer (voice: Aoede). English by "
                     "default; Hindi or Hinglish if you switch."],
                    ["C", "Same tools", "Voice tools run on our server and call the same analytics code as chat. There "
                     "are fewer of them (13) because a voice model works best with a short list; some bundle several "
                     "chat tools, e.g. well_profile also returns offset decline, anomalies and wax / sand."],
                ],
            },
            {
                "heading": "Is it a multi-agent system?",
                "body": [
                    "No. Urvi is a single agent with many tools: one ADK agent for chat and one Gemini Live session for "
                    "voice. There are no sub-agents and no agent-to-agent hand-offs.",
                    "The design allowed splitting into specialist sub-agents if the agent picked the wrong tool too often "
                    "(below 90%). The evaluation scored 46 of 46 (100%), so one agent is enough.",
                    "How to say it: \"One Urvi agent with 34 engineering tools for chat, and the same tools through "
                    "Gemini Live for voice. Every number comes from deterministic tools, never from the model.\"",
                ],
            },
            {
                "heading": "Where the recommendations come from",
                "body": [
                    "The next-best-action tool combines physics checks (water diagnostics, pump signatures, offset wells, "
                    "pressure surveys), a trained intervention classifier, historical success rates and look-alike "
                    "wells, and returns a ranked top 3 with probability of success, expected gain, rig-days and the SOP.",
                    "Full explanation, with a worked example: docs/ml_recommendation_engine.md.",
                ],
            },
            {
                "heading": "Data, build and identity (the grey lines)",
                "body": [
                    "Data: a seeded generator creates 412 synthetic wells (Geleki, Lakwa, Lakhmani, 60 months). The app "
                    "reads parquet copies packed into the container; the same data also sits in a BigQuery medallion "
                    "lakehouse (Bronze → Silver → Gold) in Mumbai (asia-south1).",
                    "Build: Cloud Build builds the container image and stores it in Artifact Registry; Cloud Run runs "
                    "it as one instance (sessions are kept in memory).",
                    "Identity: Cloud Run runs as a dedicated service account and reaches Gemini and BigQuery without "
                    "API keys.",
                ],
            },
            {
                "heading": "Why the demo runs in the US region",
                "body": [
                    "Gemini Live is not yet offered in India regions, so the demo runs in us-central1. It uses only "
                    "synthetic data. The production design runs in India regions: see the Target view.",
                ],
            },
            {
                "heading": "Words used",
                "table": {
                    "cols": ["Term", "Meaning"],
                    "rows": [
                        ["Cloud Run", "Google's service that runs our container and scales it"],
                        ["ADK", "Agent Development Kit: Google's framework for building agents that call tools"],
                        ["Gemini 3.8 Flash", "The text model behind the chat agent"],
                        ["Gemini 3.8 Live", "The speech-to-speech model behind voice"],
                        ["Tool", "A Python function the model can call; it returns data, not prose"],
                        ["ui_control", "The tool that lets the agent change the screen (open a well, full screen …)"],
                        ["Medallion lakehouse", "Data in three layers: Bronze (raw), Silver (cleaned), Gold (ready to use)"],
                    ],
                },
            },
        ],
    },
    "target": {
        "title": "How Urvi would work in production for ONGC",
        "intro": ("Same agent, same tools, real data. ONGC's systems feed the ONGC Enterprise Data Platform (EDP); "
                  "Urvi reads a governed \"Well Health\" data product from the EDP; Urvi and Gemini run in Google Cloud "
                  "India regions; nothing leaves India. AI runs in the cloud, as the EDP RFP places it."),
        "sections": [
            {
                "heading": "A question, step by step",
                "steps": [
                    ["1", "Sign in", "Users reach Urvi through Identity-Aware Proxy with their ONGC login (single sign-on). "
                     "Typed and voice traffic both enter here."],
                    ["2", "Urvi API + web app", "The same service as the demo, on Cloud Run in Mumbai, scaling with load."],
                    ["3", "ADK agent", "The same single agent and tools as the demo; role-based access is enforced."],
                    ["4", "Gemini (India)", "Gemini on Vertex AI India regional endpoints. ONGC data is not used to train "
                     "models."],
                    ["5", "Tools", "The same engineering tools, plus nightly scores from the trained recommendation models."],
                    ["6", "EDP data adapter", "A new adapter in Urvi's data access layer. It replaces the demo's parquet "
                     "files."],
                    ["7", "EDP consumption API", "The adapter reads the Well Health data product through the EDP's API "
                     "(the RFP allows no direct database queries)."],
                ],
            },
            {
                "heading": "Voice",
                "steps": [
                    ["B", "Gemini Live (India)", "The Live proxy connects to Gemini Live on an India endpoint at go-live."],
                    ["C", "Same tools", "Voice tools call the same analytics code as chat."],
                ],
            },
            {
                "heading": "Where the data comes from",
                "steps": [
                    ["D1", "ONGC systems → EDP on-prem", "Production / DPR, SCADA + OSI PI, WIS / EDS, SAP, LIMS and DISHA "
                     "are ingested by the EDP's ingestion layer (UDEL) in ONGC's data centres. Raw Category A data (e.g. "
                     "raw SCADA) stays there."],
                    ["D2", "Interconnect", "Data that ONGC places in the cloud zone travels over a private link "
                     "(Cloud Interconnect), encrypted."],
                    ["D3", "Bronze → Silver → Gold", "The EDP cloud zone cleans and curates it into the Well Health data "
                     "product."],
                    ["D4", "Consumption API", "The product is published through the EDP API, which Urvi reads (step 7)."],
                ],
            },
            {
                "heading": "Two other routes (dashed)",
                "body": [
                    "Route B: the data stays on-prem and Urvi, still in the cloud, reads only the rows it needs from the "
                    "on-prem EDP API over the private link.",
                    "Route P (pilot): before the EDP is live, ONGC exports 10–20 mature Assam wells (names masked) to a "
                    "landing bucket in Mumbai, so Urvi can be proven on real data in weeks.",
                ],
            },
            {
                "heading": "How it stays in India and secure",
                "body": [
                    "Mumbai (asia-south1) is the primary region and Delhi (asia-south2) the disaster-recovery region; both "
                    "are MeitY-empanelled and accepted as India-resident by the RFP (§3.2.6).",
                    "ONGC holds the encryption keys (Cloud KMS, CMEK / EKM); a VPC Service Controls perimeter prevents data "
                    "copies leaving the project; Access Approval means Google support access needs ONGC's approval; logs "
                    "stay in India for at least 180 days.",
                ],
            },
            {
                "heading": "What changes from the demo",
                "table": {
                    "cols": ["Area", "Demo", "Production"],
                    "rows": [
                        ["Region", "us-central1 (Gemini Live)", "asia-south1 / asia-south2"],
                        ["Data", "Synthetic, packed into the app", "ONGC EDP Well Health product via API"],
                        ["Access", "Public demo URL", "IAP + ONGC single sign-on, role-based access"],
                        ["Scale", "One instance, in-memory sessions", "Autoscaling, Memorystore session store"],
                        ["Recommendations", "Classifier + rates + look-alikes", "Models trained on ONGC history (Vertex AI)"],
                        ["Documents", "Keyword search", "Vertex AI Search"],
                    ],
                },
            },
            {
                "heading": "Read more",
                "body": [
                    "Data routes and residency: docs/data_access_plan.md.",
                    "Training, inference and decisions: docs/ml_recommendation_engine.md.",
                ],
            },
        ],
    },
}
