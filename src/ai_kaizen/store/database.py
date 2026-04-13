"""SQLite persistence layer for AI-Kaizen toolkit."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


def _default_db_path() -> Path:
    return Path.home() / ".ai-kaizen" / "kaizen.db"


def get_db_path() -> Path:
    env = os.environ.get("AI_KAIZEN_DB")
    if env:
        return Path(env)
    return _default_db_path()


class Store:
    def __init__(self, db_path: Optional[Path] = None, run_migrations: bool = True):
        self.db_path = db_path or get_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), timeout=10)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA busy_timeout=5000")
        if run_migrations:
            self._migrate()

    def _migrate(self):
        self.conn.executescript(SCHEMA)
        # V2: add transformation_type to initiatives if not present
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(initiatives)").fetchall()]
        if "transformation_type" not in cols:
            self.conn.execute(
                "ALTER TABLE initiatives ADD COLUMN transformation_type TEXT DEFAULT 'optimize'"
            )
        self.conn.commit()

    def close(self):
        self.conn.close()

    # --- Config (current initiative selection) ---

    def set_config(self, key: str, value: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    def get_config(self, key: str) -> Optional[str]:
        row = self.conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def get_current_initiative_id(self) -> Optional[str]:
        return self.get_config("current_initiative")

    # --- Initiatives ---

    def create_initiative(self, **kwargs) -> str:
        now = datetime.utcnow().isoformat()
        kwargs.setdefault("created_at", now)
        kwargs.setdefault("updated_at", now)
        kwargs.setdefault("status", "active")
        kwargs.setdefault("severity_class", "S2")
        kwargs.setdefault("autonomy_level", "L0")
        kwargs.setdefault("current_loop", "discovery")
        kwargs.setdefault("current_phase", "plan")
        kwargs.setdefault("description", "")
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self.conn.execute(
            f"INSERT INTO initiatives ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
        self.conn.commit()
        return kwargs["id"]

    def get_initiative(self, initiative_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM initiatives WHERE id = ?", (initiative_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_initiatives(self, status: Optional[str] = None) -> list[dict]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM initiatives WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM initiatives ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def update_initiative(self, initiative_id: str, **kwargs):
        kwargs["updated_at"] = datetime.utcnow().isoformat()
        sets = ", ".join(f"{k} = ?" for k in kwargs.keys())
        self.conn.execute(
            f"UPDATE initiatives SET {sets} WHERE id = ?",
            [*kwargs.values(), initiative_id],
        )
        self.conn.commit()

    # --- Outcomes ---

    def create_outcome(self, **kwargs) -> str:
        now = datetime.utcnow().isoformat()
        kwargs.setdefault("created_at", now)
        kwargs.setdefault("updated_at", now)
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self.conn.execute(
            f"INSERT INTO outcomes ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
        self.conn.commit()
        return kwargs["id"]

    def list_outcomes(self, initiative_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM outcomes WHERE initiative_id = ? ORDER BY created_at",
            (initiative_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Eval Suites & Runs ---

    def create_eval_suite(self, **kwargs) -> str:
        kwargs.setdefault("created_at", datetime.utcnow().isoformat())
        kwargs.setdefault("assertion_count", 0)
        kwargs.setdefault("description", "")
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self.conn.execute(
            f"INSERT INTO eval_suites ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
        self.conn.commit()
        return kwargs["id"]

    def list_eval_suites(self, initiative_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM eval_suites WHERE initiative_id = ? ORDER BY level",
            (initiative_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def record_eval_run(self, **kwargs) -> str:
        kwargs.setdefault("run_at", datetime.utcnow().isoformat())
        kwargs.setdefault("notes", "")
        kwargs.setdefault("commit_ref", "")
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self.conn.execute(
            f"INSERT INTO eval_runs ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
        self.conn.commit()
        return kwargs["id"]

    def list_eval_runs(self, initiative_id: str, level: Optional[str] = None) -> list[dict]:
        if level:
            rows = self.conn.execute(
                "SELECT * FROM eval_runs WHERE initiative_id = ? AND level = ? ORDER BY run_at DESC",
                (initiative_id, level),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM eval_runs WHERE initiative_id = ? ORDER BY run_at DESC",
                (initiative_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def latest_eval_run(self, initiative_id: str, level: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM eval_runs WHERE initiative_id = ? AND level = ? ORDER BY run_at DESC LIMIT 1",
            (initiative_id, level),
        ).fetchone()
        return dict(row) if row else None

    # --- PDCA Entries ---

    def create_pdca_entry(self, **kwargs) -> str:
        kwargs.setdefault("created_at", datetime.utcnow().isoformat())
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self.conn.execute(
            f"INSERT INTO pdca_entries ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
        self.conn.commit()
        return kwargs["id"]

    def list_pdca_entries(self, initiative_id: str, loop: Optional[str] = None) -> list[dict]:
        if loop:
            rows = self.conn.execute(
                "SELECT * FROM pdca_entries WHERE initiative_id = ? AND loop = ? ORDER BY created_at",
                (initiative_id, loop),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM pdca_entries WHERE initiative_id = ? ORDER BY created_at",
                (initiative_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # --- Gate Decisions ---

    def record_gate_decision(self, **kwargs) -> str:
        kwargs.setdefault("decided_at", datetime.utcnow().isoformat())
        kwargs.setdefault("rationale", "")
        kwargs.setdefault("criteria_snapshot", "")
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self.conn.execute(
            f"INSERT INTO gate_decisions ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
        self.conn.commit()
        return kwargs["id"]

    # --- Kill Criteria ---

    def create_kill_criterion(self, **kwargs) -> str:
        kwargs.setdefault("updated_at", datetime.utcnow().isoformat())
        kwargs.setdefault("triggered", 0)
        kwargs.setdefault("current_value", "")
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self.conn.execute(
            f"INSERT INTO kill_criteria ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
        self.conn.commit()
        return kwargs["id"]

    def list_kill_criteria(self, initiative_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM kill_criteria WHERE initiative_id = ? ORDER BY signal",
            (initiative_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def update_kill_criterion(self, criterion_id: str, **kwargs):
        kwargs["updated_at"] = datetime.utcnow().isoformat()
        sets = ", ".join(f"{k} = ?" for k in kwargs.keys())
        self.conn.execute(
            f"UPDATE kill_criteria SET {sets} WHERE id = ?",
            [*kwargs.values(), criterion_id],
        )
        self.conn.commit()

    # --- Data Readiness ---

    def save_data_readiness(self, **kwargs):
        kwargs.setdefault("assessed_at", datetime.utcnow().isoformat())
        kwargs.setdefault("notes", "")
        self.conn.execute(
            "INSERT OR REPLACE INTO data_readiness "
            "(initiative_id, existence, accessibility, quality, latency, history, coverage, notes, assessed_at) "
            "VALUES (:initiative_id, :existence, :accessibility, :quality, :latency, :history, :coverage, :notes, :assessed_at)",
            kwargs,
        )
        self.conn.commit()

    def get_data_readiness(self, initiative_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM data_readiness WHERE initiative_id = ?", (initiative_id,)
        ).fetchone()
        return dict(row) if row else None

    # --- Stakeholders ---

    def create_stakeholder(self, **kwargs) -> str:
        kwargs.setdefault("created_at", datetime.utcnow().isoformat())
        kwargs.setdefault("concern", "")
        kwargs.setdefault("engagement_status", "not_engaged")
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self.conn.execute(
            f"INSERT INTO stakeholders ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
        self.conn.commit()
        return kwargs["id"]

    def list_stakeholders(self, initiative_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM stakeholders WHERE initiative_id = ? ORDER BY role",
            (initiative_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- PMO: Initiative Scores ---

    def save_initiative_score(self, **kwargs):
        kwargs.setdefault("scored_at", datetime.utcnow().isoformat())
        kwargs.setdefault("notes", "")
        self.conn.execute(
            "INSERT OR REPLACE INTO initiative_scores "
            "(initiative_id, business_value, baseline_measurability, data_readiness, "
            "change_readiness, reversibility, compliance_burden, platform_reuse, notes, scored_at) "
            "VALUES (:initiative_id, :business_value, :baseline_measurability, :data_readiness, "
            ":change_readiness, :reversibility, :compliance_burden, :platform_reuse, :notes, :scored_at)",
            kwargs,
        )
        self.conn.commit()

    def get_initiative_score(self, initiative_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM initiative_scores WHERE initiative_id = ?", (initiative_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["total"] = (d["business_value"] * 2) + d["baseline_measurability"] + \
                     d["data_readiness"] + d["change_readiness"] + d["reversibility"] + \
                     (6 - d["compliance_burden"]) + d["platform_reuse"]
        return d

    def list_initiative_scores(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT s.*, i.name, i.status, i.current_loop, i.current_phase "
            "FROM initiative_scores s JOIN initiatives i ON s.initiative_id = i.id "
            "ORDER BY (s.business_value * 2 + s.baseline_measurability + s.data_readiness + "
            "s.change_readiness + s.reversibility + (6 - s.compliance_burden) + s.platform_reuse) DESC"
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["total"] = (d["business_value"] * 2) + d["baseline_measurability"] + \
                         d["data_readiness"] + d["change_readiness"] + d["reversibility"] + \
                         (6 - d["compliance_burden"]) + d["platform_reuse"]
            results.append(d)
        return results

    # --- PMO: ROI Entries ---

    def record_roi(self, **kwargs) -> str:
        kwargs.setdefault("recorded_at", datetime.utcnow().isoformat())
        kwargs.setdefault("notes", "")
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self.conn.execute(
            f"INSERT INTO roi_entries ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
        self.conn.commit()
        return kwargs["id"]

    def latest_roi(self, initiative_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM roi_entries WHERE initiative_id = ? ORDER BY recorded_at DESC LIMIT 1",
            (initiative_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_roi_entries(self, initiative_id: Optional[str] = None) -> list[dict]:
        if initiative_id:
            rows = self.conn.execute(
                "SELECT * FROM roi_entries WHERE initiative_id = ? ORDER BY recorded_at DESC",
                (initiative_id,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT r.*, i.name FROM roi_entries r JOIN initiatives i ON r.initiative_id = i.id "
                "ORDER BY r.recorded_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def portfolio_roi_summary(self) -> dict:
        row = self.conn.execute("""
            SELECT
                COUNT(DISTINCT initiative_id) as initiative_count,
                SUM(value_created) as total_value_created,
                SUM(value_captured) as total_value_captured,
                SUM(tco_to_date) as total_tco
            FROM (
                SELECT initiative_id, value_created, value_captured, tco_to_date,
                    ROW_NUMBER() OVER (PARTITION BY initiative_id ORDER BY recorded_at DESC) as rn
                FROM roi_entries
            ) WHERE rn = 1
        """).fetchone()
        d = dict(row)
        d["total_net_value"] = (d["total_value_captured"] or 0) - (d["total_tco"] or 0)
        d["capture_rate"] = (
            (d["total_value_captured"] or 0) / d["total_value_created"]
            if d["total_value_created"]
            else 0
        )
        d["portfolio_roi"] = (
            d["total_net_value"] / d["total_tco"]
            if d["total_tco"]
            else 0
        )
        return d

    # --- Workforce Assessments (CxO Dashboard) ---

    def save_workforce_assessment(self, **kwargs) -> str:
        kwargs.setdefault("assessment_date", datetime.utcnow().isoformat())
        kwargs.setdefault("notes", "")
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self.conn.execute(
            f"INSERT INTO workforce_assessments ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
        self.conn.commit()
        return kwargs["id"]

    def latest_workforce_assessment(self) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM workforce_assessments ORDER BY assessment_date DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    def list_workforce_assessments(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM workforce_assessments ORDER BY assessment_date DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Governance Reviews (CxO Dashboard) ---

    def save_governance_review(self, **kwargs) -> str:
        kwargs.setdefault("reviewed_at", datetime.utcnow().isoformat())
        kwargs.setdefault("findings", "")
        kwargs.setdefault("reviewer", "")
        kwargs.setdefault("status", "pending")
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self.conn.execute(
            f"INSERT INTO governance_reviews ({cols}) VALUES ({placeholders})",
            list(kwargs.values()),
        )
        self.conn.commit()
        return kwargs["id"]

    def list_governance_reviews(self, initiative_id: Optional[str] = None) -> list[dict]:
        if initiative_id:
            rows = self.conn.execute(
                "SELECT * FROM governance_reviews WHERE initiative_id = ? ORDER BY reviewed_at DESC",
                (initiative_id,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT g.*, i.name as initiative_name FROM governance_reviews g "
                "JOIN initiatives i ON g.initiative_id = i.id ORDER BY g.reviewed_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def governance_summary(self) -> dict:
        """Compute governance coverage stats across portfolio."""
        total = self.conn.execute("SELECT COUNT(*) as cnt FROM initiatives WHERE status = 'active'").fetchone()["cnt"]
        with_reviews = self.conn.execute(
            "SELECT COUNT(DISTINCT g.initiative_id) as cnt FROM governance_reviews g "
            "JOIN initiatives i ON g.initiative_id = i.id WHERE i.status = 'active'"
        ).fetchone()["cnt"]
        completed = self.conn.execute(
            "SELECT COUNT(DISTINCT g.initiative_id) as cnt FROM governance_reviews g "
            "JOIN initiatives i ON g.initiative_id = i.id "
            "WHERE i.status = 'active' AND g.status = 'completed'"
        ).fetchone()["cnt"]
        return {
            "total_active": total,
            "with_reviews": with_reviews,
            "completed_reviews": completed,
            "coverage_pct": (with_reviews / total * 100) if total else 0,
            "completion_pct": (completed / total * 100) if total else 0,
        }

    # --- CxO Aggregate Queries ---

    def transformation_depth_summary(self) -> dict:
        """Count initiatives by transformation_type."""
        rows = self.conn.execute(
            "SELECT COALESCE(transformation_type, 'optimize') as ttype, COUNT(*) as cnt "
            "FROM initiatives WHERE status = 'active' "
            "GROUP BY ttype ORDER BY cnt DESC"
        ).fetchall()
        result = {"optimize": 0, "redesign": 0, "reinvent": 0}
        for row in rows:
            result[row["ttype"]] = row["cnt"]
        total = sum(result.values())
        result["total"] = total
        result["reinvent_pct"] = (result["reinvent"] / total * 100) if total else 0
        result["redesign_pct"] = (result["redesign"] / total * 100) if total else 0
        result["optimize_pct"] = (result["optimize"] / total * 100) if total else 0
        return result

    def pilot_to_scale_summary(self) -> dict:
        """Compute pilot-to-scale pipeline metrics."""
        rows = self.conn.execute(
            "SELECT current_loop, COUNT(*) as cnt, "
            "GROUP_CONCAT(name, ', ') as names "
            "FROM initiatives WHERE status = 'active' "
            "GROUP BY current_loop"
        ).fetchall()
        by_loop = {"discovery": 0, "validation": 0, "scaling": 0}
        names_by_loop = {"discovery": [], "validation": [], "scaling": []}
        for row in rows:
            by_loop[row["current_loop"]] = row["cnt"]
            names_by_loop[row["current_loop"]] = row["names"].split(", ") if row["names"] else []
        total = sum(by_loop.values())
        return {
            "by_loop": by_loop,
            "names_by_loop": names_by_loop,
            "total": total,
            "discovery_pct": (by_loop["discovery"] / total * 100) if total else 0,
            "validation_pct": (by_loop["validation"] / total * 100) if total else 0,
            "scaling_pct": (by_loop["scaling"] / total * 100) if total else 0,
            "stuck_in_pilot": by_loop["discovery"] + by_loop["validation"],
            "at_scale": by_loop["scaling"],
        }

    def data_readiness_portfolio(self) -> dict:
        """Aggregate data readiness across all active initiatives."""
        rows = self.conn.execute(
            "SELECT d.*, i.name FROM data_readiness d "
            "JOIN initiatives i ON d.initiative_id = i.id "
            "WHERE i.status = 'active'"
        ).fetchall()
        if not rows:
            total_active = self.conn.execute(
                "SELECT COUNT(*) as cnt FROM initiatives WHERE status = 'active'"
            ).fetchone()["cnt"]
            return {"assessed_count": 0, "total_active": total_active, "avg_score": 0, "coverage_pct": 0, "items": []}
        total_active = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM initiatives WHERE status = 'active'"
        ).fetchone()["cnt"]
        items = []
        total_score = 0
        for row in rows:
            d = dict(row)
            score = d["existence"] + d["accessibility"] + d["quality"] + \
                    d["latency"] + d["history"] + d["coverage"]
            d["total_score"] = score
            total_score += score
            items.append(d)
        return {
            "assessed_count": len(items),
            "total_active": total_active,
            "coverage_pct": (len(items) / total_active * 100) if total_active else 0,
            "avg_score": total_score / len(items) if items else 0,
            "items": sorted(items, key=lambda x: x["total_score"]),
        }

    def eval_coverage_summary(self) -> dict:
        """Check how many active initiatives have eval suites and passing runs."""
        total = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM initiatives WHERE status = 'active'"
        ).fetchone()["cnt"]
        with_suites = self.conn.execute(
            "SELECT COUNT(DISTINCT es.initiative_id) as cnt FROM eval_suites es "
            "JOIN initiatives i ON es.initiative_id = i.id WHERE i.status = 'active'"
        ).fetchone()["cnt"]
        with_runs = self.conn.execute(
            "SELECT COUNT(DISTINCT er.initiative_id) as cnt FROM eval_runs er "
            "JOIN initiatives i ON er.initiative_id = i.id WHERE i.status = 'active'"
        ).fetchone()["cnt"]
        return {
            "total_active": total,
            "with_suites": with_suites,
            "with_runs": with_runs,
            "suite_coverage_pct": (with_suites / total * 100) if total else 0,
            "run_coverage_pct": (with_runs / total * 100) if total else 0,
        }

    def tco_breakdown(self) -> dict:
        """TCO breakdown across portfolio by confidence level."""
        rows = self.conn.execute("""
            SELECT confidence, COUNT(*) as cnt,
                   SUM(tco_to_date) as total_tco,
                   SUM(value_captured) as total_captured
            FROM (
                SELECT initiative_id, confidence, tco_to_date, value_captured,
                    ROW_NUMBER() OVER (PARTITION BY initiative_id ORDER BY recorded_at DESC) as rn
                FROM roi_entries
            ) WHERE rn = 1
            GROUP BY confidence
        """).fetchall()
        result = {}
        for row in rows:
            result[row["confidence"]] = {
                "count": row["cnt"],
                "tco": row["total_tco"] or 0,
                "captured": row["total_captured"] or 0,
            }
        return result


SCHEMA = """
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS initiatives (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    severity_class TEXT DEFAULT 'S2',
    autonomy_level TEXT DEFAULT 'L0',
    current_loop TEXT DEFAULT 'discovery',
    current_phase TEXT DEFAULT 'plan',
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outcomes (
    id TEXT PRIMARY KEY,
    initiative_id TEXT NOT NULL REFERENCES initiatives(id),
    metric TEXT NOT NULL,
    baseline TEXT NOT NULL,
    target_range TEXT NOT NULL,
    confidence_target TEXT DEFAULT '',
    timeframe TEXT DEFAULT '',
    scope TEXT DEFAULT '',
    constraint_desc TEXT DEFAULT '',
    operating_envelope TEXT DEFAULT '',
    known_confounders TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_suites (
    id TEXT PRIMARY KEY,
    initiative_id TEXT NOT NULL REFERENCES initiatives(id),
    level TEXT NOT NULL,
    description TEXT DEFAULT '',
    assertion_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id TEXT PRIMARY KEY,
    suite_id TEXT NOT NULL REFERENCES eval_suites(id),
    initiative_id TEXT NOT NULL REFERENCES initiatives(id),
    level TEXT NOT NULL,
    total INTEGER DEFAULT 0,
    passed INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    pass_rate REAL DEFAULT 0.0,
    notes TEXT DEFAULT '',
    commit_ref TEXT DEFAULT '',
    run_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pdca_entries (
    id TEXT PRIMARY KEY,
    initiative_id TEXT NOT NULL REFERENCES initiatives(id),
    loop TEXT NOT NULL,
    phase TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gate_decisions (
    id TEXT PRIMARY KEY,
    initiative_id TEXT NOT NULL REFERENCES initiatives(id),
    loop TEXT NOT NULL,
    result TEXT NOT NULL,
    rationale TEXT DEFAULT '',
    criteria_snapshot TEXT DEFAULT '',
    decided_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kill_criteria (
    id TEXT PRIMARY KEY,
    initiative_id TEXT NOT NULL REFERENCES initiatives(id),
    signal TEXT NOT NULL,
    threshold TEXT NOT NULL,
    current_value TEXT DEFAULT '',
    triggered INTEGER DEFAULT 0,
    loop TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS data_readiness (
    initiative_id TEXT PRIMARY KEY REFERENCES initiatives(id),
    existence INTEGER DEFAULT 0,
    accessibility INTEGER DEFAULT 0,
    quality INTEGER DEFAULT 0,
    latency INTEGER DEFAULT 0,
    history INTEGER DEFAULT 0,
    coverage INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    assessed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stakeholders (
    id TEXT PRIMARY KEY,
    initiative_id TEXT NOT NULL REFERENCES initiatives(id),
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    concern TEXT DEFAULT '',
    engagement_status TEXT DEFAULT 'not_engaged',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS initiative_scores (
    initiative_id TEXT PRIMARY KEY REFERENCES initiatives(id),
    business_value INTEGER NOT NULL,
    baseline_measurability INTEGER NOT NULL,
    data_readiness INTEGER NOT NULL,
    change_readiness INTEGER NOT NULL,
    reversibility INTEGER NOT NULL,
    compliance_burden INTEGER NOT NULL,
    platform_reuse INTEGER NOT NULL,
    notes TEXT DEFAULT '',
    scored_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roi_entries (
    id TEXT PRIMARY KEY,
    initiative_id TEXT NOT NULL REFERENCES initiatives(id),
    confidence TEXT DEFAULT 'projected',
    value_created REAL DEFAULT 0.0,
    value_captured REAL DEFAULT 0.0,
    tco_to_date REAL DEFAULT 0.0,
    notes TEXT DEFAULT '',
    recorded_at TEXT NOT NULL
);

-- CxO Dashboard: Workforce readiness assessments (org-level)
CREATE TABLE IF NOT EXISTS workforce_assessments (
    id TEXT PRIMARY KEY,
    assessment_date TEXT NOT NULL,
    total_headcount INTEGER DEFAULT 0,
    ai_trained_count INTEGER DEFAULT 0,
    ai_fluency_score REAL DEFAULT 0.0,
    roles_redesigned INTEGER DEFAULT 0,
    roles_total INTEGER DEFAULT 0,
    upskilling_completion_pct REAL DEFAULT 0.0,
    notes TEXT DEFAULT ''
);

-- CxO Dashboard: Governance tracking per initiative
CREATE TABLE IF NOT EXISTS governance_reviews (
    id TEXT PRIMARY KEY,
    initiative_id TEXT NOT NULL REFERENCES initiatives(id),
    review_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    reviewer TEXT DEFAULT '',
    findings TEXT DEFAULT '',
    reviewed_at TEXT NOT NULL
);

-- CxO Dashboard: Transformation type tagging on initiatives
-- Uses ALTER TABLE to add column if not exists (safe migration)
"""

MIGRATION_V2 = """
-- Add transformation_type to initiatives if not present
-- optimize = layering AI on existing process
-- redesign = redesigning key processes around AI
-- reinvent = creating new products/services or reinventing business models
"""
