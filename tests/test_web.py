"""Tests for the web routes."""

import json
import pytest


class TestDashboard:
    def test_dashboard_empty(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"AI-Kaizen" in resp.data
        assert b"Portfolio Dashboard" in resp.data

    def test_dashboard_with_initiative(self, seeded_client):
        client, _ = seeded_client
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Test Initiative" in resp.data


class TestInitiativeList:
    def test_list_empty(self, client):
        resp = client.get("/initiatives")
        assert resp.status_code == 200
        assert b"No initiatives yet" in resp.data

    def test_create_initiative(self, client):
        resp = client.post("/initiatives", data={
            "name": "New Project",
            "severity": "S1",
            "description": "A test project",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Created initiative" in resp.data
        assert b"New Project" in resp.data

    def test_create_initiative_missing_name(self, client):
        resp = client.post("/initiatives", data={
            "name": "",
            "severity": "S2",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Name is required" in resp.data

    def test_create_initiative_invalid_severity(self, client):
        resp = client.post("/initiatives", data={
            "name": "Bad Severity",
            "severity": "S9",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Severity must be" in resp.data


class TestInitiativeDetail:
    def test_detail_page(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.get(f"/initiatives/{ini_id}")
        assert resp.status_code == 200
        assert b"Test Initiative" in resp.data
        assert b"Gate Check" in resp.data

    def test_detail_not_found(self, client):
        resp = client.get("/initiatives/does-not-exist")
        assert resp.status_code == 404


class TestOutcomes:
    def test_add_outcome(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/outcome", data={
            "metric": "MTBF",
            "baseline": "72h",
            "target": "96h",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Outcome added" in resp.data

    def test_add_outcome_missing_fields(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/outcome", data={
            "metric": "",
            "baseline": "",
            "target": "",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"is required" in resp.data

    def test_add_outcome_bad_initiative(self, client):
        resp = client.post("/initiatives/bad-id/outcome", data={
            "metric": "Test", "baseline": "1", "target": "2",
        })
        assert resp.status_code == 404


class TestEvals:
    def test_scaffold_eval(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/eval/scaffold", data={
            "level": "L0",
            "description": "Safety tests",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Eval suite created" in resp.data

    def test_scaffold_invalid_level(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/eval/scaffold", data={
            "level": "L99",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Level must be" in resp.data

    def test_record_eval_run(self, seeded_client):
        client, ini_id = seeded_client
        # First create a suite
        client.post(f"/initiatives/{ini_id}/eval/scaffold", data={
            "level": "L0", "description": "",
        })
        # Then record a run
        resp = client.post(f"/initiatives/{ini_id}/eval/record", data={
            "level": "L0", "total": "50", "passed": "48", "notes": "Good run",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Eval recorded" in resp.data

    def test_record_eval_passed_exceeds_total(self, seeded_client):
        client, ini_id = seeded_client
        client.post(f"/initiatives/{ini_id}/eval/scaffold", data={"level": "L0"})
        resp = client.post(f"/initiatives/{ini_id}/eval/record", data={
            "level": "L0", "total": "10", "passed": "15",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"cannot exceed" in resp.data.lower()

    def test_record_eval_no_suite(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/eval/record", data={
            "level": "L0", "total": "10", "passed": "10",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"No eval suite" in resp.data


class TestPDCA:
    def test_log_entry(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/pdca", data={
            "phase": "plan",
            "note": "Identified root cause",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Logged plan" in resp.data

    def test_log_invalid_phase(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/pdca", data={
            "phase": "invalid",
            "note": "Something",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Phase must be" in resp.data

    def test_log_empty_note(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/pdca", data={
            "phase": "plan",
            "note": "",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"is required" in resp.data


class TestPMOScore:
    def test_score_initiative(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/pmo/score", data={
            "business_value": "4",
            "measurability": "3",
            "data_readiness": "3",
            "change_risk": "2",
            "reversibility": "3",
            "compliance_risk": "1",
            "reuse_potential": "3",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"PMO score saved" in resp.data

    def test_score_out_of_range(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/pmo/score", data={
            "business_value": "7",
            "measurability": "3",
            "data_readiness": "3",
            "change_risk": "2",
            "reversibility": "3",
            "compliance_risk": "1",
            "reuse_potential": "3",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"between 1 and 5" in resp.data


class TestDataReadiness:
    def test_assess(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/assess", data={
            "existence": "2", "accessibility": "2", "quality": "1",
            "latency": "2", "history": "3", "coverage": "2",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Data readiness assessment saved" in resp.data

    def test_assess_out_of_range(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/assess", data={
            "existence": "5", "accessibility": "2", "quality": "1",
            "latency": "2", "history": "3", "coverage": "2",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"between 0 and 3" in resp.data


class TestROI:
    def test_track_roi(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/roi", data={
            "value_created": "25000",
            "value_captured": "8000",
            "tco": "15000",
            "confidence": "projected",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"ROI recorded" in resp.data

    def test_track_roi_invalid_confidence(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/roi", data={
            "value_created": "25000",
            "value_captured": "8000",
            "tco": "15000",
            "confidence": "guessed",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Confidence must be" in resp.data


class TestPortfolioROI:
    def test_portfolio_empty(self, client):
        resp = client.get("/portfolio/roi")
        assert resp.status_code == 200
        assert b"Portfolio ROI" in resp.data

    def test_portfolio_with_data(self, seeded_client):
        client, ini_id = seeded_client
        client.post(f"/initiatives/{ini_id}/roi", data={
            "value_created": "25000",
            "value_captured": "8000",
            "tco": "15000",
            "confidence": "projected",
        })
        resp = client.get("/portfolio/roi")
        assert resp.status_code == 200
        assert b"25,000" in resp.data


class TestExport:
    def test_export_json(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.get(f"/initiatives/{ini_id}/export?format=json")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["initiative"]["name"] == "Test Initiative"

    def test_export_html(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.get(f"/initiatives/{ini_id}/export?format=html")
        assert resp.status_code == 200
        assert b"Export" in resp.data

    def test_export_not_found(self, client):
        resp = client.get("/initiatives/bad-id/export?format=json")
        assert resp.status_code == 404


class TestExecutiveDashboard:
    def test_exec_dashboard_empty(self, client):
        resp = client.get("/executive")
        assert resp.status_code == 200
        assert b"Executive AI Transformation Dashboard" in resp.data
        assert b"ROI" in resp.data
        assert b"Pilot-to-Scale" in resp.data
        assert b"Workforce" in resp.data

    def test_exec_dashboard_with_data(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.get("/executive")
        assert resp.status_code == 200
        assert b"Transformation Depth" in resp.data
        assert b"Governance" in resp.data

    def test_workforce_assessment(self, client):
        resp = client.post("/executive/workforce", data={
            "total_headcount": "500",
            "ai_trained_count": "125",
            "ai_fluency_score": "2.8",
            "roles_redesigned": "15",
            "roles_total": "80",
            "upskilling_completion_pct": "45.0",
            "notes": "Q1 assessment",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Workforce assessment saved" in resp.data
        # Values should show on dashboard
        assert b"2.8" in resp.data
        assert b"Q1 assessment" in resp.data or b"45" in resp.data

    def test_workforce_validation(self, client):
        resp = client.post("/executive/workforce", data={
            "total_headcount": "not_a_number",
            "ai_trained_count": "10",
            "ai_fluency_score": "3",
            "roles_redesigned": "5",
            "roles_total": "50",
            "upskilling_completion_pct": "20",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"must be a whole number" in resp.data

    def test_governance_review(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/governance", data={
            "review_type": "ethics",
            "status": "completed",
            "reviewer": "Jane Smith",
            "findings": "No issues found",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Governance review recorded" in resp.data

    def test_governance_invalid_type(self, seeded_client):
        client, ini_id = seeded_client
        resp = client.post(f"/initiatives/{ini_id}/governance", data={
            "review_type": "invalid",
            "status": "pending",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Review type must be" in resp.data

    def test_governance_bad_initiative(self, client):
        resp = client.post("/initiatives/bad-id/governance", data={
            "review_type": "ethics",
            "status": "pending",
        })
        assert resp.status_code == 404

    def test_transformation_type_on_create(self, client):
        resp = client.post("/initiatives", data={
            "name": "Reinvention Project",
            "severity": "S1",
            "transformation_type": "reinvent",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Created initiative" in resp.data


class TestCxOService:
    def test_full_snapshot(self, tmp_db):
        from ai_kaizen.services.core import CxODashboardService, InitiativeService
        ini_svc = InitiativeService(tmp_db)
        ini = ini_svc.create(name="Test", severity="S2")
        cxo = CxODashboardService(tmp_db)
        snap = cxo.full_snapshot()
        assert "roi" in snap
        assert "pilot_to_scale" in snap
        assert "workforce" in snap
        assert "governance" in snap
        assert "readiness_gap" in snap
        assert "transformation_depth" in snap
        assert "cost_transparency" in snap
        assert "eval_coverage" in snap
        assert snap["pilot_to_scale"]["total"] == 1

    def test_record_workforce(self, tmp_db):
        from ai_kaizen.services.core import CxODashboardService
        cxo = CxODashboardService(tmp_db)
        result = cxo.record_workforce(
            total_headcount=200, ai_trained_count=80,
            ai_fluency_score=3.5, roles_redesigned=10,
            roles_total=50, upskilling_completion_pct=60,
        )
        assert result["total_headcount"] == 200
        assert result["ai_fluency_score"] == 3.5
