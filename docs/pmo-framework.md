# AI-Kaizen PMO Framework: Portfolio Prioritization & ROI Measurement

> *"Organizations don't fail at running one AI initiative — they fail at choosing the right 3-5 and saying no to the rest."*

---

## 1. The Portfolio Problem

The AI-Kaizen Framework v2 tells you how to run **an initiative**. This PMO framework tells you how to:
- **Select** the right initiatives from a pipeline of candidates
- **Prioritize** based on value, feasibility, and risk
- **Allocate** constrained resources (data engineering, eval engineering, ops time)
- **Measure** ROI across the portfolio — not just per-initiative
- **Kill** underperformers early and reallocate to higher-value work
- **Cap WIP** to prevent pilot sprawl

---

## 2. Initiative Intake: The Scoring Rubric

Every candidate initiative is scored across **7 dimensions** before entering the portfolio. Each dimension is scored 1-5.

### 2.1 Scoring Dimensions

| # | Dimension | What It Measures | Score 1 (Low) | Score 5 (High) |
|---|-----------|-----------------|---------------|-----------------|
| **V** | **Business Value** | Quantifiable impact on revenue, cost, quality, safety, or compliance | Marginal improvement; hard to quantify | >$500K/yr impact; clear causal link to KPI |
| **B** | **Baseline Measurability** | Can we measure the current state reliably? | No baseline exists; would need 6+ months to establish | Baseline already tracked in existing systems with 12+ months of data |
| **D** | **Data Readiness** | Layer 0 Data Readiness Score mapped to 1-5 | Score 0-4 (fundamental gaps) | Score 15-18 (production-ready) |
| **C** | **Change Readiness** | Stakeholder willingness, cultural fit, prior AI experience | Active resistance; failed prior AI initiative; no sponsor | Champion in operations; positive prior experience; exec sponsor secured |
| **R** | **Reversibility** | How easily can we undo a bad deployment? | Irreversible actions (safety, regulatory filings, customer-facing) | Purely advisory (L0 inform); no downstream action |
| **X** | **Compliance Burden** | Regulatory, legal, and audit requirements | FDA/ISO validation required; multi-month approval cycles | No regulatory constraints; internal process only |
| **P** | **Platform Reuse** | Does this build capabilities other initiatives can use? | One-off; bespoke to specific process | Builds shared eval infra, data pipelines, or agent patterns usable by 3+ future initiatives |

### 2.2 The Initiative Score

```
INITIATIVE SCORE = (V × 2) + B + D + C + R + (6 - X) + P
                   ─────────────────────────────────────────
                              Max possible: 40

Weights:
  Business Value gets 2× weight (it's the reason we're doing this)
  Compliance Burden is inverted (lower burden = higher score)
```

| Score Range | Recommendation |
|-------------|---------------|
| 30-40 | **Fast-track:** Enter Discovery loop immediately |
| 22-29 | **Qualified:** Enter backlog; start when capacity opens |
| 15-21 | **Conditional:** Requires remediation on weakest dimension before intake |
| Below 15 | **Decline:** Not viable for AI transformation at this time |

### 2.3 The Initiative Canvas (One-Page Intake)

Every candidate must complete this before scoring:

```
╔══════════════════════════════════════════════════════════════╗
║  AI-KAIZEN INITIATIVE CANVAS                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Initiative Name: _________________________________________  ║
║  Sponsor (Ops):   _________________________________________  ║
║  Date:            _________________________________________  ║
║                                                              ║
║  ┌─────────────────────────┬───────────────────────────┐    ║
║  │  OUTCOME (Layer 5)      │  DATA READINESS (Layer 0) │    ║
║  │                         │                           │    ║
║  │  Metric: ______________ │  Existence:    [ ]/3      │    ║
║  │  Baseline: ____________ │  Accessibility:[ ]/3      │    ║
║  │  Target: ______________ │  Quality:      [ ]/3      │    ║
║  │  Timeframe: ___________ │  Latency:      [ ]/3      │    ║
║  │  Scope: _______________ │  History:      [ ]/3      │    ║
║  │                         │  Coverage:     [ ]/3      │    ║
║  │                         │  TOTAL:        [ ]/18     │    ║
║  ├─────────────────────────┼───────────────────────────┤    ║
║  │  SEVERITY CLASS         │  STARTING AUTONOMY        │    ║
║  │                         │                           │    ║
║  │  [ ] S0: Safety         │  [ ] L0: Inform           │    ║
║  │  [ ] S1: Production     │  [ ] L1: Recommend        │    ║
║  │  [ ] S2: Efficiency     │  [ ] L2: Oversight        │    ║
║  │  [ ] S3: Advisory       │  [ ] L3: Autonomous       │    ║
║  ├─────────────────────────┼───────────────────────────┤    ║
║  │  KILL CRITERIA          │  ESTIMATED INVESTMENT     │    ║
║  │                         │                           │    ║
║  │  1. __________________ │  Discovery:  $________     │    ║
║  │  2. __________________ │  Validation: $________     │    ║
║  │  3. __________________ │  Year 1 TCO: $________     │    ║
║  ├─────────────────────────┴───────────────────────────┤    ║
║  │  STAKEHOLDERS                                        │    ║
║  │                                                      │    ║
║  │  Transformation Owner: _____________________________ │    ║
║  │  Key Operators:        _____________________________ │    ║
║  │  AI/Eval Lead:         _____________________________ │    ║
║  │  Exec Sponsor:         _____________________________ │    ║
║  ├──────────────────────────────────────────────────────┤    ║
║  │  SCORING (filled by PMO)                             │    ║
║  │                                                      │    ║
║  │  V:__ B:__ D:__ C:__ R:__ X:__ P:__ TOTAL: __/40   │    ║
║  │  Recommendation: [ ] Fast-track [ ] Qualified        │    ║
║  │                  [ ] Conditional [ ] Decline          │    ║
║  └──────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 3. Portfolio Prioritization

### 3.1 The Prioritization Matrix

After scoring, plot initiatives on a 2×2 matrix:

```
                    HIGH VALUE (V ≥ 8)
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         │   STRATEGIC    │   FAST-TRACK  │
         │   BETS         │   (Do First)  │
         │               │               │
         │  High value,   │  High value,  │
         │  low feasib.   │  high feasib. │
         │  → Invest in   │  → Start now  │
         │    readiness   │               │
LOW ─────┼───────────────┼───────────────┼───── HIGH
FEASIB.  │               │               │  FEASIBILITY
(D+C+R   │   DECLINE     │   QUICK WINS  │  (D+C+R+B ≥ 14)
+B < 14) │   (Don't Do)  │   (Fill Gaps)  │
         │               │               │
         │  Low value,    │  Low value,   │
         │  low feasib.   │  high feasib. │
         │  → Say no      │  → Only if    │
         │               │    builds      │
         │               │    platform    │
         └───────────────┼───────────────┘
                         │
                    LOW VALUE (V < 8)
```

### 3.2 WIP Limits

**Critical rule:** Cap active initiatives based on organizational capacity.

| Org Size | Max Active Initiatives | Max in Discovery | Max in Validation | Max in Scaling |
|----------|----------------------|-----------------|-------------------|----------------|
| Small (< 500 employees) | 2 | 1 | 1 | 1 |
| Medium (500-5,000) | 3-5 | 2 | 2 | 3 |
| Large (5,000+) | 5-8 | 3 | 3 | 5 |

**Why WIP limits matter:** Every active initiative consumes data engineering, eval engineering, and ops leadership time. Without limits, you get "pilot sprawl" — 12 initiatives, all at Discovery, none reaching Validation.

**The bottleneck is almost always data engineering and domain expert time**, not AI engineering. Size your WIP to these constraints.

### 3.3 Sequencing Rules

1. **Fast-Track quadrant first** — highest value, most feasible
2. **Platform builders before consumers** — if Initiative A builds shared eval infra that Initiative B needs, do A first (even if B scores higher)
3. **One S0/S1 initiative at a time** — safety/production-critical work demands disproportionate attention
4. **Stagger Discovery starts by 2-4 weeks** — don't compete for the same stakeholders during intake

---

## 4. ROI Measurement System

### 4.1 The Three Levels of ROI

| Level | What It Measures | When You Have It | Accuracy |
|-------|-----------------|-----------------|----------|
| **Projected ROI** | Expert estimates + analogy to similar initiatives | At intake (Initiative Canvas) | ±50% |
| **Estimated ROI** | Leading indicators from Validation loop data | After 8+ weeks of L1+L2 eval data | ±30% |
| **Measured ROI** | Controlled experiment results (Level 3 eval) | After Scaling loop experiment | ±15% |

### 4.2 ROI Calculation

```
                    ┌──────────────────────────────────────┐
                    │         PORTFOLIO ROI MODEL           │
                    ├──────────────────────────────────────┤
                    │                                      │
  PER INITIATIVE:   │  Value Created                       │
                    │    = Σ (KPI improvement × unit value) │
                    │                                      │
                    │  Value Captured                       │
                    │    = Value Created × Capture Rate     │
                    │    (Did someone act on it?)           │
                    │                                      │
                    │  Net Value                            │
                    │    = Value Captured - Initiative TCO  │
                    │                                      │
                    │  ROI                                  │
                    │    = Net Value / Initiative TCO       │
                    │                                      │
  PORTFOLIO:        │  Portfolio ROI                        │
                    │    = Σ Net Value (all initiatives)    │
                    │      / Σ TCO (all initiatives)        │
                    │                                      │
                    │  Includes killed initiatives!         │
                    │  (Discovery spend on killed projects  │
                    │   is a FEATURE, not waste — you       │
                    │   learned cheaply what doesn't work)  │
                    └──────────────────────────────────────┘
```

### 4.3 The Value Tracking Table

Each initiative tracks value at every PDCA checkpoint:

| Initiative | Loop | Confidence | Value Created | Value Captured | Capture Rate | TCO to Date | Net Value | ROI |
|-----------|------|-----------|--------------|---------------|-------------|------------|-----------|-----|
| Pred. Maint. Line 3 | Validation | Estimated | $420K/yr | $290K/yr | 69% | $380K | -$90K | -24% |
| QC Defect Triage | Scaling | Measured | $680K/yr | $610K/yr | 90% | $520K | +$90K | +17% |
| Gemba Walk Assist | Discovery | Projected | $150K/yr | TBD | TBD | $45K | TBD | TBD |

**Key insight: Track "Value Created" and "Value Captured" separately.** Most programs fail at capture, not creation. If your agent identifies $420K in value but only $290K is captured, the problem isn't the agent — it's adoption, workflow integration, or incentive alignment.

### 4.4 Leading vs. Lagging Indicators

| Indicator Type | Metrics | Update Cadence | Who Owns |
|---------------|---------|---------------|----------|
| **Leading** (predict future ROI) | Eval pass rates, override rate trend, agent utilization, time-to-action, operator satisfaction | Weekly | Eval Engineer + Agent Operator |
| **Lagging** (confirm actual ROI) | MTBF, defect rate, throughput, downtime hours, cost-per-unit, energy consumption | Monthly | Operations Leadership |
| **Portfolio Health** | Active vs. WIP limit, kill rate, avg time in Discovery, capture rate trend | Monthly | PMO |

### 4.5 The ROI Confidence Progression

Every initiative must progress through confidence levels. **Stuck confidence = stuck initiative.**

```
PROJECTED (±50%)                    ESTIMATED (±30%)
    │                                   │
    │  Gate: Discovery → Validation     │  Gate: Validation → Scaling
    │  Evidence: Expert estimates +     │  Evidence: 8+ weeks of L1+L2
    │  data readiness score             │  eval data + leading indicators
    │                                   │
    ▼                                   ▼
MEASURED (±15%)                     VALIDATED (±10%)
    │                                   │
    │  Gate: Scaling experiment done    │  Gate: 2+ quarters production
    │  Evidence: Controlled experiment  │  Evidence: Sustained KPI movement
    │  (A/B, DiD, or stepped-wedge)    │  with confounder tracking
    │                                   │
    ▼                                   ▼
  GO/NO-GO for sustained investment    Annual budget justification
```

---

## 5. Portfolio-Level PDCA

The PMO runs its own PDCA cycle at the portfolio level:

### 5.1 Monthly Portfolio Review

| Agenda Item | Time | Owner |
|-------------|------|-------|
| **Status sweep** — each initiative: loop, phase, eval scores, blockers | 15 min | PMO |
| **Kill/pivot decisions** — any initiative hitting kill criteria? | 10 min | Exec Sponsor |
| **Capacity check** — are we within WIP limits? Any bottlenecks? | 10 min | PMO |
| **Pipeline review** — new candidates scored? Sequencing changes? | 10 min | PMO |
| **ROI update** — portfolio-level value created, captured, net | 10 min | Finance + Ops |
| **Action items** — decisions made, owners assigned | 5 min | PMO |

### 5.2 Quarterly Portfolio Retrospective

| Question | What You're Looking For |
|----------|----------------------|
| Which initiatives advanced a loop this quarter? | Velocity — are things moving? |
| Which initiatives are stuck? Why? | Bottleneck identification |
| What did we kill? What did we learn? | Learning capture — kills are data, not failure |
| Is our scoring rubric predicting success? | Calibration — are high-scoring initiatives actually performing? |
| Are we building platform capabilities or just one-offs? | Strategic alignment |
| What's our capture rate trend? | Adoption health — is the organization acting on AI outputs? |

### 5.3 Annual Portfolio Reset

| Action | Purpose |
|--------|---------|
| Re-score all active initiatives | Conditions change; scores should too |
| Refresh the candidate pipeline | New problems, new capabilities, new data sources |
| Update TCO actuals vs. projections | Calibrate future estimates |
| Publish "State of AI Transformation" report | Transparency, executive alignment, celebrate wins + honest about gaps |
| Adjust WIP limits based on demonstrated capacity | Growth or contraction based on evidence |

---

## 6. Effort Estimation Model

### 6.1 Initiative T-Shirt Sizing

Before detailed TCO, use t-shirt sizes to roughly allocate:

| Size | Discovery Cost | Validation Cost | Year 1 TCO | Typical Scope |
|------|---------------|----------------|------------|---------------|
| **S** | $20-50K | $80-150K | $150-300K | Single process, clean data, L0-L1 autonomy, S2-S3 severity |
| **M** | $50-100K | $150-350K | $300-700K | Multi-process, moderate data work, L0-L2 autonomy, S1-S2 severity |
| **L** | $100-200K | $350-600K | $700K-1.5M | Cross-functional, significant data infra, L0-L3 autonomy target, S0-S1 severity |
| **XL** | $200K+ | $600K+ | $1.5M+ | Multi-site, new data infrastructure build, regulatory requirements |

### 6.2 Effort Allocation by Role

| Role | Discovery (%) | Validation (%) | Scaling (%) |
|------|--------------|----------------|-------------|
| AI/Agent Engineer | 30% | 40% | 20% |
| Eval Engineer | 20% | 30% | 25% |
| Data Engineer | 30% | 20% | 15% |
| Domain Expert (Ops) | 10% | 5% | 10% |
| Change Management | 5% | 3% | 10% |
| Agent Operator | 0% | 2% | 20% |
| PMO / Oversight | 5% | 0% | 0% |

**Key takeaway:** Data engineering dominates Discovery; AI engineering dominates Validation; operations (agent operator + change management) dominates Scaling.

### 6.3 Cost-Per-Initiative vs. Cost-Per-Portfolio

| Cost Type | Per-Initiative | Portfolio (Shared) |
|-----------|---------------|-------------------|
| Agent development | ✅ | |
| Domain-specific evals | ✅ | |
| Data integration (source-specific) | ✅ | |
| Trace logging infrastructure | | ✅ Build once, reuse |
| Eval CI/CD pipeline | | ✅ Build once, reuse |
| Level 2 review tooling | | ✅ Build once, reuse |
| Monitoring / alerting | | ✅ Build once, reuse |
| PMO overhead | | ✅ Amortized across initiatives |
| Training / change management templates | | ✅ Build once, customize |

**This is why "Platform Reuse" (P) is a scoring dimension.** Early initiatives that build shared infrastructure reduce the cost of every subsequent initiative by 30-50%.

---

## 7. PMO Dashboard Metrics

### 7.1 Portfolio Health Scorecard

```
╔══════════════════════════════════════════════════════════════╗
║  AI-KAIZEN PORTFOLIO DASHBOARD                               ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ACTIVE: 4/5 (WIP limit)    PIPELINE: 7 candidates          ║
║  KILLED THIS QTR: 1          AVG DISCOVERY TIME: 3.2 weeks  ║
║                                                              ║
║  ┌──────────────────────────────────────────────────┐       ║
║  │  Initiative          Loop       Phase   Score    │       ║
║  │  ─────────────────── ────────── ─────── ──────── │       ║
║  │  Pred Maint Line 3   Validation Check   32/40   │       ║
║  │  QC Defect Triage    Scaling    Do      28/40   │       ║
║  │  Gemba Walk Assist   Discovery  Plan    24/40   │       ║
║  │  Energy Optimizer    Discovery  Do      22/40   │       ║
║  │  ⊘ Inventory Agent   KILLED     —       19/40   │       ║
║  └──────────────────────────────────────────────────┘       ║
║                                                              ║
║  PORTFOLIO ROI                                               ║
║  ────────────                                                ║
║  Value Created (annualized):   $1.25M                       ║
║  Value Captured (annualized):  $900K                        ║
║  Capture Rate:                 72%                           ║
║  Total TCO (YTD):              $945K                        ║
║  Portfolio Net Value (YTD):    -$45K (expected: breakeven Q3)║
║                                                              ║
║  HEALTH SIGNALS                                              ║
║  ────────────                                                ║
║  ⚠ Energy Optimizer: data readiness score dropped to 8/18   ║
║  ✓ QC Defect Triage: L3 experiment shows +18% defect catch  ║
║  ⚠ Capture rate trending down (was 78% last quarter)        ║
╚══════════════════════════════════════════════════════════════╝
```

### 7.2 Key Portfolio Metrics

| Metric | Target | Red Flag |
|--------|--------|----------|
| **Active ≤ WIP limit** | Always | Any breach means something must be paused or killed |
| **Avg time in Discovery** | 2-4 weeks | >6 weeks = scope creep or data readiness hell |
| **Kill rate** | 20-40% of initiatives | <10% = not killing bad ideas; >50% = bad intake scoring |
| **Capture rate** | >70% | <50% = adoption problem, not AI problem |
| **Portfolio ROI (annual)** | >1.5x by Year 2 | <1.0x after Year 2 = structural issue |
| **Platform reuse rate** | >30% of infra shared | <10% = building one-offs; will not scale |
| **Scoring calibration** | Top-scored initiatives outperform | If low-scored initiatives outperform, recalibrate rubric |

---

## 8. CLI Commands (PMO Extension)

```bash
# Pipeline management
ai-kaizen pmo intake                           # Interactive initiative canvas + scoring
ai-kaizen pmo score --initiative "energy-opt"  # Score or re-score an initiative
ai-kaizen pmo rank                             # Show prioritized backlog

# Portfolio operations
ai-kaizen pmo dashboard                        # Portfolio health scorecard
ai-kaizen pmo capacity                         # WIP limit check + bottleneck analysis
ai-kaizen pmo review                           # Generate monthly review agenda

# ROI tracking
ai-kaizen roi track --initiative "pred-maint" --value-created 420000 --value-captured 290000
ai-kaizen roi portfolio                        # Portfolio-level ROI summary
ai-kaizen roi confidence --initiative "pred-maint"  # Show confidence progression

# Effort estimation
ai-kaizen pmo estimate --size M --severity S1  # T-shirt size → cost estimate
```

---

## Appendix: Mapping to Common PMO Frameworks

| If You Use... | AI-Kaizen PMO Maps To... |
|--------------|--------------------------|
| **PMI/PMBOK** | Initiative Canvas = Project Charter; Scoring = Business Case; PDCA Loops = Phase Gates; Kill Criteria = Termination Criteria |
| **SAFe** | Portfolio = Portfolio Kanban; WIP Limits = SAFe WIP; Scoring = WSJF (Weighted Shortest Job First); Discovery = PI Planning |
| **OKR** | Outcome Statement = Key Result; Initiative Score = Confidence Level; Portfolio Review = OKR Check-in |
| **Hoshin Kanri** | Scoring = Catchball; Portfolio PDCA = Annual Hoshin cycle; Monthly Review = Monthly Hoshin review |
| **Six Sigma** | Severity Classes = DPMO tiers; Eval Levels = Control Plan; Kill Criteria = Tollgate exit criteria |
