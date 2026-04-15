# AI-Kaizen — Copilot Instructions

## Build & Test

```bash
# Install (editable + dev deps)
pip install -e ".[dev]"

# Run full test suite (92 tests)
python -m pytest tests/ -q

# Run a single test file
python -m pytest tests/test_web.py -q

# Run a single test class or method
python -m pytest tests/test_web.py::TestValueTracking::test_record_creation_event -q

# Run with coverage
python -m pytest tests/ --cov=ai_kaizen --cov-report=term-missing
```

No linter or type-checker is configured. No CI pipeline yet.

## Architecture

```
CLI (click)  →  Services  →  Store (SQLite)
Flask Web UI →  Services  →  Store (SQLite)
```

- **CLI** (`cli.py`): Click-based, uses `_KaizenGroup` custom group for top-level exception handling and logging setup.
- **Services** (`services/core.py`): `InitiativeService`, `EvalService`, `PDCAService`, `OutcomeService`, `DataReadinessService`, `PMOService`. Each takes a `Store` instance.
- **Store** (`store/database.py`): Single `Store` class wrapping SQLite. ~15 tables. All queries go through `_execute()`.
- **Web** (`web/`): Flask factory pattern via `create_app()`. Routes in `routes.py`, templates in `templates/`.
- **Domain** (`domain/models.py`): Pydantic models for validation.

## Database — `_execute()` and `commit=True`

**Critical convention**: All database queries must go through `self._execute(sql, params, commit=False)`.

- **Read operations**: `self._execute("SELECT ...", [param])` — default `commit=False`.
- **Write operations**: `self._execute("INSERT/UPDATE/DELETE ...", [param], commit=True)` — must pass `commit=True`.
- **Never call `self.conn.commit()` directly** outside of `_migrate()`. The `_execute` wrapper handles commits.
- **Never call `self.conn.execute()` directly**. The wrapper provides timing, slow-query detection (>100ms), and error metrics.

When doing bulk replacements in `database.py`, verify each call site individually — automated find-and-replace has caused syntax errors and missing commits (26-test failure incident).

## Flask App Patterns

- **Factory**: `create_app(db_path=None, testing=False)` — pass `db_path` to override default.
- **Store access**: `app.get_store()` — returns the shared `Store` instance. Use inside `with app.app_context():` in tests.
- **CSRF**: Lazy-initialized via `_get_csrf()` to avoid import-time side effects.
- **Request IDs**: Auto-generated UUID per request, set in `before_request`, available via `X-Request-ID` header.
- **Test fixtures** (in `conftest.py`):
  - `tmp_db` — isolated `Store` with temp SQLite file.
  - `app` / `client` — Flask test app with isolated DB.
  - `seeded_client` — returns `(client, initiative_id)` with a pre-created initiative.

## Database Path & Environment

Default DB: `~/.ai-kaizen/kaizen.db`

Override with `AI_KAIZEN_DB` env var:
```bash
export AI_KAIZEN_DB=~/.ai-kaizen/template-healthcare.db
ai-kaizen serve --port 5001
```

The template healthcare DB at `~/.ai-kaizen/template-healthcare.db` has seeded data (2 initiatives with full eval suites, PDCA, PMO scores, ROI, and value events). Use it for demos; don't write tests against it.

## macOS Shell Gotchas

- **No `grep -P`**: macOS grep doesn't support Perl regex. Use `grep -E` (extended) or pipe to `python3 -c` for complex patterns.
- **Heredoc variable expansion**: When embedding Python in bash heredocs, use `<< 'EOF'` (quoted) to prevent `$variable` expansion. If you need bash vars inside Python, pass them as env vars or arguments — not inline `$VAR` references.
- **No `killall`/`pkill`**: Use `kill <PID>` with specific process IDs.

## Logging

- Centralized in `logging_config.py`. Call `setup_logging()` once (idempotent via `_CONFIGURED` flag).
- Logger namespace: `ai_kaizen.*` — get loggers via `logging.getLogger(__name__)`.
- JSON format via `AI_KAIZEN_LOG_JSON=1` env var.
- Log at boundaries only — don't duplicate exception logging in both caller and callee.
