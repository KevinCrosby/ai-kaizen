"""Flask app factory for AI-Kaizen web UI."""

from __future__ import annotations

import logging
import os
import secrets
import time
import uuid
from pathlib import Path

from flask import Flask, g, jsonify, request

from ai_kaizen.logging_config import request_id_var, setup_logging
from ai_kaizen.metrics import metrics
from ai_kaizen.store.database import Store, get_db_path

logger = logging.getLogger(__name__)

csrf = None  # lazy init


def _get_csrf():
    global csrf
    if csrf is None:
        from flask_wtf.csrf import CSRFProtect
        csrf = CSRFProtect()
    return csrf


def create_app(db_path: Path | None = None, testing: bool = False) -> Flask:
    """Application factory."""
    setup_logging()

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    app.config["SECRET_KEY"] = os.environ.get(
        "AI_KAIZEN_SECRET_KEY", secrets.token_hex(32)
    )
    app.config["WTF_CSRF_ENABLED"] = not testing
    app.config["DB_PATH"] = db_path or get_db_path()

    _get_csrf().init_app(app)

    # Run migrations once at startup
    try:
        startup_store = Store(app.config["DB_PATH"], run_migrations=True)
        startup_store.close()
    except Exception:
        logger.exception("Failed to run DB migrations at startup")
        raise

    # --- Store lifecycle (lazy per-request) ---
    def get_store() -> Store:
        if "store" not in g:
            g.store = Store(app.config["DB_PATH"], run_migrations=False)
        return g.store

    app.get_store = get_store  # type: ignore[attr-defined]

    @app.teardown_appcontext
    def close_store(exc: BaseException | None) -> None:
        store = g.pop("store", None)
        if store is not None:
            try:
                store.close()
            except Exception:
                logger.warning("Error closing DB connection", exc_info=True)

    # --- Request lifecycle: ID, timing, metrics ---
    @app.before_request
    def before_request_hook() -> None:
        rid = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        g.request_id = rid
        g.start_time = time.monotonic()
        request_id_var.set(rid)

    @app.after_request
    def after_request_hook(response):
        duration_ms = (time.monotonic() - getattr(g, "start_time", time.monotonic())) * 1000
        rid = getattr(g, "request_id", "-")
        response.headers["X-Request-ID"] = rid

        # Skip static file logging
        if not request.path.startswith("/static"):
            metrics.inc("http_requests_total")
            metrics.inc("http_requests_total", tags={"method": request.method, "status": str(response.status_code)})
            metrics.observe("http_request_duration_ms", duration_ms)
            logger.info(
                "%s %s %s %.0fms",
                request.method, request.path, response.status_code, duration_ms,
            )

        return response

    # --- Metrics endpoint ---
    @app.route("/metrics")
    def metrics_endpoint():
        """Process-local technical metrics (counters, histograms)."""
        return jsonify(metrics.snapshot())

    # --- Error handlers ---
    from ai_kaizen.web.errors import register_error_handlers

    register_error_handlers(app)

    # --- Routes ---
    from ai_kaizen.web.routes import bp

    app.register_blueprint(bp)

    logger.info("AI-Kaizen web app initialized (db=%s, testing=%s)", app.config["DB_PATH"], testing)
    return app
