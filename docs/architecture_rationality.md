# Urvi AI Agent (Cairn Barmer): Architectural Rationality & Engine Design

> **Executive Summary (BLUF)**: Urvi is a **Single-Agent, Multi-Tool (SAMT) Architecture that leverages the best of both worlds**: an **agentic front-end (Gemini 3.8 Live)** to understand and map human needs in natural language, conversational context, and code-switching, paired with **deterministic algorithms on the back-end** (decline curves, breakthrough diagnostics, ML classifiers, and governed BigQuery lakehouse views) to completely eliminate hallucinations. Every number spoken comes from deterministic code, never from model imagination.

---

## 1. The Core Architectural Philosophy: Best of Both Worlds

In upstream petroleum operations across mature fields (Mangala, Bhagyam, Aishwariya, Raageshwari), generative AI cannot be trusted to perform ad-hoc mathematics, filter well rosters, or fabricate engineering diagnostics. A single hallucinated water cut percentage, polymer breakthrough estimate, or pump failure recommendation can compromise operational safety and capital allocation.

By implementing a **Single-Agent, Multi-Tool (SAMT) pattern**, Urvi bridges two previously incompatible paradigms:
1. **The Agentic World (Linguistics & Intent)**: Fluid, natural language voice comprehension, handling colloquialisms, Hindi/Hinglish code-switching, conversational memory, and screen context without rigid menu hierarchies.
2. **The Deterministic World (Mathematical Rigor)**: Absolute mathematical reproducibility, subsurface physics compliance, governed database queries, and zero-hallucination guardrails.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      PROBABILISTIC COGNITIVE ZONE                      │
│                  (Where the Gemini AI Agent Lives)                     │
│                                                                        │
│   • Multimodal audio stream processing (16 kHz in / 24 kHz out)        │
│   • Natural language & multilingual parsing (English / Hindi / Hinglish)│
│   • Conversational memory & coreference resolution ("this well")       │
│   • Tool selection & parameter extraction into typed dictionaries      │
│   • Natural language explanation synthesis of returned tool data       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Emitted Tool Call: {tool, args}
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     DETERMINISTIC EXECUTION ZONE                       │
│                     (Zero AI Agency — Pure Code)                       │
│                                                                        │
│   • In-memory well master normalization & matching (_find_well)        │
│   • Production status & KPI sorting (list_problem_wells)               │
│   • Subsurface physics: decline curves & breakthrough diagnostics      │
│   • ML intervention classification & candidate ranking (TC-021, TC-022)│
│   • Governed BigQuery Silver/Gold data lakehouse queries (Arrow/Pandas)│
│   • Numerical integrity response guard (masks any unverified number)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Tool Result Data Dictionary
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   VERIFIED RESPONSE & UI SYNCHRONIZATION               │
│   • Spoken answer delivered with zero hallucinated figures             │
│   • Screen actions dispatched (ui_control: 3D map fly-to, schematics)  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Is the Voice-to-Dictionary Step the Only Part That is an "Agent"?

**Yes, conceptually.** 

In agentic theory (e.g., the ReAct pattern), an "Agent" is an autonomous reasoning loop: **Perceive $\rightarrow$ Decide $\rightarrow$ Act $\rightarrow$ Communicate**. 

In Urvi, agency is deliberately restricted to the boundaries:
1. **The Inbound Boundary (Speech $\rightarrow$ Dictionary)**: Gemini Live listens to continuous audio, interprets conversational context, and **decides which tool to invoke with what parameters**. This is the decision-making agency.
2. **The Outbound Boundary (Dictionary $\rightarrow$ Spoken Voice)**: Gemini Live takes structured JSON results and synthesizes a natural, fluent spoken answer in the selected persona and language.

**Between these two boundaries, there is zero AI agency.** 
The database filtering, dataframe manipulations, physics algorithms, and intervention scorings are written in deterministic Python. The LLM does not write SQL, does not filter pandas tables, and does not execute arbitrary code.

---

## 3. What the Agent Does to Convert Voice into a Dictionary (The 6 Cognitive Tasks)

Converting natural spoken audio into an actionable Python tool call requires the agent to execute 6 simultaneous cognitive tasks:

### 1. Multilingual Acoustic Normalization
* **Code-Switching**: Fluently understands mixed Hindi-English phrasing used in field operations:
  * *"Mangala dikhao"* $\rightarrow$ targets Mangala field.
  * *"Kitne wells down hain?"* $\rightarrow$ targets fleet failure KPIs.
  * *"Sabse kharab well kaunsi hai?"* $\rightarrow$ targets priority problem wells.
* **Disfluency Handling**: Seamlessly removes stuttering, filler words ("uhm", "err"), and conversational self-corrections (e.g., *"Show well MGL 128... no wait, MGL 129"* $\rightarrow$ resolves cleanly to `MGL-129`).

### 2. Conversational Memory & Coreference Resolution
* **Pronoun Resolution**: If a user first asks *"Tell me about MGL-047"*, and follows up with *"What is **its** water cut?"*, the agent binds the pronoun *"its"* to `well_id="MGL-047"`.
* **Screen State Awareness**: When the engineer says *"What is the next best action for **this well**?"*, the agent inspects active frontend session context to inject whichever well is currently open in the 3D viewport.

### 3. Tool Selection & Intent Routing
* Matches user intent against the registered descriptions of Urvi's 13 voice tools:
  * Diagnostics $\rightarrow$ `attribute_decline`
  * Single well lookup $\rightarrow$ `well_summary` or `well_profile`
  * Field-level comparison $\rightarrow$ `compare_fields`
  * Chit-chat or policy questions $\rightarrow$ Direct conversational response without tool execution.

### 4. Parameter Extraction & Schema Typing
* Extracts messy human qualifiers into strict Python types conforming to tool function signatures:
  * *"In the last three years"* $\rightarrow$ `months=36` (integer)
  * *"Current quarter"* $\rightarrow$ `period="QTD"` (string)
  * *"Failing wells"* $\rightarrow$ `status="failed"` (string)

### 5. Ambiguity Detection & Default Injection
* **Default Values**: If the user asks *"Which wells are at risk?"* without specifying a count, the agent automatically supplies the declared tool default (`limit=5`).
* **Active Elicitation**: If the user asks a completely ungrounded question (*"Compare them"* with no prior entities), the agent asks for clarification rather than hallucinating arbitrary parameters.

### 6. Multimodal UI Control Dispatch (`ui_control`)
* Along with analytics tools, the agent triggers screen commands:
  * Switching between map basemaps (satellite vs. terrain).
  * Flying the 3D camera to a specific wellhead or gathering station.
  * Opening the completion schematic or workover timeline drawer.

---

## 4. How Urvi Knows Which Wells to Filter

Urvi does not execute ad-hoc SQL `WHERE` clauses against production databases. Instead, it utilizes four deterministic filtering mechanisms:

| Mechanism | Example User Request | Agent Tool Call (Dictionary) | Deterministic Code Execution |
| :--- | :--- | :--- | :--- |
| **1. Direct Entity Resolution** | *"Show me Mangala well 47"* | `well_summary(well_id="MGL-047")` | `_find_well()` normalizes text (`strip().upper().replace(" ", "")`) and finds the exact record in the well master catalog. |
| **2. Status & Production Slicing** | *"Which wells are down right now?"* | `list_problem_wells(status="failed", limit=5)` | Filters master list for `status == "failed"`, sorts ascending by `oil_bopd` (worst hit first), and returns the top 5 records. |
| **3. Active Viewport Context** | *"What is the next best action for this well?"* | `next_best_action(well_id="MGL-047")` | Frontend injects the currently selected well ID from the active dashboard tab into the session context. |
| **4. Physics & Telemetry Diagnostics** | *"Which wells have water breakthrough?"* | `attribute_decline(field="Mangala")` | Python analytics engine scans telemetry data (water cut $>85\%$, sudden WOR ramp-up, pump pressure anomalies) to rank candidate wells. |

---

## 5. End-to-End Verification Guardrail

To ensure enterprise trustworthiness across executive leadership and asset teams:

1. **Tool-Sourced Grounding**: All figures (oil rates, gas MCFD, water cut, pressures, rig days) are computed by deterministic Python functions.
2. **Post-Turn Number Masking**: An automated output validator intercepts Gemini's spoken response before audio synthesis. Every numerical value in the spoken sentence is checked against the tool's raw JSON output dictionary. Any number generated by model imagination is automatically masked.
3. **Auditability**: Every tool call and its arguments are logged with duration timestamps and data lineage tracking.
