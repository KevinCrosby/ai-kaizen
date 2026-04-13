# AI-Kaizen Toolkit

**CLI + Web + Copilot Skill for AI-Agent-Forward Kaizen transformation at scale.**

Operationalizes the [AI-Kaizen Framework v2](https://gist.github.com/KevinCrosby/6c409ca5cc5102a0b675d30ab2223f6f) — an eval-driven, PDCA-native approach to AI transformation that works backwards from business outcomes.

> *"The only AI transformation framework that treats 'knowing when to kill the project' as a success metric."*

## Core Concept: Eval-First Transformation

Every AI initiative must earn the right to act — progressing through bounded autonomy levels (L0 Inform → L1 Recommend → L2 Oversight → L3 Autonomous) based on measurable eval evidence, not hope.

## Three Ways to Use It

| Interface | Best For | Start With |
|-----------|----------|------------|
| **CLI** | Power users, automation, CI/CD | `pip install -e . && ai-kaizen init "My Project"` |
| **Web UI** | Visual thinkers, stakeholder demos | `ai-kaizen serve` → http://localhost:5001 |
| **Copilot Skill** | Natural language, agentic workflows | Just talk — 16 tools auto-activate on keywords |

## Quick Start

```bash
# Install
git clone https://github.com/KevinCrosby/ai-kaizen.git
cd ai-kaizen
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# CLI
ai-kaizen init "Predictive Maintenance - Line 3"
ai-kaizen assess data-readiness
ai-kaizen outcome set --metric "MTBF" --baseline "72h" --target "96-120h"
ai-kaizen eval scaffold --level L0
ai-kaizen pdca start discovery
ai-kaizen status

# Web UI
ai-kaizen serve              # http://localhost:5001
ai-kaizen serve --host 0.0.0.0 --port 8080   # network-accessible
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `ai-kaizen init` | Create a new transformation initiative |
| `ai-kaizen select` | Set the current working initiative |
| `ai-kaizen assess` | Run data readiness or cultural assessments |
| `ai-kaizen outcome` | Define and track business outcomes |
| `ai-kaizen eval` | Scaffold eval suites, record results |
| `ai-kaizen pdca` | Track PDCA loops, log entries, check gates |
| `ai-kaizen pmo` | Portfolio scoring, ranking, capacity, estimation |
| `ai-kaizen roi` | Track ROI with confidence levels |
| `ai-kaizen status` | Portfolio dashboard or initiative deep-dive |
| `ai-kaizen export` | Generate markdown/JSON reports |
| `ai-kaizen serve` | Launch the web dashboard |

## Web UI

A lightweight Flask web app with a dark-themed responsive UI.

```
http://localhost:5001/              # Portfolio Dashboard
http://localhost:5001/executive     # CxO Executive Dashboard (7 metric categories)
http://localhost:5001/initiatives   # Create & manage initiatives
http://localhost:5001/portfolio/roi # Portfolio ROI breakdown
```

**Features:**
- Create initiatives with severity class + transformation type (optimize/redesign/reinvent)
- Define outcomes, scaffold evals, record eval runs
- Log PDCA entries, run gate checks
- 6-dimension data readiness assessment with visual bars
- 7-dimension PMO scoring with auto-recommendation
- ROI tracking with confidence progression
- Governance review tracking per initiative
- JSON and HTML export

## CxO Executive Dashboard

Research-backed dashboard tracking 7 metric categories that CxOs and AI transformation leaders care most about:

| # | Category | Source | Tracks |
|---|----------|--------|--------|
| 1 | **ROI & Value Realization** | Deloitte | Value captured, TCO, net value, portfolio ROI% |
| 2 | **Pilot-to-Scale Pipeline** | BCG | Discovery→Validation→Scaling funnel with progress bar |
| 3 | **Workforce Readiness** | Deloitte (62% cite #1 barrier) | AI fluency, training %, role redesign, upskilling |
| 4 | **AI Governance** | Deloitte (1-in-5 mature) | Review coverage, eval suite coverage, completion rate |
| 5 | **Readiness Gap** | Deloitte (42% strategy-ready) | Composite ops readiness (data + eval + governance) |
| 6 | **Transformation Depth** | Deloitte (34% reimagining) | Optimize vs Redesign vs Reinvent breakdown |
| 7 | **Cost Transparency** | BCG/PwC | TCO breakdown by confidence level |

Sources: Deloitte State of AI 2026 (3,235 leaders), BCG AI Survey (1,400 C-suite), MIT Sloan/BCG, PwC.

## Copilot CLI Skill

The toolkit ships as a **GitHub Copilot CLI extension** with 16 tools. When working in any directory, just mention kaizen/initiative/transformation and the tools activate automatically.

**Available tools:**

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

**Install the skill:**
- **Per-repo:** Already in `.github/extensions/ai-kaizen/` — works for anyone who clones
- **User-wide:** Copy `.github/extensions/ai-kaizen/` to `~/.copilot/extensions/ai-kaizen/`

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

## Eval Levels

| Level | Purpose | Cadence |
|-------|---------|---------|
| **L0: Safety** | Prompt injection, PII, blast radius, idempotency | Pre-deploy gate (non-negotiable) |
| **L1: Assertions** | Feature-level correctness tests | Every code/prompt change |
| **L2: Human+Model** | Domain expert + LLM-as-judge review | Weekly |
| **L2.5: Monitoring** | Drift, confidence, override rate, cost | Always-on |
| **L3: Experiments** | Controlled A/B, DiD, stepped-wedge | Quarterly+ |

## Risk-Tiered Thresholds

| Severity | L0 | L1 | L2 |
|----------|-----|-----|-----|
| S0: Safety-critical | 100% | ≥95% | ≥90% |
| S1: Production-critical | 100% | ≥90% | ≥85% |
| S2: Efficiency | 100% | ≥80% | ≥80% |
| S3: Advisory | 100% | ≥70% | ≥75% |

## PMO: Portfolio Prioritization & ROI

The toolkit includes a full PMO framework for managing multiple initiatives at scale:

```bash
ai-kaizen pmo score              # Interactive 7-dimension scoring
ai-kaizen pmo rank               # Prioritized backlog
ai-kaizen pmo dashboard          # Portfolio health scorecard
ai-kaizen pmo capacity           # WIP limit check + bottleneck analysis
ai-kaizen roi track --value-created 420000 --value-captured 290000 --tco 180000
ai-kaizen roi portfolio          # Portfolio-level ROI summary
ai-kaizen pmo estimate --size M  # T-shirt size → cost estimate
```

**7-Dimension Scoring Rubric:** Business Value (2×), Baseline Measurability, Data Readiness, Change Readiness, Reversibility, Compliance Burden, Platform Reuse → Score out of 40 → Fast-track / Qualified / Conditional / Decline.

**ROI Confidence Progression:** Projected (±50%) → Estimated (±30%) → Measured (±15%) → Validated (±10%). Each level requires progressively harder evidence.

See [docs/pmo-framework.md](docs/pmo-framework.md) for the complete PMO guide.

## Project Structure

```
ai-kaizen/
├── src/ai_kaizen/
│   ├── cli.py              # Click CLI entry point
│   ├── domain/models.py    # Pydantic domain models
│   ├── store/database.py   # SQLite persistence (WAL mode, 14 tables)
│   ├── services/core.py    # Business logic (7 service classes)
│   └── web/                # Flask web UI
│       ├── app.py          # App factory, CSRF, lazy store
│       ├── routes.py       # 18 route handlers
│       ├── templates/      # Jinja2 templates (dark theme)
│       └── static/style.css
├── .github/extensions/
│   └── ai-kaizen/          # Copilot CLI skill (16 tools)
├── docs/
│   ├── framework-v2.md     # Full framework document
│   ├── pmo-framework.md    # PMO portfolio management guide
│   └── research.md         # Foundation research
├── tests/
│   ├── test_services.py    # 27 service layer tests
│   └── test_web.py         # 39 web route + CxO tests
└── pyproject.toml          # Python 3.9+, Flask, Click, Rich
```

## Who Uses What

| Role | CLI | Web | Copilot Skill |
|------|-----|-----|---------------|
| **CxO / VP** | `status` | Executive Dashboard | `ai-kaizen-executive-snapshot` |
| **Transformation Owner** | `init`, `outcome`, `pdca` | Initiative detail page | Natural language prompts |
| **PMO / Portfolio Mgr** | `pmo rank`, `roi` | Portfolio ROI page | `ai-kaizen-pmo-score`, `ai-kaizen-roi` |
| **AI/Eval Engineer** | `eval scaffold`, `eval record` | Eval forms | `ai-kaizen-eval-*` |
| **Frontline Supervisor** | `pdca gate` | Gate check card | `ai-kaizen-gate` |

## The Key Idea

**AI must earn the right to act.** Every agent starts at L0 (inform only) and can only advance to L1 → L2 → L3 autonomy by passing progressively harder eval gates — with operations leadership (not the AI team) making the promotion call based on evidence.

The toolkit enforces this: no skipping levels, no vibes-based promotion, explicit kill criteria at every gate.

## Research & Framework

- [Foundation Research: Kaizen, Gemba, AI/ML](https://gist.github.com/KevinCrosby/beacb8f1ac0cb5dfcd63c7d0c79c9bba)
- [AI-Kaizen Framework v2](https://gist.github.com/KevinCrosby/6c409ca5cc5102a0b675d30ab2223f6f)

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -v                    # 66 tests
ai-kaizen serve --debug      # Dev server with auto-reload
```

## License

MIT
