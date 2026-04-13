"""Service layer — business logic between CLI and store."""

from __future__ import annotations

import re
import uuid
from typing import Optional

from ai_kaizen.domain.models import (
    EVAL_THRESHOLDS,
    TSHIRT_COSTS,
    EvalLevel,
    SeverityClass,
    TShirtSize,
)
from ai_kaizen.store.database import Store


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:48]


def _uid() -> str:
    return uuid.uuid4().hex[:8]


class InitiativeService:
    def __init__(self, store: Store):
        self.store = store

    def create(self, name: str, description: str = "", severity: str = "S2") -> dict:
        slug = _slug(name)
        initiative_id = f"{slug}-{_uid()}"
        self.store.create_initiative(id=initiative_id, name=name, description=description, severity_class=severity)
        self.store.set_config("current_initiative", initiative_id)
        return self.store.get_initiative(initiative_id)

    def select(self, initiative_id: str) -> dict:
        ini = self.store.get_initiative(initiative_id)
        if not ini:
            raise ValueError(f"Initiative '{initiative_id}' not found")
        self.store.set_config("current_initiative", initiative_id)
        return ini

    def current(self) -> Optional[dict]:
        iid = self.store.get_current_initiative_id()
        if not iid:
            return None
        return self.store.get_initiative(iid)

    def require_current(self) -> dict:
        ini = self.current()
        if not ini:
            raise ValueError("No initiative selected. Run 'ai-kaizen init' or 'ai-kaizen select' first.")
        return ini

    def list_all(self, status: Optional[str] = None) -> list[dict]:
        return self.store.list_initiatives(status)

    def update_status(self, initiative_id: str, status: str):
        self.store.update_initiative(initiative_id, status=status)

    def advance_phase(self, initiative_id: str, phase: str):
        self.store.update_initiative(initiative_id, current_phase=phase)

    def advance_loop(self, initiative_id: str, loop: str):
        self.store.update_initiative(initiative_id, current_loop=loop, current_phase="plan")


class OutcomeService:
    def __init__(self, store: Store):
        self.store = store

    def create(self, initiative_id: str, metric: str, baseline: str, target_range: str, **kwargs) -> dict:
        oid = f"outcome-{_uid()}"
        self.store.create_outcome(
            id=oid, initiative_id=initiative_id,
            metric=metric, baseline=baseline, target_range=target_range, **kwargs,
        )
        outcomes = self.store.list_outcomes(initiative_id)
        return [o for o in outcomes if o["id"] == oid][0]

    def list(self, initiative_id: str) -> list[dict]:
        return self.store.list_outcomes(initiative_id)


class EvalService:
    def __init__(self, store: Store):
        self.store = store

    def create_suite(self, initiative_id: str, level: str, description: str = "") -> dict:
        sid = f"eval-{level.lower().replace('.', '')}-{_uid()}"
        self.store.create_eval_suite(
            id=sid, initiative_id=initiative_id, level=level, description=description,
        )
        suites = self.store.list_eval_suites(initiative_id)
        return [s for s in suites if s["id"] == sid][0]

    def record_run(self, initiative_id: str, suite_id: str, level: str,
                   total: int, passed: int, notes: str = "", commit_ref: str = "") -> dict:
        rid = f"run-{_uid()}"
        failed = total - passed
        pass_rate = passed / total if total > 0 else 0.0
        self.store.record_eval_run(
            id=rid, suite_id=suite_id, initiative_id=initiative_id, level=level,
            total=total, passed=passed, failed=failed, pass_rate=pass_rate,
            notes=notes, commit_ref=commit_ref,
        )
        return self.store.latest_eval_run(initiative_id, level)

    def list_suites(self, initiative_id: str) -> list[dict]:
        return self.store.list_eval_suites(initiative_id)

    def list_runs(self, initiative_id: str, level: Optional[str] = None) -> list[dict]:
        return self.store.list_eval_runs(initiative_id, level)

    def check_thresholds(self, initiative_id: str, severity: str) -> list[dict]:
        """Check latest eval runs against severity-tiered thresholds."""
        sev = SeverityClass(severity)
        thresholds = EVAL_THRESHOLDS.get(sev, {})
        results = []
        for level, required in thresholds.items():
            run = self.store.latest_eval_run(initiative_id, level.value)
            actual = run["pass_rate"] if run else 0.0
            results.append({
                "level": level.value,
                "required": required,
                "actual": round(actual, 3),
                "passing": actual >= required,
                "has_data": run is not None,
            })
        return results


class PDCAService:
    def __init__(self, store: Store):
        self.store = store

    def log_entry(self, initiative_id: str, loop: str, phase: str, note: str) -> dict:
        eid = f"pdca-{_uid()}"
        self.store.create_pdca_entry(
            id=eid, initiative_id=initiative_id, loop=loop, phase=phase, note=note,
        )
        self.store.update_initiative(initiative_id, current_loop=loop, current_phase=phase)
        entries = self.store.list_pdca_entries(initiative_id, loop)
        return [e for e in entries if e["id"] == eid][0]

    def list_entries(self, initiative_id: str, loop: Optional[str] = None) -> list[dict]:
        return self.store.list_pdca_entries(initiative_id, loop)

    def check_gate(self, initiative_id: str) -> dict:
        """Check kill criteria and eval thresholds for gate decision."""
        ini = self.store.get_initiative(initiative_id)
        criteria = self.store.list_kill_criteria(initiative_id)
        triggered = [c for c in criteria if c["triggered"]]

        eval_svc = EvalService(self.store)
        eval_checks = eval_svc.check_thresholds(initiative_id, ini["severity_class"])
        failing_evals = [e for e in eval_checks if not e["passing"] and e["has_data"]]

        if triggered:
            result = "blocked"
            rationale = f"Kill criteria triggered: {', '.join(c['signal'] for c in triggered)}"
        elif failing_evals:
            result = "blocked"
            rationale = f"Eval thresholds not met: {', '.join(e['level'] for e in failing_evals)}"
        else:
            missing = [e for e in eval_checks if not e["has_data"]]
            if missing:
                result = "incomplete"
                rationale = f"Missing eval data for: {', '.join(e['level'] for e in missing)}"
            else:
                result = "passed"
                rationale = "All kill criteria clear; all eval thresholds met"

        return {
            "initiative_id": initiative_id,
            "loop": ini["current_loop"],
            "result": result,
            "rationale": rationale,
            "kill_criteria": criteria,
            "eval_checks": eval_checks,
        }


class PMOService:
    def __init__(self, store: Store):
        self.store = store

    def score_initiative(self, initiative_id: str, **scores) -> dict:
        # Map friendly names to store column names
        mapped = {
            "initiative_id": initiative_id,
            "business_value": scores.get("business_value"),
            "baseline_measurability": scores.get("measurability", scores.get("baseline_measurability")),
            "data_readiness": scores.get("data_readiness"),
            "change_readiness": scores.get("change_risk", scores.get("change_readiness")),
            "reversibility": scores.get("reversibility"),
            "compliance_burden": scores.get("compliance_risk", scores.get("compliance_burden")),
            "platform_reuse": scores.get("reuse_potential", scores.get("platform_reuse")),
            "notes": scores.get("notes", ""),
        }
        self.store.save_initiative_score(**mapped)
        return self.store.get_initiative_score(initiative_id)

    def ranked_backlog(self) -> list[dict]:
        return self.store.list_initiative_scores()

    def record_roi(self, initiative_id: str, confidence: str,
                   value_created: float, value_captured: float,
                   tco_to_date: float, notes: str = "") -> dict:
        rid = f"roi-{_uid()}"
        self.store.record_roi(
            id=rid, initiative_id=initiative_id, confidence=confidence,
            value_created=value_created, value_captured=value_captured,
            tco_to_date=tco_to_date, notes=notes,
        )
        return self.store.latest_roi(initiative_id)

    def portfolio_summary(self) -> dict:
        return self.store.portfolio_roi_summary()

    def estimate_effort(self, size: str) -> dict:
        ts = TShirtSize(size)
        costs = TSHIRT_COSTS[ts]
        return {
            "size": size,
            "discovery": costs["discovery"],
            "validation": costs["validation"],
            "year1_tco": costs["year1_tco"],
        }

    def capacity_check(self, max_wip: int = 5) -> dict:
        active = self.store.list_initiatives("active")
        by_loop = {"discovery": [], "validation": [], "scaling": []}
        for ini in active:
            loop = ini.get("current_loop", "discovery")
            if loop in by_loop:
                by_loop[loop].append(ini["name"])
        return {
            "active_count": len(active),
            "wip_limit": max_wip,
            "within_limit": len(active) <= max_wip,
            "by_loop": by_loop,
        }


class DataReadinessService:
    def __init__(self, store: Store):
        self.store = store

    def assess(self, initiative_id: str, scores: dict, notes: str = "") -> dict:
        self.store.save_data_readiness(initiative_id=initiative_id, notes=notes, **scores)
        return self.get(initiative_id)

    def get(self, initiative_id: str) -> Optional[dict]:
        dr = self.store.get_data_readiness(initiative_id)
        if not dr:
            return None
        total = dr["existence"] + dr["accessibility"] + dr["quality"] + \
                dr["latency"] + dr["history"] + dr["coverage"]
        dr["total_score"] = total
        if total >= 15:
            dr["recommendation"] = "Proceed to outcome definition"
        elif total >= 10:
            dr["recommendation"] = "Proceed with scoped outcomes; parallel-track data remediation"
        elif total >= 5:
            dr["recommendation"] = "Data remediation project first; defer AI agent development"
        else:
            dr["recommendation"] = "Fundamental infrastructure investment required"
        return dr
