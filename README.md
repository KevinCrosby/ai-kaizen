# AI-Kaizen Toolkit

**CLI toolkit for AI-Agent-Forward Kaizen transformation at scale.**

Operationalizes the [AI-Kaizen Framework v2](https://gist.github.com/KevinCrosby/6c409ca5cc5102a0b675d30ab2223f6f) — an eval-driven, PDCA-native approach to AI transformation that works backwards from business outcomes.

> *"The only AI transformation framework that treats 'knowing when to kill the project' as a success metric."*

## Core Concept: Eval-First Transformation

Every AI initiative must earn the right to act — progressing through bounded autonomy levels (L0 Inform → L1 Recommend → L2 Oversight → L3 Autonomous) based on measurable eval evidence, not hope.

## Quick Start

```bash
pip install -e .
ai-kaizen init "Predictive Maintenance - Line 3"
ai-kaizen assess data-readiness
ai-kaizen outcome set --metric "MTBF" --baseline "72h" --target "96-120h"
ai-kaizen eval scaffold --level 0
ai-kaizen pdca start discovery
ai-kaizen status
```

## Commands

| Command | Description |
|---------|-------------|
| `ai-kaizen init` | Create a new transformation initiative |
| `ai-kaizen select` | Set the current working initiative |
| `ai-kaizen assess` | Run data readiness or cultural assessments |
| `ai-kaizen outcome` | Define and track business outcomes |
| `ai-kaizen eval` | Scaffold eval suites, record results |
| `ai-kaizen pdca` | Track PDCA loops, log entries, check gates |
| `ai-kaizen status` | Portfolio dashboard or initiative deep-dive |
| `ai-kaizen export` | Generate markdown/JSON reports |

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

## Project Structure

```
ai-kaizen/
├── src/ai_kaizen/
│   ├── cli.py              # Click CLI entry point
│   ├── domain/models.py    # Pydantic domain models
│   ├── store/              # SQLite persistence (WAL mode)
│   ├── services/           # Business logic layer
│   ├── commands/           # Thin CLI adapters
│   └── scaffolds/          # Jinja2 eval templates
├── docs/
│   ├── framework-v2.md     # Full framework document
│   └── research.md         # Foundation research
└── tests/
```

## Research & Framework

- [Foundation Research: Kaizen, Gemba, AI/ML](https://gist.github.com/KevinCrosby/beacb8f1ac0cb5dfcd63c7d0c79c9bba)
- [AI-Kaizen Framework v2](https://gist.github.com/KevinCrosby/6c409ca5cc5102a0b675d30ab2223f6f)

## How People Use This

### The Core Workflow

**1. Start an initiative**
```bash
ai-kaizen init "Predictive Maintenance - Packaging Line 3"
```
Names and tracks a transformation initiative with severity class, autonomy target, and ownership.

**2. Assess readiness**
```bash
ai-kaizen assess data-readiness
```
Interactive scorecard (0-18) across 6 dimensions — existence, accessibility, quality, latency, history, coverage. Outputs a go/no-go recommendation before you invest.

**3. Define the outcome you're working backwards from**
```bash
ai-kaizen outcome set --metric "MTBF" --baseline "72h" --target "96-120h" --scope "Lines 1-4, Building B"
```
Forces specificity: what metric, what baseline, what target range, what operating envelope, what confounders.

**4. Scaffold your eval suite**
```bash
ai-kaizen eval scaffold --level 0   # Safety invariants (prompt injection, PII, blast radius)
ai-kaizen eval scaffold --level 1   # Feature assertions (start with 10-15, grow from production)
```
Generates actual pytest files with the 5-level eval structure pre-populated with domain-relevant stubs.

**5. Track PDCA loops**
```bash
ai-kaizen pdca start discovery
ai-kaizen pdca log --phase plan --note "Data readiness scored 11/18; scoping to sensor-rich lines only"
ai-kaizen pdca gate                  # Checks kill criteria — tells you: proceed, hold, or kill
```
Three nested loops: Discovery (2-4 weeks) → Validation (6-12 weeks) → Scaling (ongoing). Gate checks enforce kill criteria automatically.

**6. Monitor across initiatives**
```bash
ai-kaizen status                     # Portfolio dashboard: all initiatives at a glance
ai-kaizen status --initiative pred-maint-line3   # Deep dive: evals, overrides, autonomy level, ROI confidence
```

### Who Uses What

| Role | They Use | To Do |
|------|----------|-------|
| **VP Operations** | `status`, `pdca gate` | Portfolio oversight, go/no-go decisions |
| **Transformation Owner** | `init`, `outcome`, `pdca` | Define initiatives, track PDCA loops, decide promotions |
| **AI/Eval Engineer** | `eval scaffold`, `eval record` | Build and maintain eval suites |
| **Frontline Supervisor** | Gate reports, override logs | Validate agent performance against floor reality |

### The Key Idea

**AI must earn the right to act.** Every agent starts at L0 (inform only) and can only advance to L1 → L2 → L3 autonomy by passing progressively harder eval gates — with operations leadership (not the AI team) making the promotion call based on evidence.

The toolkit enforces this: no skipping levels, no vibes-based promotion, explicit kill criteria at every gate.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
