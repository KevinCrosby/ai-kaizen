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
