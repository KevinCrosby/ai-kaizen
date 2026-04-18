# AI-Kaizen Toolkit

**CLI + Web + Copilot Skill for AI-Agent-Forward Kaizen transformation at scale.**

Operationalizes the [AI-Kaizen Framework v2](https://gist.github.com/KevinCrosby/6c409ca5cc5102a0b675d30ab2223f6f) — an eval-driven, PDCA-native approach to AI transformation that works backwards from business outcomes.

> *"The only AI transformation framework that treats 'knowing when to kill the project' as a success metric."*

## Core Concept: Eval-First Transformation

Every AI initiative must earn the right to act — progressing through bounded autonomy levels (L0 Inform → L1 Recommend → L2 Oversight → L3 Autonomous) based on measurable eval evidence, not hope.

## Three Ways to Use It

| Interface | Best For | Start With |
|-----------|----------|------------|
| **CLI** (`ai-kaizen`) | Power users, automation, CI/CD | `pip install -e . && ai-kaizen init "My Project"` |
| **Web UI** | Visual thinkers, stakeholder demos | `ai-kaizen serve` → http://localhost:5000 |
| **Copilot Skill** | Natural language, agentic workflows | 16 tools auto-activate on keywords |

## Quick Start

### Prerequisites

- **Python 3.9+** — `python3 --version`
- **pip** (comes with Python)

### Install

```bash
git clone https://github.com/KevinCrosby/ai-kaizen.git
cd ai-kaizen
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
pip install -e .
```

Verify: `ai-kaizen --version && ai-kaizen --help`

### Your First Initiative

```bash
# Create an initiative
ai-kaizen init "Customer Support Ticket Routing"

# Define the target outcome (work backwards from here)
ai-kaizen outcome set --metric "resolution time" --baseline "45 min avg" --target "15-25 min"

# Score data readiness (0-3 per dimension, interactive)
ai-kaizen assess data-readiness

# Scaffold safety eval tests (generates pytest stubs)
ai-kaizen eval scaffold --level L0 --output-dir ./evals

# Log PDCA activity
ai-kaizen pdca log --phase plan --note "Data readiness 14/18. Labels exist but 30% miscategorized."

# Check the gate — ready to proceed?
ai-kaizen pdca gate

# Portfolio dashboard
ai-kaizen status
```

### Launch the Web UI

```bash
ai-kaizen serve                           # → http://localhost:5000
ai-kaizen serve --port 8080               # custom port
ai-kaizen serve --host 0.0.0.0 --debug    # network-accessible + auto-reload
```

### Load the Demo Portfolio

A template healthcare portfolio with 10 initiatives across 8 industries is included:

```bash
# Seed the healthcare template (2 fully-detailed + 8 industry initiatives)
bash examples/seed-healthcare-portfolio.sh
ai-kaizen serve --port 5001
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `ai-kaizen init` | Create a new transformation initiative |
| `ai-kaizen select` | Set the current working initiative |
| `ai-kaizen assess data-readiness` | 6-dimension data readiness assessment |
| `ai-kaizen outcome set` | Define measurable business outcome |
| `ai-kaizen eval scaffold` | Generate eval test stubs (L0-L3 pytest files) |
| `ai-kaizen eval record` | Record eval run results |
| `ai-kaizen pdca log` | Log a PDCA entry (plan/do/check/act) |
| `ai-kaizen pdca gate` | Check gate criteria (kill/continue/promote) |
| `ai-kaizen pmo score` | 7-dimension PMO scoring |
| `ai-kaizen pmo rank` | Prioritized initiative backlog |
| `ai-kaizen roi track` | Track ROI with confidence levels |
| `ai-kaizen status` | Portfolio dashboard or initiative deep-dive |
| `ai-kaizen export` | Generate markdown/JSON reports |
| `ai-kaizen canvas` | Export initiative as A3 one-pager (markdown) |
| `ai-kaizen should-be-agent` | Interactive: should this task be an agent? |
| `ai-kaizen serve` | Launch the web dashboard |
| `ai-kaizen metrics` | Show process metrics (counters, latency) |

## Web UI

Dark-themed Flask web app — 9 templates, 20 route handlers.

| Route | Page |
|-------|------|
| `/` | Portfolio Dashboard — Estimated ROI, Actual ROI, Capture Rate |
| `/executive` | CxO Executive Dashboard (7 research-backed metric categories) |
| `/initiatives` | Create & manage initiatives |
| `/initiatives/<id>` | Initiative detail — outcomes, evals, PDCA, PMO, ROI, governance |
| `/initiatives/<id>/canvas` | Download A3 one-pager markdown |
| `/portfolio/roi` | Portfolio ROI breakdown with per-initiative trends |
| `/tools/should-be-agent` | "Should This Be an Agent?" 8-question assessment |

**Key features:**
- Severity class (S0-S3) + transformation type (optimize/redesign/reinvent)
- Define outcomes, scaffold evals, record eval run pass rates
- PDCA entry logging with loop/phase tracking + gate checks
- 6-dimension data readiness assessment with visual bars
- 7-dimension PMO scoring → auto-recommend (Fast-track/Qualified/Conditional/Decline)
- ROI tracking with value created vs captured and confidence progression
- Value event logging (create/capture/cost) with category breakdown
- Governance review tracking per initiative
- A3 one-pager canvas export (markdown download per initiative)
- "Should This Be an Agent?" interactive weighted assessment tool
- JSON and HTML export

## CxO Executive Dashboard

Research-backed dashboard tracking 7 metric categories:

| # | Category | Source | Tracks |
|---|----------|--------|--------|
| 1 | **ROI & Value Realization** | Deloitte | Value captured, TCO, net value, portfolio ROI% |
| 2 | **Pilot-to-Scale Pipeline** | BCG | Discovery→Validation→Scaling funnel |
| 3 | **Workforce Readiness** | Deloitte (62% cite #1 barrier) | AI fluency, training %, role redesign |
| 4 | **AI Governance** | Deloitte (1-in-5 mature) | Review coverage, eval coverage, completion |
| 5 | **Readiness Gap** | Deloitte (42% strategy-ready) | Composite ops readiness (data+eval+governance) |
| 6 | **Transformation Depth** | Deloitte (34% reimagining) | Optimize vs Redesign vs Reinvent breakdown |
| 7 | **Cost Transparency** | BCG/PwC | TCO breakdown by confidence level |

Sources: Deloitte State of AI 2026 (3,235 leaders), BCG AI Survey (1,400 C-suite), MIT Sloan/BCG, PwC.

## Eval Levels & Scaffold Templates

The `eval scaffold` command generates pytest stubs for each level:

| Level | Purpose | Generated Test Classes | Cadence |
|-------|---------|----------------------|---------|
| **L0: Safety** | Prompt injection, PII, blast radius | PromptInjection, DataPrivacy, FailSafe, BiasFairness | Pre-deploy gate |
| **L1: Assertions** | Feature-level correctness | CoreAccuracy, EdgeCases, Regression, Calibration | Every change |
| **L2: Human+Model** | Domain expert + LLM-as-judge | HumanAgreement, LLMJudge, OverrideAnalysis | Weekly |
| **L2.5: Monitoring** | Drift, confidence, cost | DataDrift, PerformanceDegradation, OperationalHealth | Always-on |
| **L3: Experiments** | Controlled A/B, DiD | ExperimentDesign, ExperimentResults, RolloutReadiness | Quarterly+ |

```bash
ai-kaizen eval scaffold --level L0 --output-dir ./evals   # → test_eval_l0_safety.py
ai-kaizen eval scaffold --level L1 --output-dir ./evals   # → test_eval_l1_assertions.py
```

Each file contains test stubs with `NotImplementedError` — fill them in with your domain-specific eval logic.

## Risk-Tiered Thresholds

| Severity | L0 | L1 | L2 |
|----------|-----|-----|-----|
| S0: Safety-critical | 100% | ≥95% | ≥90% |
| S1: Production-critical | 100% | ≥90% | ≥85% |
| S2: Efficiency | 100% | ≥80% | ≥80% |
| S3: Advisory | 100% | ≥70% | ≥75% |

## "Should This Be an Agent?" Decision Tree

An 8-question weighted assessment (CLI + web) to determine if a task is ready for agentic automation:

| # | Question | Weight |
|---|----------|--------|
| 1 | Is the task repetitive (>10x/week)? | ×2 |
| 2 | Can success be measured deterministically? | ×3 |
| 3 | Is training/reference data readily available? | ×2 |
| 4 | Are agent actions easily reversible? | ×2 |
| 5 | Is a human bottleneck causing delays? | ×1 |
| 6 | Are inputs and outputs well-structured? | ×2 |
| 7 | Is the safety risk low (S2-S3, not S0)? | ×2 |
| 8 | Is there a documented process today? | ×1 |

**Scoring:** ≥12/15 = **STRONG YES**, 7-11 = **MAYBE** (address gaps), <7 = **NOT YET**

## Initiative Canvas (A3 One-Pager)

Export any initiative as a markdown A3 one-pager for stakeholder reviews:

```bash
ai-kaizen canvas   # prints markdown to stdout
```

Includes: initiative metadata, outcomes, eval pass rates, PDCA history, gate status, data readiness, PMO score, ROI summary, and value tracking — all on one page.

Also available as a download button on each initiative's web detail page.

## PMO: Portfolio Prioritization & ROI

```bash
ai-kaizen pmo score              # Interactive 7-dimension scoring
ai-kaizen pmo rank               # Prioritized backlog
ai-kaizen roi track --value-created 420000 --value-captured 290000 --tco 180000
ai-kaizen status                 # Portfolio dashboard with Estimated/Actual ROI
```

**7-Dimension Scoring Rubric:** Business Value (2×), Baseline Measurability, Data Readiness, Change Readiness, Reversibility, Compliance Burden, Platform Reuse → Score out of 40 → Fast-track / Qualified / Conditional / Decline.

**ROI Confidence Progression:** Projected (±50%) → Estimated (±30%) → Measured (±15%) → Validated (±10%). Each level requires progressively harder evidence.

**Portfolio Dashboard:** Shows total Estimated ROI (value created), Actual ROI (captured − TCO), Capture Rate %, and per-initiative breakdown with green/red indicators.

See [docs/pmo-framework.md](docs/pmo-framework.md) for the complete PMO guide.

## Copilot CLI Skill

Ships as a **GitHub Copilot CLI extension** with 16 tools. Mention "kaizen", "initiative", "eval", or "transformation" and tools auto-activate.

| Tool | Description |
|------|-------------|
| `ai-kaizen-init` | Create initiative |
| `ai-kaizen-list` | Show all initiatives |
| `ai-kaizen-select` | Set working initiative |
| `ai-kaizen-outcome` | Define measurable outcome |
| `ai-kaizen-eval-scaffold` | Create eval suite (L0-L3) |
| `ai-kaizen-eval-record` | Record eval run results |
| `ai-kaizen-pdca` | Log PDCA entry |
| `ai-kaizen-gate` | Check gate criteria |
| `ai-kaizen-data-readiness` | 6-dimension data assessment |
| `ai-kaizen-pmo-score` | 7-dimension PMO scoring |
| `ai-kaizen-pmo-rank` | Ranked initiative backlog |
| `ai-kaizen-roi` | Record ROI data point |
| `ai-kaizen-executive-snapshot` | Full CxO dashboard (7 categories) |
| `ai-kaizen-workforce-assess` | Workforce readiness tracking |
| `ai-kaizen-portfolio` | Portfolio health summary |
| `ai-kaizen-serve` | Launch web dashboard |

**Install:**
- **Per-repo:** Already in `.github/extensions/ai-kaizen/` — works for anyone who clones
- **User-wide:** Copy to `~/.copilot/extensions/ai-kaizen/`

## Framework Architecture

```
┌─────────────────────────────────────────────────┐
│  LAYER 5: Business Outcome (start here)         │
│  LAYER 4: Eval Criteria (5 levels: L0→L3)       │
│  LAYER 3: Agent Architecture (maturity-labeled)  │
│  LAYER 2: Data + Infra Readiness                │
│  LAYER 1: People + Culture + Governance         │
└─────────────────────────────────────────────────┘
         ↕ Feedback loops between all layers
```

**Execution:** Three nested PDCA loops — Discovery (2-4 weeks) → Validation (6-12 weeks) → Scaling (ongoing)

## Project Structure

```
ai-kaizen/
├── src/ai_kaizen/
│   ├── cli.py                  # Click CLI (17 commands, 841 lines)
│   ├── domain/models.py        # Pydantic domain models
│   ├── store/database.py       # SQLite persistence (WAL mode, 15 tables)
│   ├── services/core.py        # Business logic (7 service classes)
│   ├── scaffolds/
│   │   ├── eval_templates.py   # L0-L3 pytest scaffold generators
│   │   ├── initiative_canvas.py # A3 one-pager markdown export
│   │   └── agent_decision_tree.py # 8-question agent readiness check
│   ├── logging_config.py       # Structured logging (JSON optional)
│   ├── metrics.py              # Process metrics (counters, histograms)
│   └── web/
│       ├── app.py              # Flask app factory, CSRF, lazy store
│       ├── routes.py           # 20 route handlers
│       └── templates/          # 9 Jinja2 templates (dark theme)
├── .github/
│   ├── extensions/ai-kaizen/   # Copilot CLI skill (16 tools)
│   └── copilot-instructions.md # DB conventions, test commands, macOS notes
├── docs/
│   ├── index.html              # Static site for file:// browsing
│   ├── framework-v2.md         # Full framework document
│   ├── pmo-framework.md        # PMO portfolio management guide
│   └── research.md             # Foundation research
├── examples/
│   └── seed-healthcare-portfolio.sh  # Template portfolio seed script
├── tests/
│   ├── test_services.py        # 42 service + scaffold tests
│   ├── test_web.py             # 39 web route + CxO dashboard tests
│   ├── test_store.py           # 27 store layer tests
│   └── evals/test_eval_l0.py   # Example L0 safety eval stubs
└── pyproject.toml              # Python 3.9+, Flask, Click, Rich, Pydantic
```

## Template Portfolio (10 Industries)

The demo database includes fully-populated initiatives across 8 industries:

| Industry | Initiative | Severity | Status |
|----------|-----------|----------|--------|
| Healthcare | AI-Powered Radiology Triage | S0 | Active |
| Pharma | Clinical Trial Patient Matching | S1 | Active |
| Financial Services | AML Transaction Monitoring | S1 | Active |
| Manufacturing | Predictive Maintenance | S2 | Active |
| Retail | Dynamic Pricing Engine | S2 | Active |
| Insurance | Claims Triage Automation | S1 | Active |
| Logistics | Demand Forecasting | S2 | Active |
| Energy | Grid Load Balancing | S1 | Active |
| Legal | Contract Review Automation | S2 | Active |
| EdTech | Adaptive Learning Paths | S3 | Active |

Each has outcomes, eval suites with runs, PDCA history, data readiness, PMO scores, ROI entries, and value events.

## Who Uses What

| Role | CLI | Web | Copilot Skill |
|------|-----|-----|---------------|
| **CxO / VP** | `status` | Executive Dashboard | `ai-kaizen-executive-snapshot` |
| **Transformation Owner** | `init`, `outcome`, `pdca`, `canvas` | Initiative detail + canvas download | Natural language |
| **PMO / Portfolio Mgr** | `pmo rank`, `roi` | Portfolio ROI page | `ai-kaizen-pmo-score`, `ai-kaizen-roi` |
| **AI/Eval Engineer** | `eval scaffold`, `eval record` | Eval forms | `ai-kaizen-eval-*` |
| **Frontline Supervisor** | `pdca gate`, `should-be-agent` | Gate check + Agent Check page | `ai-kaizen-gate` |

## The Key Idea

**AI must earn the right to act.** Every agent starts at L0 (inform only) and can only advance to L1 → L2 → L3 autonomy by passing progressively harder eval gates — with operations leadership (not the AI team) making the promotion call based on evidence.

The toolkit enforces this: no skipping levels, no vibes-based promotion, explicit kill criteria at every gate.

## Research & Framework

- [Foundation Research: Kaizen, Gemba, AI/ML](https://gist.github.com/KevinCrosby/beacb8f1ac0cb5dfcd63c7d0c79c9bba)
- [AI-Kaizen Framework v2](https://gist.github.com/KevinCrosby/6c409ca5cc5102a0b675d30ab2223f6f)

## Development

```bash
git clone https://github.com/KevinCrosby/ai-kaizen.git
cd ai-kaizen
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests (108 passing, excludes eval stubs)
python -m pytest tests/ --ignore=tests/evals -q

# Run with debug logging
AI_KAIZEN_LOG_LEVEL=DEBUG ai-kaizen status

# Dev server with auto-reload
ai-kaizen serve --debug

# Process metrics
ai-kaizen metrics --json
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_KAIZEN_DB` | `~/.ai-kaizen/kaizen.db` | SQLite database file path |
| `AI_KAIZEN_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `AI_KAIZEN_LOG_JSON` | `0` | Set to `1` for structured JSON log output |
| `AI_KAIZEN_SECRET_KEY` | auto-generated | Flask session secret key |

### Data Storage

All data lives in a single SQLite file (WAL mode, 15 tables). To start fresh: `rm ~/.ai-kaizen/kaizen.db`

Project-specific database: `export AI_KAIZEN_DB=./my-project.db`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: ai-kaizen` | Activate venv: `source .venv/bin/activate` |
| `No initiative selected` | Run `ai-kaizen init "Name"` or `ai-kaizen select` |
| DB locked errors | Close other ai-kaizen processes; DB uses WAL mode with 5s timeout |
| Web UI won't start | Check port isn't in use: `lsof -i :5000` |
| Template changes not showing | Restart Flask (no auto-reload in production mode) |
| Copilot skill not loading | Run `node --check .github/extensions/ai-kaizen/extension.mjs` |

## License

MIT
