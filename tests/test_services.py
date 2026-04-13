"""Tests for the service layer."""

import pytest
from ai_kaizen.services.core import (
    InitiativeService,
    OutcomeService,
    EvalService,
    PDCAService,
    PMOService,
    DataReadinessService,
)


class TestInitiativeService:
    def test_create(self, tmp_db):
        svc = InitiativeService(tmp_db)
        ini = svc.create("Test Initiative", severity="S1")
        assert ini["name"] == "Test Initiative"
        assert ini["severity_class"] == "S1"
        assert ini["current_loop"] == "discovery"
        assert ini["current_phase"] == "plan"
        assert ini["status"] == "active"

    def test_create_auto_selects(self, tmp_db):
        svc = InitiativeService(tmp_db)
        ini = svc.create("Auto Select Test")
        current = svc.current()
        assert current["id"] == ini["id"]

    def test_select_nonexistent(self, tmp_db):
        svc = InitiativeService(tmp_db)
        with pytest.raises(ValueError, match="not found"):
            svc.select("does-not-exist")

    def test_list_all(self, tmp_db):
        svc = InitiativeService(tmp_db)
        svc.create("One")
        svc.create("Two")
        assert len(svc.list_all()) == 2

    def test_list_by_status(self, tmp_db):
        svc = InitiativeService(tmp_db)
        ini = svc.create("Active One")
        svc.update_status(ini["id"], "paused")
        assert len(svc.list_all("active")) == 0
        assert len(svc.list_all("paused")) == 1

    def test_require_current_when_none(self, tmp_db):
        svc = InitiativeService(tmp_db)
        with pytest.raises(ValueError, match="No initiative selected"):
            svc.require_current()

    def test_advance_phase(self, tmp_db):
        svc = InitiativeService(tmp_db)
        ini = svc.create("Phase Test")
        svc.advance_phase(ini["id"], "do")
        updated = tmp_db.get_initiative(ini["id"])
        assert updated["current_phase"] == "do"

    def test_advance_loop(self, tmp_db):
        svc = InitiativeService(tmp_db)
        ini = svc.create("Loop Test")
        svc.advance_loop(ini["id"], "validation")
        updated = tmp_db.get_initiative(ini["id"])
        assert updated["current_loop"] == "validation"
        assert updated["current_phase"] == "plan"


class TestOutcomeService:
    def test_create_and_list(self, tmp_db):
        ini_svc = InitiativeService(tmp_db)
        ini = ini_svc.create("Outcome Test")
        svc = OutcomeService(tmp_db)
        outcome = svc.create(ini["id"], metric="MTBF", baseline="72h", target_range="96-120h")
        assert outcome["metric"] == "MTBF"
        assert len(svc.list(ini["id"])) == 1

    def test_create_with_scope(self, tmp_db):
        ini = InitiativeService(tmp_db).create("Scoped")
        svc = OutcomeService(tmp_db)
        outcome = svc.create(ini["id"], metric="Latency", baseline="200ms",
                             target_range="<100ms", scope="API v2", timeframe="3 months")
        assert outcome["scope"] == "API v2"


class TestEvalService:
    def test_create_suite(self, tmp_db):
        ini = InitiativeService(tmp_db).create("Eval Test")
        svc = EvalService(tmp_db)
        suite = svc.create_suite(ini["id"], level="L0", description="Safety tests")
        assert suite["level"] == "L0"

    def test_record_run(self, tmp_db):
        ini = InitiativeService(tmp_db).create("Eval Run Test")
        svc = EvalService(tmp_db)
        suite = svc.create_suite(ini["id"], level="L0")
        run = svc.record_run(ini["id"], suite["id"], level="L0", total=50, passed=50)
        assert run["pass_rate"] == 1.0
        assert run["total"] == 50

    def test_check_thresholds_s1(self, tmp_db):
        ini = InitiativeService(tmp_db).create("Threshold Test", severity="S1")
        svc = EvalService(tmp_db)
        suite = svc.create_suite(ini["id"], level="L0")
        svc.record_run(ini["id"], suite["id"], level="L0", total=100, passed=100)
        results = svc.check_thresholds(ini["id"], "S1")
        l0 = next(r for r in results if r["level"] == "L0")
        assert l0["passing"] is True
        assert l0["actual"] == 1.0

    def test_check_thresholds_failing(self, tmp_db):
        ini = InitiativeService(tmp_db).create("Fail Test", severity="S1")
        svc = EvalService(tmp_db)
        suite = svc.create_suite(ini["id"], level="L0")
        svc.record_run(ini["id"], suite["id"], level="L0", total=100, passed=95)
        results = svc.check_thresholds(ini["id"], "S1")
        l0 = next(r for r in results if r["level"] == "L0")
        assert l0["passing"] is False


class TestPDCAService:
    def test_log_entry(self, tmp_db):
        ini = InitiativeService(tmp_db).create("PDCA Test")
        svc = PDCAService(tmp_db)
        entry = svc.log_entry(ini["id"], loop="discovery", phase="plan", note="Test entry")
        assert entry["phase"] == "plan"
        assert entry["note"] == "Test entry"

    def test_log_advances_phase(self, tmp_db):
        ini = InitiativeService(tmp_db).create("Phase Advance")
        svc = PDCAService(tmp_db)
        svc.log_entry(ini["id"], loop="discovery", phase="do", note="Started work")
        updated = tmp_db.get_initiative(ini["id"])
        assert updated["current_phase"] == "do"

    def test_check_gate_incomplete(self, tmp_db):
        ini = InitiativeService(tmp_db).create("Gate Test", severity="S2")
        svc = PDCAService(tmp_db)
        gate = svc.check_gate(ini["id"])
        assert gate["result"] == "incomplete"

    def test_check_gate_passed(self, tmp_db):
        ini = InitiativeService(tmp_db).create("Gate Pass", severity="S3")
        eval_svc = EvalService(tmp_db)
        for level in ["L0", "L1", "L2"]:
            suite = eval_svc.create_suite(ini["id"], level=level)
            eval_svc.record_run(ini["id"], suite["id"], level=level, total=100, passed=100)
        gate = PDCAService(tmp_db).check_gate(ini["id"])
        assert gate["result"] == "passed"


class TestPMOService:
    def test_score_initiative(self, tmp_db):
        ini = InitiativeService(tmp_db).create("PMO Test")
        svc = PMOService(tmp_db)
        score = svc.score_initiative(
            ini["id"], business_value=4, measurability=3,
            data_readiness=3, change_risk=2, reversibility=3,
            compliance_risk=1, reuse_potential=3,
        )
        # V=4×2=8, B=3, D=3, C=2, R=3, inv(X)=6-1=5, P=3 = 27
        assert score["total"] == 27

    def test_record_roi(self, tmp_db):
        ini = InitiativeService(tmp_db).create("ROI Test")
        svc = PMOService(tmp_db)
        roi = svc.record_roi(
            ini["id"], confidence="projected",
            value_created=25000, value_captured=8000, tco_to_date=15000,
        )
        assert roi["value_created"] == 25000
        assert roi["confidence"] == "projected"

    def test_portfolio_summary_empty(self, tmp_db):
        svc = PMOService(tmp_db)
        summary = svc.portfolio_summary()
        assert summary["initiative_count"] == 0

    def test_capacity_check(self, tmp_db):
        svc = PMOService(tmp_db)
        InitiativeService(tmp_db).create("One")
        InitiativeService(tmp_db).create("Two")
        capacity = svc.capacity_check(max_wip=5)
        assert capacity["active_count"] == 2
        assert capacity["within_limit"] is True

    def test_capacity_over_wip(self, tmp_db):
        svc = PMOService(tmp_db)
        for i in range(6):
            InitiativeService(tmp_db).create(f"Init {i}")
        capacity = svc.capacity_check(max_wip=5)
        assert capacity["within_limit"] is False


class TestDataReadinessService:
    def test_assess(self, tmp_db):
        ini = InitiativeService(tmp_db).create("DR Test")
        svc = DataReadinessService(tmp_db)
        dr = svc.assess(ini["id"], scores={
            "existence": 2, "accessibility": 2, "quality": 1,
            "latency": 2, "history": 3, "coverage": 2,
        })
        assert dr["total_score"] == 12
        assert "scoped outcomes" in dr["recommendation"].lower()

    def test_assess_low_score(self, tmp_db):
        ini = InitiativeService(tmp_db).create("Low DR")
        svc = DataReadinessService(tmp_db)
        dr = svc.assess(ini["id"], scores={
            "existence": 0, "accessibility": 1, "quality": 0,
            "latency": 1, "history": 0, "coverage": 1,
        })
        assert dr["total_score"] == 3
        assert "infrastructure" in dr["recommendation"].lower()

    def test_get_nonexistent(self, tmp_db):
        svc = DataReadinessService(tmp_db)
        assert svc.get("nonexistent") is None
