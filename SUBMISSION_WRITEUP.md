# EcoTracker — Platform Architecture & Technical Overview

**Project:** EcoTracker — AI Carbon Intelligence Platform  
**Built with:** Google ADK 2.0, Gemini, FastMCP, FastAPI, SQLite  

---

## 1. Problem Statement

Climate change is one of the defining challenges of our time, yet most people have no idea what their daily choices actually cost in terms of carbon emissions. Existing carbon calculators are static forms that require manual data entry and provide no guidance. There is a clear gap for an intelligent, conversational agent that can:

- Take natural language descriptions of everyday activities
- Compute accurate CO2 equivalent emissions using real data
- Proactively recommend actionable, personalised eco-swaps
- Do all of this safely, without exposing users to prompt injection or PII leakage risks

---

## 2. Solution Overview

EcoTracker is a **multi-agent AI system** built on the Google ADK 2.0 Workflow API. It acts as a personal eco-advisor, guiding users through footprint calculations and greener alternatives in a natural conversation.

### Core Flow

1. **User sends a natural language query** (e.g., "Calculate my carbon footprint for a 50 km gasoline drive.")
2. **Security Checkpoint** scrubs PII, blocks prompt injections, and filters credential keywords before any LLM is called.
3. **Orchestrator Agent** (Gemini-powered) routes to two specialised sub-agents via tool calls:
   - `footprint_calculator_agent` — computes CO2e using MCP emission data
   - `swap_recommender_agent` — suggests greener alternatives using MCP efficiency and offset data
4. **Post-process node** checks whether the user requested logging (`log`/`save`) and routes to HITL if so.
5. **Human-in-the-Loop (HITL)** pauses execution and asks the user to confirm before logging data.
6. **Final output node** assembles and delivers the combined response.

---

## 3. ADK Features Used

| ADK Feature | Where Used |
|-------------|-----------|
| `Workflow` (Graph API) | Root agent — deterministic, conditional multi-node pipeline |
| `@node` decorator | All 5 workflow nodes (`security_checkpoint`, `security_event_node`, `post_process_node`, `hitl_approval_node`, `final_output_node`) |
| `@node(rerun_on_resume=True)` | `hitl_approval_node` — resumes after user provides HITL input |
| `LlmAgent` | Orchestrator, footprint calculator, and swap recommender sub-agents |
| `AgentTool` | Wraps sub-agents as callable tools inside the orchestrator |
| `McpToolset` (stdio) | Connects to a local FastMCP server exposing 3 eco-data tools |
| `DEFAULT_ROUTE` edges | Ensures conditional edges have explicit fallback paths (no `[NO DEFAULT]` warnings) |
| `ctx.state` | Shares scrubbed user query and sub-agent results across all nodes |
| `RequestInput` (HITL) | Pauses the workflow and yields a confirmation prompt to the user |
| `App` | Wraps the workflow for the ADK playground server |
| Audit Logging | Structured JSON logs at every security and HITL decision point |

---

## 4. MCP Integration

A **local FastMCP server** (`app/mcp_server.py`) is launched as a subprocess via `StdioServerParameters`. It exposes three domain-specific tools:

### `get_transit_emissions(mode: str) -> dict`
Returns CO2e per km for transport modes:
- `gasoline_car` → 192 g/km
- `electric_car` → 53 g/km
- `bus` → 89 g/km
- `train` → 41 g/km
- `plane` → 255 g/km

### `get_appliance_efficiency(appliance: str) -> dict`
Returns energy consumption and star rating for appliances:
- Old fridge → 500 kWh/year (1-star)
- Modern fridge → 150 kWh/year (5-star)
- LED bulb → 10W, 80% more efficient than incandescent
- etc.

### `get_waste_offset(material: str, quantity_kg: float) -> dict`
Returns estimated CO2 savings from recycling/composting:
- Plastic → 1.5 kg CO2e saved per kg recycled
- Aluminium → 8.0 kg CO2e saved per kg recycled
- Food waste composting → 0.5 kg CO2e saved per kg composted

---

## 5. Security Design

Security was treated as a first-class concern, not an afterthought:

| Layer | Technique |
|-------|-----------|
| **Prompt Injection** | Keyword blocklist (`ignore previous instructions`, `override`, `bypass security`, etc.) |
| **PII Scrubbing** | Regex-based redaction of emails, phone numbers, and UK/US street addresses. Uses negative lookahead `(?!km\|miles\|...)` to prevent false positives on distance values like "50 km". |
| **Credential Filter** | Word-boundary regex scan for `password`, `passwd`, `pin`, `secret_key` |
| **HITL Confirmation** | Explicit user approval required before any data is persisted |
| **Audit Trail** | Every security event and HITL decision emits a structured JSON log: `[AUDIT_LOG] {"timestamp": ..., "action": ..., "severity": ..., "details": {...}}` |

---

## 6. Human-in-the-Loop Flow

When the user's query contains the words `log` or `save`, the workflow pauses:

```
orchestrator → post_process_node → hitl_approval_node
                                        │ yields RequestInput
                                        │ "Do you want to log this calculation? (yes/no)"
                                        │ user types "yes" or "no"
                                        ▼
                                   final_output_node
                                        │ includes log status in response
```

This demonstrates a real-world agentic pattern where sensitive actions (writing user data) require explicit human confirmation.

---

## 7. Challenges & Key Learnings

### ADK 2.0 Graph API Constraints
- `DEFAULT_ROUTE` cannot be combined with other routes in a list. Separate edges are required for named routes and the default.
- Functions used as workflow nodes must be decorated with `@node`. Bare functions cause Pydantic `ValidationError` on graph construction.
- Node `output` must be a `types.Content` object, not a raw string, or the framework's output schema validation will reject it.

### Windows Hot-Reload Issue
`adk web --reload_agents` creates an infinite watch loop on Windows due to `.venv` directory changes being picked up by the file watcher. Workaround: always run without `--reload_agents` on Windows and restart the server manually after code changes.

### Free-Tier Quota
`gemini-2.5-flash` has a limit of 20 requests/day on the free tier, which is quickly exhausted by a multi-agent pipeline that makes 3–5 LLM calls per user message. Switching to `gemini-2.5-flash-lite` (1,500 requests/day) is strongly recommended for development.

---

## 8. Example Session

**User:** `"Calculate my carbon footprint for a 50 km drive in a gasoline car, and suggest how I can reduce it."`

**Audit Logs:**
```json
{"action": "security_checkpoint_passed", "severity": "INFO", "details": {"pii_scrubbed": false, "status": "passed"}}
{"action": "auto_approved", "severity": "INFO", "details": {"reason": "Normal query, no confirmation required"}}
```

**Agent Response (synthesized):**
> **Carbon Footprint Calculation:**
> 50 km × 192 g CO2e/km (gasoline car) = **9.6 kg CO2e**
>
> **Eco-Swap Recommendations:**
> 1. 🚆 **Train** — 50 km by train emits only 2.05 kg CO2e (79% less)
> 2. 🚌 **Bus** — 4.45 kg CO2e (54% reduction)
> 3. ⚡ **Electric Car** — 2.65 kg CO2e if you own an EV (72% reduction)
>
> *Log Status: No log requested*

---

## 9. Recent Enhancements & Production Upgrades

Building upon the initial core architecture, EcoTracker has been upgraded into a production-grade personal sustainability system:

1. **Embedded SQLite Persistence Engine (`app/db.py`)**:
   - Replaced mock logging with a true relational schema storing verified footprint records, category breakdowns, and cumulative savings.
   - Preserves user history and computes aggregate metrics across sessions.
2. **Food & Dietary Emissions Module (`app/mcp_server.py`)**:
   - Added `get_dietary_emissions` powered by global food lifecycle benchmarks (Poore & Nemecek, Science), calculating emissions for meats, dairy, and grains against low-carbon plant alternatives.
3. **Interactive Visual Dashboard (`app/dashboard.py`)**:
   - Integrated a live Chart.js dashboard displaying category emission distributions, real-time savings meters, and recent log histories.
4. **Milestone & Gamification Engine**:
   - Automated badge evaluation (*"First Step"*, *"Eco Habit"*, *"Carbon Saver"*, *"Climate Hero"*) that triggers upon user accomplishments.
5. **Context-Aware Enterprise Security (`app/security.py`)**:
   - Refactored regex patterns to support international phone formats and context-aware credential detection, eliminating false positives on technical units (e.g., electrical plugs, distance measurements).
6. **Automated Test Suite & CI (`tests/`, `.github/workflows/ci.yml`)**:
   - 26 automated tests covering MCP calculations, security edge cases, persistence, vision OCR, and workflow node state transitions.
7. **Multimodal Vision Intelligence (`app/services/vision_scanner.py`)**:
   - Integrated Gemini 2.5 Flash Vision OCR extracting line-item emissions from grocery receipts and electric/gas utility bills with instant green swap recommendations.
8. **Dynamic Grid Carbon Intensity Tracking (`app/services/grid_intensity.py`)**:
   - Real-time UK National Grid ESO API integration and regional eGRID/ENTSO-E modeling providing dynamic g CO2e/kWh and smart EV load-shifting recommendations.
9. **Airport-to-Airport Flight Calculator (`app/services/flight_calculator.py`)**:
   - Haversine great-circle distance modeling with DEFRA radiative forcing indices (RFI 1.9x) and high-speed rail substitution analysis.
10. **"What-If" Climate & ROI Scenario Simulator (`app/services/simulator.py`)**:
    - Multi-lever transition engine modeling 1-year, 5-year, and 10-year cumulative CO2e abatement alongside household financial savings ($ USD).
11. **Enterprise ESG Scope 1, 2, 3 Disclosure (`app/services/esg_report.py`)**:
    - Corporate sustainability accounting aligned with the GHG Protocol Corporate Standard, featuring cryptographic audit hashes and a 1-click printable executive PDF report.
12. **Mobile & Desktop Responsive Architecture with Permanent Large Typography (`app/frontend.py`)**:
    - Built with high-contrast, generous 18px base typography (17px chat bubbles, 15px+ meta labels, 1.6 line-height) set as the permanent default everywhere, paired with mobile bottom app bar navigation and touch-first accessibility.
13. **Progressive Web App (PWA) & Voice Speech-to-Text**:
    - Offline service worker (`/sw.js`), web manifest (`/manifest.json`), and hands-free microphone voice dictation via Web Speech API.
14. **Community Leaderboard & 30-Day Carbon Trends**:
    - Ranked team sustainability leaderboard and 30-day historical time-series analytics chart powered by Chart.js.
15. **Full React 19 + Vite Single Page Application (`frontend/`)**:
    - Complete reactive component architecture with React 19, Chart.js, and Canvas-Confetti. Pre-compiled to `static_dist/` and served seamlessly via FastAPI at `/`, alongside a dedicated Vite HMR development server.

---

## 10. Repository Structure

```
ecotracker/
├── app/
│   ├── agent.py          # Workflow graph, nodes, orchestration
│   ├── mcp_server.py     # FastMCP server — 5 domain-specific carbon tools
│   ├── db.py             # SQLite persistence, profile statistics, and badge engine
│   ├── security.py       # Enterprise PII scrubbing, injection, and credential guardrails
│   ├── dashboard.py      # Interactive FastAPI & REST endpoints
│   ├── frontend.py       # Responsive mobile/desktop UI, PWA shell, and components
│   ├── fast_api_app.py   # Vertex AI Reasoning Engine & A2A production server
│   ├── config.py         # Env-var config
│   └── __init__.py
├── frontend/             # Modern React 19 + Vite Single Page Application (SPA)
│   ├── src/
│   │   ├── components/   # Modular React views (Chat, Vision, Analytics, Leaderboard...)
│   │   ├── App.jsx       # Root reactive application
│   │   └── index.css     # Permanent high-contrast large typography & themes
│   └── vite.config.js    # Vite configuration & backend proxy
├── static_dist/          # Pre-compiled high-performance production React assets
├── tests/                # Automated pytest suite (29 tests)
│   ├── test_advanced_features.py
│   ├── test_dashboard_api.py
│   ├── test_db.py
│   ├── test_mcp_server.py
│   ├── test_security.py
│   └── test_workflow.py
├── .github/workflows/    # Continuous integration
│   └── ci.yml
├── .env                  # API key and model (not committed)
├── Makefile              # Developer shortcuts (install, dev, dashboard, test)
├── pyproject.toml        # Dependencies and tool configurations
└── README.md
```

---

## 11. Future Scope & Strategic Roadmap

1. **IoT Smart Meter & Home Telemetry (Matter / MQTT / Zigbee)**:
   - Automated ingestion from Shelly/TP-Link smart plugs and Google Nest thermostats streaming true kWh into FastMCP calculation engines without manual human logging.
2. **Open Banking & Green Fintech Footprinting (Plaid / Yapily)**:
   - Direct transactional accounting leveraging Merchant Category Codes (MCCs) and USEEIO econometric emission models across debit and credit cards.
3. **Autonomous Agent-to-Agent (A2A) Microgrid Energy Auctions**:
   - Multi-agent ADK negotiation scheduling home battery charging and EV load shifts during dynamic negative-tariff renewable generation windows.
4. **Decentralized Carbon Credit Verification & On-Chain Audit**:
   - Double-counting-proof smart certificates on eco-friendly distributed ledgers ensuring zero-greenwashing compliance for CSRD, SEC Climate, and California SB 253 corporate disclosures.
5. **Cross-Platform Native Mobile Apps with Passive GPS Detection**:
   - React Native / Expo sensor fusion engine with battery-efficient geofencing to passively detect bicycle, train, and car transit trips.
6. **Enterprise Scope 3 Supply Chain Ingestion Portal**:
   - Upstream supplier portal automating vendor carbon questionnaires and extracting line-item carbon from PEPPOL / EDI electronic invoices.
