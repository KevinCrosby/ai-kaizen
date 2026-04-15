#!/usr/bin/env bash
# seed-healthcare-portfolio.sh
#
# Seeds an AI-Kaizen database with a realistic 2-initiative healthcare
# portfolio template. Use as a reference for how to structure initiatives,
# outcomes, eval suites, PDCA loops, and PMO scoring.
#
# Usage:
#   export AI_KAIZEN_DB=./demo.db   # optional: use a dedicated DB
#   bash examples/seed-healthcare-portfolio.sh
#
# Initiatives:
#   1. Radiology AI Triage (S0) — Discovery → Validation, with full PDCA + evals
#   2. Pharma Prior Auth Automation (S1) — Discovery loop in progress
#
set -euo pipefail

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  AI-Kaizen Template: Healthcare Imaging + Pharma Portfolio  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────────────────────────
# INITIATIVE 1: Radiology AI Triage
# ─────────────────────────────────────────────────────────────────────
echo "▸ Creating Initiative 1: Radiology AI Triage..."

ai-kaizen init "Radiology AI Triage - ED Chest X-rays" \
  -d "AI-assisted prioritization of emergency department chest X-rays to flag critical findings (pneumothorax, large effusions, widened mediastinum) for immediate radiologist review." \
  -s S0

# Data Readiness (13/18)
ai-kaizen assess data-readiness \
  --existence 3 --accessibility 2 --quality 2 \
  --latency 2 --history 3 --coverage 1 \
  --notes "PACS 5yr CXR with reports. DICOMweb API (manual auth). NLP-extracted labels ~15% ambiguous. 2-4 min acquisition lag. Night/weekend coverage gaps."

# Outcomes
ai-kaizen outcome set \
  --metric "Time-to-radiologist-read for critical CXR findings" \
  --baseline "4.2 hours average (ED, 7pm-7am shift)" \
  --target "Under 30 minutes for AI-flagged critical" \
  --scope "Emergency Department chest X-rays, Memorial Hospital main campus" \
  --timeframe "6 months from pilot start" \
  --confidence "95% CI on median improvement" \
  --constraint "FN rate < 2% (FDA 510(k) benchmark); FP rate < 15%"

ai-kaizen outcome set \
  --metric "Critical finding miss rate" \
  --baseline "8.3% miss rate on overnight CXR reads" \
  --target "Below 3% with AI-assist" \
  --scope "Pneumothorax, large pleural effusion, widened mediastinum" \
  --timeframe "12 months" \
  --constraint "No increase in total read time; no degradation of non-critical accuracy"

# Eval Suites
ai-kaizen eval scaffold --level L0 \
  -d "Safety: prompt injection, PII/DICOM header leakage, fail-safe on low confidence"
ai-kaizen eval scaffold --level L1 \
  -d "Assertions: per-pathology sensitivity/specificity, edge cases, calibration"
ai-kaizen eval scaffold --level L2 \
  -d "Human+Model: radiologist agreement, LLM-as-judge report quality, override analysis"

# Discovery PDCA
ai-kaizen pdca start discovery

ai-kaizen pdca log --phase plan \
  --note "Scoped to ED CXR. Data readiness 13/18. Identified 3 commercial models + 1 in-house. 510(k) required for autonomous; exempt for radiologist-in-the-loop."

ai-kaizen pdca log --phase do \
  --note "Retrospective: 12,000 CXR, NLP labels 94% clean. Gold standard: 847 pneumothorax, 1,203 effusion, 312 mediastinum, 9,638 negative. 70/15/15 split stratified by shift."

ai-kaizen pdca log --phase check \
  --note "ResNet-50 baseline: Pneumothorax AUC 0.94, Effusion 0.91, Mediastinum 0.87. Night shift -4%. FN rate 4.1% (above 2% target). Poor calibration >0.8."

ai-kaizen pdca log --phase act \
  --note "Proceed to Validation. Actions: augment night-shift data, switch to EfficientNet-B4, add temperature scaling, establish radiologist panel."

# Discovery Eval Runs
ai-kaizen eval record --level L0 --total 24 --passed 24 \
  --notes "All safety invariants pass. No PII in outputs, DICOM stripping verified, graceful degradation."

ai-kaizen eval record --level L1 --total 45 --passed 38 \
  --notes "Failures: 3 portable CXR, 2 pediatric, 2 post-surgical FP. FN rate 4.1%."

ai-kaizen eval record --level L2 --total 100 --passed 82 \
  --notes "Radiologist panel (n=4): 82% agreement. Disagreements on subtle effusions and post-op."

# PMO Score
ai-kaizen pmo score \
  -V 5 -B 4 -D 3 -C 3 -R 4 -X 2 -P 4 \
  --notes "High clinical value. Strong baselines. Data gaps. Moderate change risk. High compliance (FDA/HIPAA). Good reuse potential."

# ROI: Projected
ai-kaizen roi track \
  --value-created 1800000 --value-captured 420000 --tco 650000 \
  --confidence projected \
  --notes "12 avoided adverse events/yr × \$150K. 15% night throughput increase. TCO: hosting, integration, panel, regulatory."

# Validation PDCA
ai-kaizen pdca start validation

ai-kaizen pdca log --phase plan \
  --note "8-week prospective pilot, ED night shift. AI advisory (L1). Endpoints: FN rate, time-to-read, satisfaction. IRB exempt (QI)."

ai-kaizen pdca log --phase do \
  --note "Wk 1-4 shadow: 2,847 CXR, 342 flagged (12%), 87.1% agreement, FN 0.9%. Wk 5-8 advisory (L1): 18 min median time-to-read, override 8.2%, satisfaction 4.1/5."

ai-kaizen pdca log --phase check \
  --note "All targets met: time-to-read 18 min (<30), FN 0.9% (<2%), FP 12% (<15%). Small sample risk — need 6mo seasonal validation."

ai-kaizen pdca log --phase act \
  --note "Advance to Scaling. L1 only — no L2 until 6mo data. Roll out day shift + campus 2. Begin FDA pre-sub. Monthly calibration monitoring."

# Validation Eval Runs
ai-kaizen eval record --level L0 --total 28 --passed 28 \
  --notes "+4 new safety tests for live deployment. All pass."

ai-kaizen eval record --level L1 --total 52 --passed 49 \
  --notes "+7 tests from validation. 3 remaining failures: rare portable CXR artifacts."

ai-kaizen eval record --level L2 --total 150 --passed 136 \
  --notes "Panel (n=6): 90.7% agreement. LLM-judge 4.2/5. 62% overrides on borderline cases."

# ROI: Estimated (post-validation)
ai-kaizen roi track \
  --value-created 1800000 --value-captured 680000 --tco 520000 \
  --confidence estimated \
  --notes "Night throughput +22% (beat projection). Open-source model reduced TCO."


# ─────────────────────────────────────────────────────────────────────
# INITIATIVE 2: Pharma Prior Authorization Automation
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "▸ Creating Initiative 2: Pharma Prior Auth Automation..."

ai-kaizen init "Pharma Prior Authorization Automation" \
  -d "Agent-assisted prior auth for specialty pharmacy. Automates criteria matching, formulary lookup, and appeal letter generation." \
  -s S1

# Data Readiness (15/18)
ai-kaizen assess data-readiness \
  --existence 3 --accessibility 3 --quality 2 \
  --latency 3 --history 2 --coverage 2 \
  --notes "Claims in EDW, formulary in Medi-Span. Clinical criteria PDFs need extraction. Real-time eligibility API. 2yr PA decisions. Specialty biologics criteria change quarterly."

# Outcomes
ai-kaizen outcome set \
  --metric "Prior authorization turnaround time" \
  --baseline "72 hours average (specialty pharmacy)" \
  --target "Under 4 hours for auto-adjudicable requests" \
  --scope "Specialty pharmacy — oncology, rheumatology, neurology top 50 drugs" \
  --timeframe "9 months" \
  --constraint "Accuracy >= 94.2% (human baseline); denial rate must not increase"

ai-kaizen outcome set \
  --metric "Pharmacist time per prior auth" \
  --baseline "22 minutes average" \
  --target "Under 5 minutes for AI-assisted" \
  --scope "Same drug scope" \
  --timeframe "9 months" \
  --constraint "Pharmacist reviews all AI recommendations; no autonomous submissions for 12 months"

# Eval Suites
ai-kaizen eval scaffold --level L0 \
  -d "Safety: PHI handling, formulary integrity, denial accuracy, fail-safe to human"
ai-kaizen eval scaffold --level L1 \
  -d "Assertions: criteria matching per drug class, appeal letter quality, formulary lookup"

# Discovery PDCA
ai-kaizen pdca start discovery

ai-kaizen pdca log --phase plan \
  --note "Top 50 specialty drugs, 8 major payers (82% volume). RAG over 340 formulary docs. Agent: criteria extraction → eligibility → clinical match → draft → pharmacist queue."

ai-kaizen pdca log --phase do \
  --note "RAG pipeline: criteria extraction 91% oncology, 87% rheumatology, 84% neurology. Criteria-to-chart matching 88% (n=500). Errors: step-therapy sequences, weight-based dosing."

# Eval Runs
ai-kaizen eval record --level L0 --total 18 --passed 18 \
  --notes "PHI redacted, no hallucinated criteria, graceful fallback, audit trail complete."

ai-kaizen eval record --level L1 --total 35 --passed 30 \
  --notes "Failures: 3 step-therapy, 2 weight-based dosing. Matching 88% (below 90% S1 target)."

# PMO Score
ai-kaizen pmo score \
  -V 4 -B 4 -D 4 -C 4 -R 5 -X 3 -P 3 \
  --notes "#1 pharmacist complaint. Good baselines. Accessible data. Highly reversible. Moderate compliance (state regs vary)."

# ROI: Projected
ai-kaizen roi track \
  --value-created 2400000 --value-captured 0 --tco 380000 \
  --confidence projected \
  --notes "4 FTE pharmacist savings (\$600K/yr) + faster therapy access. Pre-validation."


# ─────────────────────────────────────────────────────────────────────
# Portfolio Summary
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Portfolio seeded! View with:                    ║"
echo "║                                                  ║"
echo "║  ai-kaizen status          # portfolio overview  ║"
echo "║  ai-kaizen pmo rank        # prioritized backlog ║"
echo "║  ai-kaizen roi portfolio   # ROI summary         ║"
echo "║  ai-kaizen serve           # web dashboard       ║"
echo "╚══════════════════════════════════════════════════╝"

ai-kaizen pmo rank
echo ""
ai-kaizen roi portfolio
