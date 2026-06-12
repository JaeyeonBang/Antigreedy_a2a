# Antigreedy A2A

> Project memory for Claude Code. Read this first; global rules in `~/.claude/` still apply.

## What this is

Research-stage project on **A2A (Agent-to-Agent)** with an **anti-greedy** focus.
Currently early/exploratory — research notes live in `docs/`. Stack: **Python**.

> Fill in the one-line problem statement and goal once scope is fixed:
> - Problem:
> - Goal:
> - Non-goals:

## Layout

```
docs/        research notes (research_1.md = scratch)
```

(Add `src/`, `tests/`, `pyproject.toml` as the project takes shape.)

## Conventions

- **Python 3** (system: 3.8.10). Use a `.venv` per project; never install globally.
- **Secrets** in env vars only — `.env` is gitignored, commit a `.env.example` instead.
- **TDD**: tests first, 80%+ coverage (see global golden-principles).
- **Small files/functions**: ≤800 lines/file, ≤50 lines/function.
- **Conventional commits**: `feat|fix|refactor|docs|test|chore`.

## Tooling available (global skills — no per-project install)

- **gstack** (`/gstack`, v1.57.10.0) — headless browser QA, design, ship, review, security (`/cso`), and more.
- **graphify** (`/graphify`) — turn any input (code, docs, papers) into a clustered knowledge graph + HTML/JSON report. Useful for mapping the A2A research corpus in `docs/`.
- **RTK** — token-optimized CLI proxy (auto-applied via hook).

## Verification (non-negotiable)

No completion claims without fresh evidence. Run the command, read the output, then report.
For features touching 3+ files / architecture / API / schema: `/plan` first, no code before plan approval.
