# Agents & Automation

## Purpose

Automated agents run tests, scrape data and serve the UI. They must respect external rate limits, avoid PII, and leave the repository in a clean state.

## Agent Roster

| Agent | Role | Inputs | Outputs | Tools |
|---|---|---|---|---|
| scraper | gather rarity metrics | limit, dry_run, output_dir | CSV, logs | pokemon_rarity_cli, http_request |
| tester | execute unit tests | none | pass/fail report | pytest |
| linter | check markdown | file paths | warnings | markdownlint_cli |
| ui | serve Streamlit | port | running web app | streamlit_run |

## Tool Contracts

```json
{
  "name": "pokemon_rarity_cli",
  "input_schema": {"limit": "int?", "dry_run": "bool", "output_dir": "string?"},
  "errors": ["EHTTP", "EIO"],
  "timeout_sec": 600,
  "side_effects": ["network", "filesystem"]
}
```

```json
{
  "name": "pytest",
  "input_schema": {"tests": "string?"},
  "errors": ["EIMPORT", "EASSERT"],
  "timeout_sec": 300,
  "side_effects": []
}
```

```json
{
  "name": "markdownlint_cli",
  "input_schema": {"paths": "[string]"},
  "errors": ["ELINT"],
  "timeout_sec": 60,
  "side_effects": []
}
```

```json
{
  "name": "streamlit_run",
  "input_schema": {"file": "string", "port": "int"},
  "errors": ["EADDRINUSE"],
  "timeout_sec": 60,
  "side_effects": ["network"]
}
```

## Prompt Contracts

### System Prompt (scraper)

- Be courteous: wait `1s` between outbound requests.
- Abort on repeated `403` or `429` responses.
- Log all request metadata.

### Task Prompt Template

```text
Run `pokemon-rarity --limit {{limit}} --dry-run{{#if output_dir}} --output-dir {{output_dir}}{{/if}}` and return the resulting CSV path or error.
```

### Few-shot Example

```text
Input: limit=5
Output: `/workspace/pokemon_rarity_analysis_enhanced.csv`
```

## Memory / RAG

- Index files under `data/` and generated CSVs.
- Chunk size: 2KB.
- Metadata: file path, data source, timestamp.
- Remove cached data older than 30 days and redact any tokens.

## Orchestration & Handoffs

- `tester` runs before `scraper` to ensure code health.
- `scraper` writes CSV then notifies `ui` to restart.
- On failure, agents retry up to 3 times with exponential backoff.
- All tools must be idempotent; include a run ID in temp files.

## Safety

- Never store or echo PII.
- Do not commit secrets; use environment variables for tokens.
- Escalate to a human if external services return unexpected content.

## Evaluation

- Regression suite: `pytest` must pass.
- Smoke test: `pokemon-rarity --limit 1 --dry-run` completes in <2 min.
- Success metrics: scrape completion rate, test pass rate, mean latency.

## Ops Runbook

- **Deploy prompts/tools**: update `AGENTS.md` and merge to `main`.
- **Rotate keys**: replace environment variables and restart agents.
- **Logging**: inspect `pogorarity/pogo_debug.log` and Streamlit console.
- **Dashboards**: TODO add metrics dashboard.
- **Incidents**: capture logs, revert to last known good commit, notify maintainers.

Refer to [README.md](README.md) for project overview and manual commands.
