# Project conventions for Claude Code

Test automation framework (Python, pytest, Playwright, requests) for https://automationexercise.com.

## Commands
- Install: `pip install -r requirements.txt && playwright install chromium`
- All tests: `pytest` · by layer: `pytest -m api|ui|integration|unit|smoke`
- Parallel with retries: `pytest -n auto --reruns 1`
- AI triage after a run: `python -m ai_triage`

## Rules
- UI tests interact with the site **only through page objects** in `pages/`. No raw selectors in tests.
- Prefer `data-qa`, ids or roles for locators. Avoid XPath and nth-child chains.
- Use Playwright `expect(...)` for UI assertions (auto-waiting). Never use `time.sleep` or `wait_for_timeout`.
- API tests assert on `response.code` (business status in the body), not `http_status`.
- Validate API payloads with the pydantic models in `api/schemas.py`.
- Create test users with the `registered_user` fixture or `utils.data_factory.new_user()`; always clean up.
- Every test must be independent and safe to run in parallel.
- Every test gets a layer marker (`ui`, `api`, `integration`, `unit`); critical-path tests also get `smoke`.
- `ai_triage` must never raise: failures degrade to a plain report.
- Never commit secrets. `ANTHROPIC_API_KEY` lives in `.env` locally and in GitHub Secrets in CI.
