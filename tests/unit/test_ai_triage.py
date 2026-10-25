"""Unit tests for the AI triage module. They run offline: Claude is replaced
by a fake client, so they are fast and free."""
import json
from types import SimpleNamespace

import pytest

from ai_triage import analyzer

pytestmark = pytest.mark.unit


def _record(nodeid, outcome, attempt=1, error="AssertionError: boom"):
    return {"nodeid": nodeid, "outcome": outcome, "attempt": attempt, "error": error,
            "test_source": "def test_x(): ...", "markers": ["ui"], "screenshot": None,
            "page_url": None, "duration_s": 1.2}


class FakeClient:
    def __init__(self, reply: str):
        self.reply = reply
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.reply)])


def test_group_marks_test_that_passed_on_retry_as_flaky():
    cases = analyzer.group_failures([_record("t::flaky", "rerun")])
    assert cases[0].final_status == "passed_on_retry"


def test_group_marks_test_that_failed_every_attempt_as_failed():
    records = [_record("t::broken", "rerun", 1), _record("t::broken", "failed", 2)]
    case = analyzer.group_failures(records)[0]
    assert case.final_status == "failed"
    assert len(case.attempts) == 2


def test_real_failures_are_sorted_before_flaky_ones():
    records = [_record("a::flaky", "rerun"), _record("z::broken", "failed")]
    assert [c.nodeid for c in analyzer.group_failures(records)] == ["z::broken", "a::flaky"]


def test_parse_response_extracts_json_wrapped_in_text():
    data = analyzer.parse_response('Here you go:\n```json\n{"category": "FLAKY_TEST"}\n```')
    assert data["category"] == "FLAKY_TEST"


def test_parse_response_normalizes_unknown_category():
    assert analyzer.parse_response('{"category": "ALIENS"}')["category"] == "UNKNOWN"


def test_analyze_maps_claude_reply_to_result():
    reply = json.dumps({"category": "TEST_DEFECT", "confidence": "high", "summary": "Selector changed",
                        "probable_cause": "Button id renamed", "suggested_action": "Update locator"})
    client = FakeClient(reply)
    case = analyzer.group_failures([_record("t::x", "failed")])

    result = analyzer.analyze(case, client)[0]

    assert result.category == "TEST_DEFECT"
    assert result.suggested_action == "Update locator"
    assert client.calls[0]["system"] == analyzer.SYSTEM_PROMPT


def test_analyze_survives_bad_model_output():
    result = analyzer.analyze(analyzer.group_failures([_record("t::x", "failed")]), FakeClient("not json"))[0]
    assert result.category == "UNKNOWN"
    assert result.error


def test_run_without_api_key_still_writes_report(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    failures = tmp_path / "failures"
    failures.mkdir()
    (failures / "failures.jsonl").write_text(json.dumps(_record("t::x", "failed")) + "\n")

    assert analyzer.run(failures_dir=failures, out_dir=tmp_path) == 0
    report = (tmp_path / "ai-triage.md").read_text()
    assert "ANTHROPIC_API_KEY not set" in report
    assert "t::x" in report


def test_run_with_no_failures_reports_clean_run(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert analyzer.run(failures_dir=tmp_path / "missing", out_dir=tmp_path) == 0
    assert "No failures" in (tmp_path / "ai-triage.md").read_text()
