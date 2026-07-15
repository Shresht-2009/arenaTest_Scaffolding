"""
Telemetry Stats Collector.
"""

from __future__ import annotations

import time
from typing import Dict, Any
from collections import defaultdict


class StatsCollector:
    """
    Collects real-time stats for dashboard.
    """

    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.timings: Dict[str, list] = defaultdict(list)
        self.gauges: Dict[str, float] = {}
        self.start_time = time.time()

    def inc(self, key: str, value: int = 1):
        self.counters[key] += value

    def record_timing(self, key: str, duration_ms: float):
        timings = self.timings[key]
        timings.append(duration_ms)
        if len(timings) > 1000:
            timings.pop(0)

    def set_gauge(self, key: str, value: float):
        self.gauges[key] = value

    def get_stats(self) -> Dict[str, Any]:
        uptime = time.time() - self.start_time
        avg_timings = {}
        for k, v in self.timings.items():
            avg_timings[k] = sum(v) / len(v) if v else 0

        return {
            "uptime_seconds": uptime,
            "counters": dict(self.counters),
            "avg_timings_ms": avg_timings,
            "gauges": dict(self.gauges),
        }

    def reset(self):
        self.counters.clear()
        self.timings.clear()
        self.gauges.clear()
        self.start_time = time.time()


# Global singleton
_stats_instance: StatsCollector | None = None


def get_stats_collector() -> StatsCollector:
    global _stats_instance
    if _stats_instance is None:
        _stats_instance = StatsCollector()
    return _stats_instance
