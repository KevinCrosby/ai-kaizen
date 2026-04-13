"""Domain models for AI-Kaizen toolkit."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---

class SeverityClass(str, enum.Enum):
    S0_SAFETY = "S0"
    S1_PRODUCTION = "S1"
    S2_EFFICIENCY = "S2"
    S3_ADVISORY = "S3"


class AutonomyLevel(str, enum.Enum):
    L0_INFORM = "L0"
    L1_RECOMMEND = "L1"
    L2_OVERSIGHT = "L2"
    L3_AUTONOMOUS = "L3"


class PDCALoop(str, enum.Enum):
    DISCOVERY = "discovery"
    VALIDATION = "validation"
    SCALING = "scaling"


class PDCAPhase(str, enum.Enum):
    PLAN = "plan"
    DO = "do"
    CHECK = "check"
    ACT = "act"


class EvalLevel(str, enum.Enum):
    L0_SAFETY = "L0"
    L1_ASSERTIONS = "L1"
    L2_HUMAN_MODEL = "L2"
    L2_5_MONITORING = "L2.5"
    L3_EXPERIMENT = "L3"


class InitiativeStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    KILLED = "killed"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class GateResult(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TechMaturity(str, enum.Enum):
    PROVEN = "proven"
    EMERGING = "emerging"
    EXPERIMENTAL = "experimental"


# --- Core Entities ---

class Initiative(BaseModel):
    id: str
    name: str
    description: str = ""
    severity_class: SeverityClass = SeverityClass.S2_EFFICIENCY
    autonomy_level: AutonomyLevel = AutonomyLevel.L0_INFORM
    current_loop: PDCALoop = PDCALoop.DISCOVERY
    current_phase: PDCAPhase = PDCAPhase.PLAN
    status: InitiativeStatus = InitiativeStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Outcome(BaseModel):
    id: str
    initiative_id: str
    metric: str
    baseline: str
    target_range: str
    confidence_target: str = ""
    timeframe: str = ""
    scope: str = ""
    constraint: str = ""
    operating_envelope: str = ""
    known_confounders: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EvalSuite(BaseModel):
    id: str
    initiative_id: str
    level: EvalLevel
    description: str = ""
    assertion_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvalRun(BaseModel):
    id: str
    suite_id: str
    initiative_id: str
    level: EvalLevel
    total: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: float = 0.0
    notes: str = ""
    commit_ref: str = ""
    run_at: datetime = Field(default_factory=datetime.utcnow)


class PDCAEntry(BaseModel):
    id: str
    initiative_id: str
    loop: PDCALoop
    phase: PDCAPhase
    note: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GateDecision(BaseModel):
    id: str
    initiative_id: str
    loop: PDCALoop
    result: GateResult
    rationale: str = ""
    criteria_snapshot: str = ""  # JSON snapshot of criteria at decision time
    decided_at: datetime = Field(default_factory=datetime.utcnow)


class KillCriterion(BaseModel):
    id: str
    initiative_id: str
    signal: str
    threshold: str
    current_value: str = ""
    triggered: bool = False
    loop: Optional[PDCALoop] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Stakeholder(BaseModel):
    id: str
    initiative_id: str
    name: str
    role: str
    concern: str = ""
    engagement_status: str = "not_engaged"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DataReadiness(BaseModel):
    initiative_id: str
    existence: int = 0       # 0-3
    accessibility: int = 0   # 0-3
    quality: int = 0         # 0-3
    latency: int = 0         # 0-3
    history: int = 0         # 0-3
    coverage: int = 0        # 0-3
    notes: str = ""
    assessed_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def total_score(self) -> int:
        return self.existence + self.accessibility + self.quality + self.latency + self.history + self.coverage

    @property
    def recommendation(self) -> str:
        score = self.total_score
        if score >= 15:
            return "Proceed to outcome definition"
        elif score >= 10:
            return "Proceed with scoped outcomes; parallel-track data remediation"
        elif score >= 5:
            return "Data remediation project first; defer AI agent development"
        else:
            return "Fundamental infrastructure investment required before AI is viable"


class GembaObservation(BaseModel):
    id: str
    initiative_id: str
    category: str = ""       # accuracy, trust, blindspot, workflow, data_quality
    finding: str = ""
    eval_action: str = ""    # what eval to add/modify based on finding
    walk_date: datetime = Field(default_factory=datetime.utcnow)


# --- PMO / Portfolio Models ---

class TShirtSize(str, enum.Enum):
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


class IntakeRecommendation(str, enum.Enum):
    FAST_TRACK = "fast_track"
    QUALIFIED = "qualified"
    CONDITIONAL = "conditional"
    DECLINE = "decline"


class ROIConfidence(str, enum.Enum):
    PROJECTED = "projected"   # ±50%
    ESTIMATED = "estimated"   # ±30%
    MEASURED = "measured"     # ±15%
    VALIDATED = "validated"   # ±10%


class InitiativeScore(BaseModel):
    """7-dimension scoring rubric for initiative intake."""
    initiative_id: str
    business_value: int = Field(ge=1, le=5, description="V: Quantifiable business impact")
    baseline_measurability: int = Field(ge=1, le=5, description="B: Can we measure current state?")
    data_readiness: int = Field(ge=1, le=5, description="D: Layer 0 readiness mapped to 1-5")
    change_readiness: int = Field(ge=1, le=5, description="C: Stakeholder willingness + culture")
    reversibility: int = Field(ge=1, le=5, description="R: How easily can we undo bad deployment?")
    compliance_burden: int = Field(ge=1, le=5, description="X: Regulatory/legal requirements (1=heavy, 5=none)")
    platform_reuse: int = Field(ge=1, le=5, description="P: Builds shared capabilities?")
    scored_at: datetime = Field(default_factory=datetime.utcnow)
    notes: str = ""

    @property
    def total(self) -> int:
        return (self.business_value * 2) + self.baseline_measurability + \
               self.data_readiness + self.change_readiness + self.reversibility + \
               (6 - self.compliance_burden) + self.platform_reuse

    @property
    def recommendation(self) -> IntakeRecommendation:
        score = self.total
        if score >= 30:
            return IntakeRecommendation.FAST_TRACK
        elif score >= 22:
            return IntakeRecommendation.QUALIFIED
        elif score >= 15:
            return IntakeRecommendation.CONDITIONAL
        else:
            return IntakeRecommendation.DECLINE

    @property
    def value_score(self) -> int:
        """Business value (weighted 2×)."""
        return self.business_value * 2

    @property
    def feasibility_score(self) -> int:
        """Sum of D + C + R + B."""
        return self.data_readiness + self.change_readiness + \
               self.reversibility + self.baseline_measurability

    @property
    def quadrant(self) -> str:
        high_value = self.value_score >= 8
        high_feasibility = self.feasibility_score >= 14
        if high_value and high_feasibility:
            return "Fast-Track"
        elif high_value and not high_feasibility:
            return "Strategic Bet"
        elif not high_value and high_feasibility:
            return "Quick Win"
        else:
            return "Decline"


class ROIEntry(BaseModel):
    """Tracks ROI at a point in time for an initiative."""
    id: str
    initiative_id: str
    confidence: ROIConfidence = ROIConfidence.PROJECTED
    value_created: float = 0.0    # annualized
    value_captured: float = 0.0   # annualized
    tco_to_date: float = 0.0
    notes: str = ""
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def capture_rate(self) -> float:
        if self.value_created == 0:
            return 0.0
        return self.value_captured / self.value_created

    @property
    def net_value(self) -> float:
        return self.value_captured - self.tco_to_date

    @property
    def roi(self) -> float:
        if self.tco_to_date == 0:
            return 0.0
        return self.net_value / self.tco_to_date


class EffortEstimate(BaseModel):
    """T-shirt size effort estimation."""
    initiative_id: str
    size: TShirtSize
    discovery_cost_low: float = 0.0
    discovery_cost_high: float = 0.0
    validation_cost_low: float = 0.0
    validation_cost_high: float = 0.0
    year1_tco_low: float = 0.0
    year1_tco_high: float = 0.0
    notes: str = ""
    estimated_at: datetime = Field(default_factory=datetime.utcnow)


TSHIRT_COSTS: dict[TShirtSize, dict[str, tuple[float, float]]] = {
    TShirtSize.S: {
        "discovery": (20_000, 50_000),
        "validation": (80_000, 150_000),
        "year1_tco": (150_000, 300_000),
    },
    TShirtSize.M: {
        "discovery": (50_000, 100_000),
        "validation": (150_000, 350_000),
        "year1_tco": (300_000, 700_000),
    },
    TShirtSize.L: {
        "discovery": (100_000, 200_000),
        "validation": (350_000, 600_000),
        "year1_tco": (700_000, 1_500_000),
    },
    TShirtSize.XL: {
        "discovery": (200_000, 400_000),
        "validation": (600_000, 1_200_000),
        "year1_tco": (1_500_000, 3_000_000),
    },
}


# --- Threshold lookup ---

EVAL_THRESHOLDS: dict[SeverityClass, dict[EvalLevel, float]] = {
    SeverityClass.S0_SAFETY: {
        EvalLevel.L0_SAFETY: 1.0,
        EvalLevel.L1_ASSERTIONS: 0.95,
        EvalLevel.L2_HUMAN_MODEL: 0.90,
    },
    SeverityClass.S1_PRODUCTION: {
        EvalLevel.L0_SAFETY: 1.0,
        EvalLevel.L1_ASSERTIONS: 0.90,
        EvalLevel.L2_HUMAN_MODEL: 0.85,
    },
    SeverityClass.S2_EFFICIENCY: {
        EvalLevel.L0_SAFETY: 1.0,
        EvalLevel.L1_ASSERTIONS: 0.80,
        EvalLevel.L2_HUMAN_MODEL: 0.80,
    },
    SeverityClass.S3_ADVISORY: {
        EvalLevel.L0_SAFETY: 1.0,
        EvalLevel.L1_ASSERTIONS: 0.70,
        EvalLevel.L2_HUMAN_MODEL: 0.75,
    },
}
