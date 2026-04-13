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
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self):
        self.conn.executescript(SCHEMA)
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
"""
