# QA Automation Framework · Python + Playwright + AI Triage

![Tests](https://github.com/<your-user>/qa-automation-framework/actions/workflows/tests.yml/badge.svg)

A test automation framework for [automationexercise.com](https://automationexercise.com) that covers **UI, API and cross-layer integration** testing, runs in **CI on every push**, and uses **Claude (Anthropic) to triage failures automatically**.

## Highlights

- **UI automation** with Playwright for Python using the **Page Object Model**.
- **API testing** with `requests` plus **contract validation** with `pydantic`.
- **Integration tests** that set state through the API and verify it in the UI (and the reverse).
- **Parallel execution** (`pytest-xdist`), **retries for flaky tests** (`pytest-rerunfailures`) and **Allure** results.
- **AI failure triage**: every failed test is sent to Claude, which classifies it as a product bug, flaky test, test defect or environment problem, and suggests a next step.
- **GitHub Actions** pipeline on push, pull request and a weekday schedule.

## Project structure

```
├── ai_triage/            # AI failure triage
│   ├── collector.py      #   pytest plugin: records error, source, screenshot per failed attempt
│   └── analyzer.py       #   sends failures to Claude, writes reports/ai-triage.md
├── api/                  # API client and pydantic response schemas
├── config/               # settings (overridable with env variables)
├── pages/                # Page Objects (login, products, cart, header)
├── tests/
│   ├── api/              # API tests
│   ├── ui/               # UI tests
│   ├── integration/      # API <-> UI tests
│   └── unit/             # offline tests of the triage module
├── utils/                # test data factory
├── conftest.py           # shared fixtures
└── .github/workflows/    # CI pipeline
```

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

pytest                             # everything
pytest -m smoke                    # critical path only
pytest -m api                      # API only
pytest -m "ui" --headed            # watch the browser
pytest -n auto --reruns 1          # parallel, retry once
```

Then run the AI triage over whatever failed:

```bash
cp .env.example .env               # add your ANTHROPIC_API_KEY
python -m ai_triage                # writes reports/ai-triage.md
```

Without an API key the triage step still runs and lists the failures, just without AI analysis, so anyone can clone and run the project.

## How the AI triage works

1. **Collect.** A pytest plugin (`ai_triage/collector.py`) records, for every failed attempt, the traceback, the test's source code, the page URL and a screenshot. It works with parallel runs and retries.
2. **Detect flakiness deterministically.** If a test failed and then passed on retry, it is marked `passed_on_retry` *before* any AI is involved. The model gets that fact as evidence.
3. **Classify.** Each failure is sent to Claude (default model: Claude Haiku, for low cost) with a prompt asking for a strict JSON answer: category, confidence, summary, probable cause and suggested action.
4. **Report.** Results go to `reports/ai-triage.md` / `.json` and, in CI, to the GitHub Actions job summary.

Guardrails: triage **never fails the build** (errors degrade to a plain report), the number of calls per run is capped (`AI_TRIAGE_MAX_FAILURES`), inputs are truncated, and the report is clearly labelled as AI suggestions for a human to verify.

## CI setup

1. Push the repo to GitHub.
2. Add your key under **Settings → Secrets and variables → Actions → New repository secret**, named `ANTHROPIC_API_KEY`.
3. The workflow runs on every push and PR. Open a run and check the **Summary** tab for the AI triage table; full reports are in the `test-reports` artifact.

## Design decisions

- **Test data through the API, assertions through the UI.** Users are created with the API in a fixture and deleted afterwards. UI tests stay fast and independent, and can run in any order or in parallel.
- **Business status over transport status.** This API always returns HTTP 200 and puts the real status in the JSON body (`responseCode`). The client exposes that as `response.code`, so tests assert on what the API actually means.
- **Contracts, not just status codes.** `pydantic` models fail the test if a field disappears or changes type.
- **Third-party ads are blocked.** The demo site loads ad and consent scripts that slow it down and cause flaky failures. They are blocked at the browser-context level; it is a stability decision, not hiding product behaviour.
- **AI as an assistant, not a judge.** Flakiness is detected deterministically from retry data; Claude adds explanation and next steps on top.

## Built with AI assistance

This project was developed with Claude Code in PyCharm. `CLAUDE.md` documents the conventions the assistant follows. Every test was reviewed and run by me.

## Author

**Victor Morera** · Senior QA Engineer · [LinkedIn](https://www.linkedin.com/in/victorluismm)
