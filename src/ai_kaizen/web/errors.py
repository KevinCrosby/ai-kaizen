"""Error handlers for AI-Kaizen web app."""

from __future__ import annotations

import logging

from flask import Flask, render_template

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", code=400, message=str(e.description)), 400

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.exception("Internal server error")
        return (
            render_template(
                "error.html", code=500, message="Something went wrong. Check the logs."
            ),
            500,
        )
