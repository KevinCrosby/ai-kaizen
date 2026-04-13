"""Shared pytest fixtures for AI-Kaizen tests."""

import pytest
from pathlib import Path

from ai_kaizen.store.database import Store
from ai_kaizen.web.app import create_app


@pytest.fixture
def tmp_db(tmp_path):
    """Provide an isolated SQLite database."""
    db_path = tmp_path / "test.db"
    store = Store(db_path)
    yield store
    store.close()


@pytest.fixture
def app(tmp_path):
    """Create a Flask test app with isolated DB."""
    db_path = tmp_path / "test_web.db"
    app = create_app(db_path=db_path, testing=True)
    app.config["TESTING"] = True
    yield app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def seeded_client(app):
    """Flask test client with a pre-created initiative."""
    client = app.test_client()
    # Create an initiative via the store
    with app.app_context():
        store = app.get_store()
        store.create_initiative(
            id="test-init-001",
            name="Test Initiative",
            severity_class="S2",
        )
        store.set_config("current_initiative", "test-init-001")
    return client, "test-init-001"
