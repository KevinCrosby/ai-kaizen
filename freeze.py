"""Freeze the Flask app into static HTML for GitHub Pages."""

import os
import sys
from pathlib import Path

# Point at the template healthcare DB
os.environ["AI_KAIZEN_DB"] = str(Path.home() / ".ai-kaizen" / "template-healthcare.db")

from flask_frozen import Freezer
from ai_kaizen.web.app import create_app
from ai_kaizen.store.database import Store

app = create_app()
app.config["FREEZER_DESTINATION"] = str(Path(__file__).parent / "docs")
app.config["FREEZER_RELATIVE_URLS"] = True
app.config["FREEZER_IGNORE_MIMETYPE_WARNINGS"] = True

freezer = Freezer(app, with_no_argument_rules=True, log_url_for=False)


@freezer.register_generator
def generate_urls():
    """Generate URLs for all pages."""
    store = Store()
    for ini in store.list_initiatives():
        yield "main.initiative_detail", {"initiative_id": ini["id"]}
    store.close()


if __name__ == "__main__":
    freezer.freeze()
    print(f"\n✅ Static site generated in docs/")
