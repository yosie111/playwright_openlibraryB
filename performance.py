"""Performance measurement utilities for page navigations."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


async def measure_page_performance(
    page,
    url: str,
    threshold_ms: int,
    label: str,
) -> dict:
    """Measure timings after navigation and return metrics + metadata."""
    metrics = await _read_browser_metrics(page)

    load_time = metrics["load_time_ms"]
    exceeded = (
        load_time is not None
        and load_time != 0
        and load_time > threshold_ms
    )

    if exceeded:
        logger.warning(
            "Performance threshold exceeded for %s: "
            "load_time_ms=%s > threshold_ms=%s",
            label, load_time, threshold_ms,
        )

    return {
        "label": label,
        "url": url,
        "threshold_ms": threshold_ms,
        "load_time_ms": metrics["load_time_ms"],
        "dom_content_loaded_ms": metrics["dom_content_loaded_ms"],
        "first_paint_ms": metrics["first_paint_ms"],
        "exceeded_threshold": exceeded,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _read_browser_metrics(page) -> dict:
    """Read timing values from the browser's Performance API."""
    js = """
    () => {
        const nav = performance.getEntriesByType('navigation')[0];
        const paint = performance.getEntriesByType('paint')
            .find(p => p.name === 'first-paint');

        return {
            load_time_ms: nav ? Math.round(nav.loadEventEnd) : null,
            dom_content_loaded_ms: nav
                ? Math.round(nav.domContentLoadedEventEnd) : null,
            first_paint_ms: paint ? Math.round(paint.startTime) : null,
        };
    }
    """
    return await page.evaluate(js)


class PerformanceCollector:
    """Collects measurements and writes a JSON report at the end."""

    def __init__(self):
        self.measurements: list[dict] = []

    def add(self, measurement: dict) -> None:
        self.measurements.append(measurement)

    def write_report(self, path: str) -> None:
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_measurements": len(self.measurements),
            "exceeded_count": sum(
                1 for m in self.measurements if m["exceeded_threshold"]
            ),
            "measurements": self.measurements,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(
            "Performance report written to %s (%d measurements)",
            path, len(self.measurements),
        )
