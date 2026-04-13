"""Tests for logging configuration and metrics collector."""

from __future__ import annotations

import json
import logging
import threading

import pytest

from ai_kaizen.logging_config import (
    _HumanFormatter,
    _JsonFormatter,
    request_id_var,
    setup_logging,
)
from ai_kaizen.metrics import MetricsCollector, metrics


# ── MetricsCollector ─────────────────────────────────────────────────────


class TestMetricsCollector:
    def setup_method(self):
        self.mc = MetricsCollector()

    def test_inc_default(self):
        self.mc.inc("requests")
        self.mc.inc("requests")
        snap = self.mc.snapshot()
        assert snap["counters"]["requests"] == 2

    def test_inc_with_tags(self):
        self.mc.inc("http", tags={"method": "GET", "status": "200"})
        self.mc.inc("http", tags={"method": "POST", "status": "201"})
        snap = self.mc.snapshot()
        assert snap["counters"]["http{method=GET,status=200}"] == 1
        assert snap["counters"]["http{method=POST,status=201}"] == 1

    def test_observe_histogram(self):
        for v in [10, 20, 30, 40, 50]:
            self.mc.observe("duration_ms", v)
        snap = self.mc.snapshot()
        h = snap["histograms"]["duration_ms"]
        assert h["count"] == 5
        assert h["min"] == 10
        assert h["max"] == 50
        assert h["avg"] == 30.0
        assert h["p50"] == 30.0

    def test_timer_context_manager(self):
        import time

        with self.mc.timer("op_ms"):
            time.sleep(0.01)
        snap = self.mc.snapshot()
        assert "op_ms" in snap["histograms"]
        assert snap["histograms"]["op_ms"]["count"] == 1
        assert snap["histograms"]["op_ms"]["min"] >= 5  # at least 5ms

    def test_reset(self):
        self.mc.inc("x")
        self.mc.observe("y", 1.0)
        self.mc.reset()
        snap = self.mc.snapshot()
        assert snap["counters"] == {}
        assert snap["histograms"] == {}

    def test_uptime(self):
        import time

        time.sleep(0.05)
        snap = self.mc.snapshot()
        assert snap["uptime_seconds"] >= 0.04

    def test_thread_safety(self):
        """Concurrent increments should not lose counts."""
        errors = []

        def worker():
            try:
                for _ in range(1000):
                    self.mc.inc("concurrent")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        snap = self.mc.snapshot()
        assert snap["counters"]["concurrent"] == 4000

    def test_p95_p99_require_enough_data(self):
        for i in range(10):
            self.mc.observe("small", float(i))
        snap = self.mc.snapshot()
        assert snap["histograms"]["small"]["p95"] is None
        assert snap["histograms"]["small"]["p99"] is None


# ── JSON Formatter ───────────────────────────────────────────────────────


class TestJsonFormatter:
    def test_formats_valid_json(self):
        fmt = _JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello %s", args=("world",), exc_info=None,
        )
        line = fmt.format(record)
        obj = json.loads(line)
        assert obj["msg"] == "hello world"
        assert obj["level"] == "INFO"
        assert "ts" in obj

    def test_includes_request_id(self):
        token = request_id_var.set("abc123")
        try:
            fmt = _JsonFormatter()
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="", lineno=0,
                msg="test", args=(), exc_info=None,
            )
            line = fmt.format(record)
            obj = json.loads(line)
            assert obj["request_id"] == "abc123"
        finally:
            request_id_var.reset(token)

    def test_includes_exception(self):
        fmt = _JsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = logging.LogRecord(
                name="test", level=logging.ERROR, pathname="", lineno=0,
                msg="err", args=(), exc_info=sys.exc_info(),
            )
        line = fmt.format(record)
        obj = json.loads(line)
        assert "exception" in obj
        assert "boom" in obj["exception"]


# ── Human Formatter ──────────────────────────────────────────────────────


class TestHumanFormatter:
    def test_formats_readable_output(self):
        fmt = _HumanFormatter()
        record = logging.LogRecord(
            name="ai_kaizen.web", level=logging.WARNING, pathname="", lineno=0,
            msg="slow", args=(), exc_info=None,
        )
        line = fmt.format(record)
        assert "WARNING" in line
        assert "slow" in line
        assert "ai_kaizen.web" in line


# ── Singleton metrics ────────────────────────────────────────────────────


class TestModuleSingleton:
    def test_singleton_exists(self):
        """The module-level metrics object should be a MetricsCollector."""
        assert isinstance(metrics, MetricsCollector)


# ── Web /metrics endpoint ────────────────────────────────────────────────


class TestMetricsEndpoint:
    def test_metrics_returns_json(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "uptime_seconds" in data
        assert "counters" in data
        assert "histograms" in data

    def test_metrics_tracks_requests(self, client):
        # Make a few requests first
        client.get("/")
        client.get("/")
        resp = client.get("/metrics")
        data = resp.get_json()
        # Should have counted at least the 2 index requests
        total = sum(v for k, v in data["counters"].items() if k.startswith("http_requests_total"))
        assert total >= 2


# ── Request ID ───────────────────────────────────────────────────────────


class TestRequestId:
    def test_response_has_request_id_header(self, client):
        resp = client.get("/")
        assert "X-Request-ID" in resp.headers
        assert len(resp.headers["X-Request-ID"]) > 0

    def test_custom_request_id_propagated(self, client):
        resp = client.get("/", headers={"X-Request-ID": "custom-123"})
        assert resp.headers["X-Request-ID"] == "custom-123"
