"""pytest plugin: record context for every failed test attempt.

Works with pytest-xdist (the controller writes every record) and pytest-rerunfailures
(a failed attempt that is retried is recorded with outcome "rerun"), which is
what lets the analyzer tell a real failure from a flaky one.
"""
from __future__ import annotations

import inspect
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

FAILURES_DIR = Path(os.getenv("AI_TRIAGE_DIR", "reports/failures"))
SCREENSHOTS_DIR = FAILURES_DIR / "screenshots"
MAX_TEXT = 6000

_attempts: dict[str, int] = {}
_is_xdist_worker = False


def _safe_name(nodeid: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", nodeid)[-150:]


def pytest_configure(config):
    global _is_xdist_worker
    # xdist workers have `workerinput`. Only the controller cleans up and
    # writes records: it receives every worker's reports, so writing from
    # both sides would duplicate them.
    _is_xdist_worker = hasattr(config, "workerinput")
    if not _is_xdist_worker and FAILURES_DIR.exists():
        shutil.rmtree(FAILURES_DIR)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    if report.when == "call" and report.failed:
        _attempts[item.nodeid] = _attempts.get(item.nodeid, 0) + 1
        attempt = _attempts[item.nodeid]
        report.user_properties.append(("triage_attempt", attempt))
        report.user_properties.append(("triage_markers", sorted({m.name for m in item.iter_markers()})))
        try:
            source = inspect.getsource(item.obj)
        except (OSError, TypeError):
            source = ""
        report.user_properties.append(("triage_source", source[:MAX_TEXT]))

        page = item.funcargs.get("page")
        if page is not None:
            try:
                SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
                path = SCREENSHOTS_DIR / f"{_safe_name(item.nodeid)}__attempt{attempt}.png"
                page.screenshot(path=str(path), full_page=False)
                report.user_properties.append(("triage_screenshot", str(path)))
                report.user_properties.append(("triage_url", page.url))
            except Exception:  # never let triage break the test run
                pass
    return report


def pytest_runtest_logreport(report):
    # rerunfailures marks retried attempts as "rerun" before this hook runs.
    if _is_xdist_worker or report.when != "call" or report.outcome not in ("failed", "rerun"):
        return
    props = dict(report.user_properties)
    record = {
        "nodeid": report.nodeid,
        "outcome": report.outcome,
        "attempt": props.get("triage_attempt", 1),
        "duration_s": round(report.duration, 2),
        "error": (report.longreprtext or "")[-MAX_TEXT:],
        "test_source": props.get("triage_source", ""),
        "markers": props.get("triage_markers", []),
        "screenshot": props.get("triage_screenshot"),
        "page_url": props.get("triage_url"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    FAILURES_DIR.mkdir(parents=True, exist_ok=True)
    with open(FAILURES_DIR / "failures.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
