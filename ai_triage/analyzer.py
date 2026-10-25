"""Send recorded failures to Claude and write a triage report.

Design rules:
- Triage must never break the build: missing key, API errors or bad JSON all
  degrade to a plain report instead of an exception.
- Cost is bounded: at most AI_TRIAGE_MAX_FAILURES calls per run, small model
  by default, truncated inputs.
- Claude classifies; humans decide. The report is advice, not a verdict.
"""
from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CATEGORIES = ("PRODUCT_BUG", "FLAKY_TEST", "TEST_DEFECT", "ENVIRONMENT", "UNKNOWN")

DEFAULT_MODEL = os.getenv("AI_TRIAGE_MODEL", "claude-haiku-5-5")
MAX_FAILURES = int(os.getenv("AI_TRIAGE_MAX_FAILURES", "15"))
INCLUDE_SCREENSHOTS = os.getenv("AI_TRIAGE_SCREENSHOTS", "true").lower() == "true"

SYSTEM_PROMPT = f"""You are a senior QA engineer triaging automated test failures.
The suite tests https://automationexercise.com (UI with Playwright, API with requests).

Classify each failure into exactly one category:
- PRODUCT_BUG: the application behaves incorrectly (wrong data, broken feature).
- FLAKY_TEST: timing/race/intermittent issue; strong signal if it passed on retry.
- TEST_DEFECT: the test itself is wrong (bad selector, outdated expectation, bad data).
- ENVIRONMENT: network, site down, rate limiting, CI/browser setup problems.
- UNKNOWN: not enough evidence.

Be concrete and brief. Do not invent facts that are not in the evidence.
Reply with ONLY a JSON object with these keys:
"category" (one of {", ".join(CATEGORIES)}), "confidence" ("low"|"medium"|"high"),
"summary" (one sentence), "probable_cause" (1-2 sentences), "suggested_action" (1-2 sentences)."""


@dataclass
class FailureCase:
    nodeid: str
    final_status: str  # "failed" or "passed_on_retry"
    attempts: list[dict[str, Any]] = field(default_factory=list)

    @property
    def last(self) -> dict[str, Any]:
        return self.attempts[-1]


@dataclass
class TriageResult:
    nodeid: str
    final_status: str
    category: str = "UNKNOWN"
    confidence: str = "low"
    summary: str = ""
    probable_cause: str = ""
    suggested_action: str = ""
    error: str | None = None


# ---------------------------------------------------------------- loading

def load_records(failures_dir: Path) -> list[dict[str, Any]]:
    path = failures_dir / "failures.jsonl"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def group_failures(records: list[dict[str, Any]]) -> list[FailureCase]:
    """Group attempts per test. If no attempt ended as 'failed', every
    recorded attempt was retried and the test eventually passed: flaky."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(record["nodeid"], []).append(record)
    cases = []
    for nodeid, attempts in grouped.items():
        attempts.sort(key=lambda r: r.get("attempt", 1))
        final = "failed" if any(a["outcome"] == "failed" for a in attempts) else "passed_on_retry"
        cases.append(FailureCase(nodeid=nodeid, final_status=final, attempts=attempts))
    # Real failures first: they matter more if we hit the call limit.
    cases.sort(key=lambda c: (c.final_status != "failed", c.nodeid))
    return cases


# ---------------------------------------------------------------- prompting

def build_message_content(case: FailureCase) -> list[dict[str, Any]]:
    last = case.last
    evidence = (
        f"Test: {case.nodeid}\n"
        f"Final status: {case.final_status} after {len(case.attempts)} failed attempt(s)\n"
        f"Markers: {', '.join(last.get('markers', [])) or 'none'}\n"
        f"Page URL at failure: {last.get('page_url') or 'n/a'}\n"
        f"Duration: {last.get('duration_s')}s\n\n"
        f"--- Test source ---\n{last.get('test_source', '')}\n\n"
        f"--- Error / traceback (last attempt) ---\n{last.get('error', '')}"
    )
    content: list[dict[str, Any]] = [{"type": "text", "text": evidence}]

    screenshot = last.get("screenshot")
    if INCLUDE_SCREENSHOTS and screenshot and Path(screenshot).exists():
        data = base64.standard_b64encode(Path(screenshot).read_bytes()).decode()
        content.insert(0, {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}})
    return content


def parse_response(text: str) -> dict[str, Any]:
    """Extract the JSON object even if the model wrapped it in prose or fences."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("no JSON object in response")
    data = json.loads(match.group(0))
    if data.get("category") not in CATEGORIES:
        data["category"] = "UNKNOWN"
    return data


# ---------------------------------------------------------------- analysis

def analyze(cases: list[FailureCase], client: Any, model: str = DEFAULT_MODEL) -> list[TriageResult]:
    results = []
    for case in cases[:MAX_FAILURES]:
        result = TriageResult(nodeid=case.nodeid, final_status=case.final_status)
        try:
            response = client.messages.create(
                model=model,
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": build_message_content(case)}],
            )
            text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
            data = parse_response(text)
            for key in ("category", "confidence", "summary", "probable_cause", "suggested_action"):
                if key in data:
                    setattr(result, key, str(data[key]))
        except Exception as exc:  # degrade gracefully, never fail the pipeline
            result.error = f"{type(exc).__name__}: {exc}"
        results.append(result)
    return results


# ---------------------------------------------------------------- reporting

def render_markdown(results: list[TriageResult], skipped: int = 0, note: str | None = None) -> str:
    lines = ["## 🤖 AI failure triage (Claude)", ""]
    if note:
        lines += [f"> {note}", ""]
    if not results:
        lines.append("No failures to triage. ✅")
        return "\n".join(lines) + "\n"

    counts: dict[str, int] = {}
    for r in results:
        counts[r.category] = counts.get(r.category, 0) + 1
    lines.append("**Summary:** " + " · ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    lines += ["", "| Test | Final status | Category | Confidence | Summary |", "|---|---|---|---|---|"]
    for r in results:
        summary = (r.summary or r.error or "").replace("|", "\\|")
        lines.append(f"| `{r.nodeid}` | {r.final_status} | {r.category} | {r.confidence} | {summary} |")

    lines += ["", "### Details", ""]
    for r in results:
        lines.append(f"**`{r.nodeid}`** — {r.category} ({r.confidence})")
        if r.error:
            lines.append(f"- ⚠️ Triage error: {r.error}")
        if r.probable_cause:
            lines.append(f"- Probable cause: {r.probable_cause}")
        if r.suggested_action:
            lines.append(f"- Suggested action: {r.suggested_action}")
        lines.append("")
    if skipped:
        lines.append(f"_{skipped} more failure(s) not analyzed (limit AI_TRIAGE_MAX_FAILURES={MAX_FAILURES})._")
    lines.append("_AI-generated suggestions. Verify before acting._")
    return "\n".join(lines) + "\n"


def write_reports(markdown: str, results: list[TriageResult], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ai-triage.md").write_text(markdown, encoding="utf-8")
    (out_dir / "ai-triage.json").write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as fh:
            fh.write(markdown)


def run(failures_dir: Path = Path("reports/failures"), out_dir: Path = Path("reports"), client: Any = None) -> int:
    cases = group_failures(load_records(failures_dir))
    if not cases:
        write_reports(render_markdown([]), [], out_dir)
        print("AI triage: no failures recorded.")
        return 0

    if client is None:
        if not os.getenv("ANTHROPIC_API_KEY"):
            note = "ANTHROPIC_API_KEY not set: failures listed without AI analysis."
            results = [TriageResult(nodeid=c.nodeid, final_status=c.final_status) for c in cases]
            write_reports(render_markdown(results, note=note), results, out_dir)
            print(f"AI triage skipped: {note}")
            return 0
        from anthropic import Anthropic

        client = Anthropic()

    results = analyze(cases, client)
    skipped = max(0, len(cases) - MAX_FAILURES)
    write_reports(render_markdown(results, skipped=skipped), results, out_dir)
    print(f"AI triage: analyzed {len(results)} failure(s). Report: {out_dir / 'ai-triage.md'}")
    return 0
