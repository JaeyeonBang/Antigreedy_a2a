# Browser e2e — A/B Theater dashboard

Plan-based (PRD §12) Playwright tests that drive the **real** dashboard in a
headless browser: E1 comprehension UX, E2 in-dashboard policy editor (the live
"wow"), E3 experiment history + replay.

The Playwright config boots the dashboard itself (`python -m antigreedy.dashboard`
with the mock backend), so there is nothing to start by hand.

## Run

```bash
cd tests/e2e
npm install                 # first time only
npx playwright install chromium   # first time only (matching browser build)
npx playwright test
```

Custom port: `E2E_PORT=9001 npx playwright test`.

## Test cases

| Plan | Spec | Asserts |
|------|------|---------|
| **E1** | glossary/legend/empty-state/help | jargon glosses (commons/airtime/verdict), colour+size+bar legend, empty-state guidance, per-button "what this does" |
| **E2** | localhost warning + seeded list | the localhost-only warning shows; seeded repo policies are listed |
| **E2** | syntax error rejected | a malformed policy → error status (no write) |
| **E2** | paste → save → govern | a pasted deny-A policy is saved, listed, and **denies agent A** on the next governed A/B run; then deleted |
| **E3** | history persist + replay | a finished run appears in History; re-opening it replays the stored event log into the panels |

Requires the project venv at `../../.venv` (created per the repo CLAUDE.md).
