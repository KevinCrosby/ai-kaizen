"""Web routes for AI-Kaizen — thin adapters over service layer."""

from __future__ import annotations

import json
import logging

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from ai_kaizen.services.core import (
    DataReadinessService,
    EvalService,
    InitiativeService,
    OutcomeService,
    PDCAService,
    PMOService,
)

logger = logging.getLogger(__name__)

bp = Blueprint("main", __name__)


# ── helpers ──────────────────────────────────────────────────────────────

def _store():
    return current_app.get_store()


def _get_initiative_or_404(initiative_id: str) -> dict:
    """Load initiative by ID, abort 404 if not found."""
    store = _store()
    ini = store.get_initiative(initiative_id)
    if not ini:
        abort(404)
    return dict(ini)


def _flash_errors(errors: list[str]) -> None:
    for e in errors:
        flash(e, "error")


# ── validation helpers ───────────────────────────────────────────────────

def _validate_int(value: str, field: str, min_val: int = 0, max_val: int = 999999) -> tuple[int | None, str | None]:
    try:
        v = int(value)
    except (ValueError, TypeError):
        return None, f"{field} must be a whole number"
    if v < min_val or v > max_val:
        return None, f"{field} must be between {min_val} and {max_val}"
    return v, None


def _validate_float(value: str, field: str, min_val: float = 0) -> tuple[float | None, str | None]:
    try:
        v = float(value)
    except (ValueError, TypeError):
        return None, f"{field} must be a number"
    if v < min_val:
        return None, f"{field} must be >= {min_val}"
    return v, None


def _validate_required(value: str | None, field: str) -> str | None:
    if not value or not value.strip():
        return f"{field} is required"
    return None


VALID_SEVERITIES = {"S0", "S1", "S2", "S3"}
VALID_PHASES = {"plan", "do", "check", "act"}
VALID_LEVELS = {"L0", "L1", "L2", "L2.5", "L3"}
VALID_CONFIDENCE = {"projected", "estimated", "measured", "validated"}


# ── dashboard ────────────────────────────────────────────────────────────

@bp.route("/")
def dashboard():
    store = _store()
    svc = InitiativeService(store)
    pmo = PMOService(store)
    initiatives = svc.list_all()
    portfolio = pmo.portfolio_summary()
    capacity = pmo.capacity_check()
    return render_template(
        "dashboard.html",
        initiatives=initiatives,
        portfolio=portfolio,
        capacity=capacity,
    )


# ── initiatives ──────────────────────────────────────────────────────────

@bp.route("/initiatives", methods=["GET"])
def initiative_list():
    store = _store()
    initiatives = InitiativeService(store).list_all()
    scores = {s["initiative_id"]: s for s in PMOService(store).ranked_backlog()}
    return render_template("initiative_list.html", initiatives=initiatives, scores=scores)


@bp.route("/initiatives", methods=["POST"])
def initiative_create():
    name = request.form.get("name", "").strip()
    severity = request.form.get("severity", "S2")
    description = request.form.get("description", "").strip()

    errors = []
    if err := _validate_required(name, "Name"):
        errors.append(err)
    if severity not in VALID_SEVERITIES:
        errors.append(f"Severity must be one of: {', '.join(sorted(VALID_SEVERITIES))}")

    if errors:
        _flash_errors(errors)
        return redirect(url_for("main.initiative_list"))

    try:
        store = _store()
        ini = InitiativeService(store).create(name=name, description=description, severity=severity)
        flash(f"Created initiative: {ini['name']}", "success")
        return redirect(url_for("main.initiative_detail", initiative_id=ini["id"]))
    except Exception:
        logger.exception("Failed to create initiative")
        flash("Failed to create initiative", "error")
        return redirect(url_for("main.initiative_list"))


@bp.route("/initiatives/<initiative_id>")
def initiative_detail(initiative_id: str):
    ini = _get_initiative_or_404(initiative_id)
    store = _store()

    outcomes = OutcomeService(store).list(initiative_id)
    suites = EvalService(store).list_suites(initiative_id)
    eval_svc = EvalService(store)
    eval_runs = {}
    for s in suites:
        run = store.latest_eval_run(initiative_id, s["level"])
        if run:
            eval_runs[s["level"]] = dict(run)

    entries = PDCAService(store).list_entries(initiative_id)
    gate = PDCAService(store).check_gate(initiative_id)
    dr = DataReadinessService(store).get(initiative_id)
    score = store.get_initiative_score(initiative_id)
    roi = store.latest_roi(initiative_id)

    return render_template(
        "initiative_detail.html",
        ini=ini,
        outcomes=outcomes,
        suites=suites,
        eval_runs=eval_runs,
        entries=entries,
        gate=gate,
        dr=dr,
        score=score,
        roi=roi,
    )


# ── outcomes ─────────────────────────────────────────────────────────────

@bp.route("/initiatives/<initiative_id>/outcome", methods=["POST"])
def outcome_create(initiative_id: str):
    _get_initiative_or_404(initiative_id)

    metric = request.form.get("metric", "").strip()
    baseline = request.form.get("baseline", "").strip()
    target = request.form.get("target", "").strip()
    scope = request.form.get("scope", "").strip()
    timeframe = request.form.get("timeframe", "").strip()

    errors = []
    if err := _validate_required(metric, "Metric"):
        errors.append(err)
    if err := _validate_required(baseline, "Baseline"):
        errors.append(err)
    if err := _validate_required(target, "Target"):
        errors.append(err)

    if errors:
        _flash_errors(errors)
        return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))

    try:
        store = _store()
        OutcomeService(store).create(
            initiative_id=initiative_id, metric=metric,
            baseline=baseline, target_range=target,
            scope=scope, timeframe=timeframe,
        )
        flash(f"Outcome added: {metric}", "success")
    except Exception:
        logger.exception("Failed to add outcome")
        flash("Failed to add outcome", "error")

    return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))


# ── evals ────────────────────────────────────────────────────────────────

@bp.route("/initiatives/<initiative_id>/eval/scaffold", methods=["POST"])
def eval_scaffold(initiative_id: str):
    _get_initiative_or_404(initiative_id)
    level = request.form.get("level", "")
    description = request.form.get("description", "").strip()

    if level not in VALID_LEVELS:
        flash(f"Level must be one of: {', '.join(sorted(VALID_LEVELS))}", "error")
        return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))

    try:
        store = _store()
        EvalService(store).create_suite(initiative_id, level=level, description=description)
        flash(f"Eval suite created: {level}", "success")
    except Exception:
        logger.exception("Failed to create eval suite")
        flash("Failed to create eval suite", "error")

    return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))


@bp.route("/initiatives/<initiative_id>/eval/record", methods=["POST"])
def eval_record(initiative_id: str):
    _get_initiative_or_404(initiative_id)
    level = request.form.get("level", "")

    errors = []
    if level not in VALID_LEVELS:
        errors.append(f"Level must be one of: {', '.join(sorted(VALID_LEVELS))}")

    total, err = _validate_int(request.form.get("total", ""), "Total", min_val=1)
    if err:
        errors.append(err)
    passed, err = _validate_int(request.form.get("passed", ""), "Passed", min_val=0)
    if err:
        errors.append(err)

    if total is not None and passed is not None and passed > total:
        errors.append("Passed cannot exceed Total")

    if errors:
        _flash_errors(errors)
        return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))

    try:
        store = _store()
        suites = EvalService(store).list_suites(initiative_id)
        suite = next((s for s in suites if s["level"] == level), None)
        if not suite:
            flash(f"No eval suite for level {level}. Create one first.", "error")
            return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))

        notes = request.form.get("notes", "").strip()
        EvalService(store).record_run(
            initiative_id=initiative_id, suite_id=suite["id"],
            level=level, total=total, passed=passed, notes=notes,
        )
        rate = (passed / total * 100) if total else 0
        flash(f"Eval recorded: {level} — {rate:.0f}% ({passed}/{total})", "success")
    except Exception:
        logger.exception("Failed to record eval run")
        flash("Failed to record eval run", "error")

    return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))


# ── PDCA ─────────────────────────────────────────────────────────────────

@bp.route("/initiatives/<initiative_id>/pdca", methods=["POST"])
def pdca_log(initiative_id: str):
    ini = _get_initiative_or_404(initiative_id)
    phase = request.form.get("phase", "")
    note = request.form.get("note", "").strip()

    errors = []
    if phase not in VALID_PHASES:
        errors.append(f"Phase must be one of: {', '.join(sorted(VALID_PHASES))}")
    if err := _validate_required(note, "Note"):
        errors.append(err)

    if errors:
        _flash_errors(errors)
        return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))

    try:
        store = _store()
        PDCAService(store).log_entry(
            initiative_id=initiative_id,
            loop=ini["current_loop"],
            phase=phase,
            note=note,
        )
        flash(f"Logged {phase}: {note[:60]}...", "success")
    except Exception:
        logger.exception("Failed to log PDCA entry")
        flash("Failed to log PDCA entry", "error")

    return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))


# ── PMO score ────────────────────────────────────────────────────────────

@bp.route("/initiatives/<initiative_id>/pmo/score", methods=["POST"])
def pmo_score(initiative_id: str):
    _get_initiative_or_404(initiative_id)

    fields = {
        "business_value": "Business Value",
        "measurability": "Measurability",
        "data_readiness": "Data Readiness",
        "change_risk": "Change Risk",
        "reversibility": "Reversibility",
        "compliance_risk": "Compliance Risk",
        "reuse_potential": "Reuse Potential",
    }
    scores = {}
    errors = []
    for key, label in fields.items():
        val, err = _validate_int(request.form.get(key, ""), label, min_val=1, max_val=5)
        if err:
            errors.append(err)
        else:
            scores[key] = val

    if errors:
        _flash_errors(errors)
        return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))

    try:
        store = _store()
        notes = request.form.get("notes", "").strip()
        PMOService(store).score_initiative(initiative_id=initiative_id, notes=notes, **scores)
        flash("PMO score saved", "success")
    except Exception:
        logger.exception("Failed to save PMO score")
        flash("Failed to save PMO score", "error")

    return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))


# ── data readiness ───────────────────────────────────────────────────────

@bp.route("/initiatives/<initiative_id>/assess", methods=["POST"])
def data_readiness(initiative_id: str):
    _get_initiative_or_404(initiative_id)

    dims = ["existence", "accessibility", "quality", "latency", "history", "coverage"]
    scores = {}
    errors = []
    for dim in dims:
        val, err = _validate_int(request.form.get(dim, ""), dim.title(), min_val=0, max_val=3)
        if err:
            errors.append(err)
        else:
            scores[dim] = val

    if errors:
        _flash_errors(errors)
        return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))

    try:
        store = _store()
        notes = request.form.get("notes", "").strip()
        DataReadinessService(store).assess(initiative_id=initiative_id, scores=scores, notes=notes)
        flash("Data readiness assessment saved", "success")
    except Exception:
        logger.exception("Failed to save data readiness")
        flash("Failed to save data readiness", "error")

    return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))


# ── ROI ──────────────────────────────────────────────────────────────────

@bp.route("/initiatives/<initiative_id>/roi", methods=["POST"])
def roi_track(initiative_id: str):
    _get_initiative_or_404(initiative_id)

    errors = []
    confidence = request.form.get("confidence", "")
    if confidence not in VALID_CONFIDENCE:
        errors.append(f"Confidence must be one of: {', '.join(sorted(VALID_CONFIDENCE))}")

    value_created, err = _validate_float(request.form.get("value_created", ""), "Value Created")
    if err:
        errors.append(err)
    value_captured, err = _validate_float(request.form.get("value_captured", ""), "Value Captured")
    if err:
        errors.append(err)
    tco, err = _validate_float(request.form.get("tco", ""), "TCO")
    if err:
        errors.append(err)

    if errors:
        _flash_errors(errors)
        return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))

    try:
        store = _store()
        notes = request.form.get("notes", "").strip()
        PMOService(store).record_roi(
            initiative_id=initiative_id, confidence=confidence,
            value_created=value_created, value_captured=value_captured,
            tco_to_date=tco, notes=notes,
        )
        flash("ROI recorded", "success")
    except Exception:
        logger.exception("Failed to record ROI")
        flash("Failed to record ROI", "error")

    return redirect(url_for("main.initiative_detail", initiative_id=initiative_id))


# ── portfolio ROI ────────────────────────────────────────────────────────

@bp.route("/portfolio/roi")
def portfolio_roi():
    store = _store()
    pmo = PMOService(store)
    portfolio = pmo.portfolio_summary()
    initiatives = InitiativeService(store).list_all()
    roi_data = []
    for ini in initiatives:
        roi = store.latest_roi(ini["id"])
        if roi:
            roi_data.append({"name": ini["name"], "id": ini["id"], **dict(roi)})
    return render_template("portfolio_roi.html", portfolio=portfolio, roi_data=roi_data)


# ── export ───────────────────────────────────────────────────────────────

@bp.route("/initiatives/<initiative_id>/export")
def initiative_export(initiative_id: str):
    ini = _get_initiative_or_404(initiative_id)
    fmt = request.args.get("format", "json")
    store = _store()

    data = {
        "initiative": ini,
        "outcomes": OutcomeService(store).list(initiative_id),
        "eval_suites": [dict(s) for s in EvalService(store).list_suites(initiative_id)],
        "pdca_entries": [dict(e) for e in PDCAService(store).list_entries(initiative_id)],
        "data_readiness": DataReadinessService(store).get(initiative_id),
        "score": store.get_initiative_score(initiative_id),
        "roi": store.latest_roi(initiative_id),
    }

    if fmt == "json":
        return current_app.response_class(
            json.dumps(data, indent=2, default=str),
            mimetype="application/json",
        )

    # Default: render as HTML
    return render_template("export.html", ini=ini, data=data)
