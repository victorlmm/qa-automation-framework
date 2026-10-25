"""AI-assisted failure triage.

`collector` is a pytest plugin that records rich context for every failed
attempt. `analyzer` (run with `python -m ai_triage`) sends that context to
Claude and writes a triage report classifying each failure.
"""
