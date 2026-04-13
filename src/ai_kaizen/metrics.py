"""Lightweight in-process metrics collector for AI-Kaizen.

Tracks counters and timing histograms for debugging and operational insight.
All metrics are per-process and reset on restart. Business metrics are derived
from the database, not tracked in RAM.

Usage:
    from ai_kaizen.metrics import metrics

    metrics.inc("requests_total")
    metrics.inc("requests_total", tags={"method": "GET", "path": "/executive"})

    with metrics.timer("request_duration_ms"):
        ...  # timed block

    metrics.snapshot()  # → dict of all metrics
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Any


class MetricsCollector:
    """Thread-safe in-memory metrics store."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = defaultdict(int)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._start_time = time.monotonic()

    def inc(self, name: str, value: int = 1, tags: dict[str, str] | None = None) -> None:
        """Increment a counter."""
        key = self._key(name, tags)
        with self._lock:
            self._counters[key] += value

    def observe(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a histogram observation (e.g. duration in ms)."""
        key = self._key(name, tags)
        with self._lock:
            self._histograms[key].append(value)

    @contextmanager
    def timer(self, name: str, tags: dict[str, str] | None = None):
        """Context manager that records elapsed time in milliseconds."""
        start = time.monotonic()
        try:
            yield
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000
            self.observe(name, elapsed_ms, tags)

    def snapshot(self) -> dict[str, Any]:
        """Return a point-in-time snapshot of all metrics."""
        with self._lock:
            counters = dict(self._counters)
            histograms = {}
            for k, values in self._histograms.items():
                if values:
                    sorted_v = sorted(values)
                    n = len(sorted_v)
                    histograms[k] = {
                        "count": n,
                        "min": round(sorted_v[0], 2),
                        "max": round(sorted_v[-1], 2),
                        "avg": round(sum(sorted_v) / n, 2),
                        "p50": round(sorted_v[n // 2], 2),
                        "p95": round(sorted_v[int(n * 0.95)], 2) if n >= 20 else None,
                        "p99": round(sorted_v[int(n * 0.99)], 2) if n >= 100 else None,
                    }
        return {
            "uptime_seconds": round(time.monotonic() - self._start_time, 1),
            "counters": counters,
            "histograms": histograms,
        }

    def reset(self) -> None:
        """Clear all metrics (useful for tests)."""
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._start_time = time.monotonic()

    @staticmethod
    def _key(name: str, tags: dict[str, str] | None) -> str:
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"


# Module-level singleton
metrics = MetricsCollector()
