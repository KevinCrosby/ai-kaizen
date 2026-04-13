"""Flask app factory for AI-Kaizen web UI."""

from __future__ import annotations

import logging
import os
import secrets
import time
from pathlib import Path

from flask import Flask, g, request
from flask_wtf.csrf import CSRFProtect

from ai_kaizen.store.database import Store, get_db_path

csrf = CSRFProtect()


def create_app(db_path: Path | None = None, testing: bool = False) -> Flask:
    """Application factory."""
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

    csrf.init_app(app)

    # --- Logging ---
    if not app.debug and not testing:
        handler = logging.StreamHandler()
        handler.setLevel(logging.WARNING)
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        )
        app.logger.addHandler(handler)

    # Run migrations once at startup
    startup_store = Store(app.config["DB_PATH"], run_migrations=True)
    startup_store.close()

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
            store.close()

    # --- Debug request logging ---
    if app.debug:

        @app.before_request
        def log_request_start() -> None:
            g.start_time = time.time()

        @app.after_request
        def log_request_end(response):
            duration = (time.time() - getattr(g, "start_time", time.time())) * 1000
            app.logger.debug(
                "%s %s %s (%.0fms)",
                request.method,
                request.path,
                response.status_code,
                duration,
            )
            return response

    # --- Error handlers ---
    from ai_kaizen.web.errors import register_error_handlers

    register_error_handlers(app)

    # --- Routes ---
    from ai_kaizen.web.routes import bp

    app.register_blueprint(bp)

    return app
