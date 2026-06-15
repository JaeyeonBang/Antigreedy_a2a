# Antigreedy A2A — PRD (Product Requirements Document)

> Status: **DRAFT v0.1** · Date: 2026-06-13 · Source research: [`research_1.md`](research_1.md)
> This is a problem-first PRD. It defines *what* and *why*, not *how*. Architecture
> and file-level breakdown come later in `/plan` (only after this PRD is approved).

---

## 1. Problem

Multi-agent LLM systems exhibit **selfish exploitation** — behavioral/strategic
"greedy": an agent maximizes its own utility at the collective's expense. Per
`research_1.md`, this is a spectrum (a→g): overt self-interest → emergent defection
→ strategic deception → LLM-to-LLM scheming → broken promises → secret collusion.

Current defenses (CoT monitoring, reputation, institutional sanctions, social
norms) each leave **structural gaps** (agent-native identity, AI-AI safety,
system-level misalignment auditing). And critically: **there is no easy sandbox**
to reproduce these behaviors, plug in defenses, and *see/measure* whether they work.

## 2. Goal

A **local experiment testbed** where a researcher can:

1. Spin up **N real LLM agents** connected over the **A2A protocol**,
2. Run a **scenario** that creates incentive for greedy/selfish behavior,
3. Plug in **hot-reloadable governance policies** (detection + intervention) and
   observe the effect **immediately**,
4. **Visualize** agent conversations/state/history as a **live graph** and
   **measure** cooperation vs greed.

### Non-goals
- Not a production governance system — a research sandbox.
- Not training/fine-tuning — behavior comes from prompting real LLMs.
- Not solving the open research gaps — just making them *testable*.
- (MVP) Not distributed/multi-machine — single host.

## 3. User & primary use case

- **Primary user**: the researcher preparing analysis / a presentation on
  selfish-exploitation governance.
- **Core loop of use**: "Run scenario X with policy set Y → watch the graph →
  read the metrics → swap/edit policy Y→Z live → compare the delta."

## 4. Core concept — the experiment loop

```
Scenario  →  spawns LLM agents (A2A)  →  agents take turns / actions
          →  every action passes the GOVERNANCE policy chain  (allow / deny / modify / flag)
          →  accepted actions update shared world STATE  (commons, reputation, payoff)
          →  all events stream to the DASHBOARD  (graph + timeline + metrics)
          →  researcher edits/adds a policy file  →  chain updates LIVE  →  observe delta
```

## 5. MVP scenario — the "commons" framing

The shared **token/compute budget is the commons** of a multi-agent "meeting".
**Greedy = an agent monopolizing airtime** (long turns / too many turns) → depletes
the shared budget before the group reaches a good decision → **commons tragedy**
(the "one person talks too much in a meeting" failure).

This is the *shallow* (overt/emergent) end of the research spectrum; the same
substrate **extends to deeper deception** later by adding hidden private payoffs.

- **Metrics**: Jain airtime-fairness index, budget-exhausted-before-done rate,
  per-agent airtime share, starvation, (later) decision quality.

## 6. Functional requirements

| ID | Requirement | Maps to user ask |
|----|-------------|------------------|
| **FR1** | **Agent network (A2A)**: programmatically spawn N real-LLM agents, each an A2A server; discover via a registry; exchange messages per scenario; capture every message. | ① 네트워크 |
| **FR2** | **Scenario engine**: pluggable scenarios; a scenario defines roles/personas, the shared resource, what counts as greedy, termination, metrics. MVP = airtime-commons meeting. | (substrate) |
| **FR3** | **Governance policy framework** *(build first)*: a `Policy` interface that intercepts each agent action → allow/deny/modify/delay + non-blocking **flags** (detection) + dashboard **events**; a **PolicyChain** by priority; a **hot-reload loader** (drop/edit `policies/*.py` → live, no restart); shared state lives outside policies so reloads keep bookkeeping. | ③ 즉시 반영 정책 |
| **FR4** | **Dashboard**: live graph (agents=nodes colored by state/cooperate/defect/flagged, messages=edges), per-agent timeline + state, policy block/flag highlighted, metrics panel. | ② 대시보드 |
| **FR5** | **Reproducibility**: config-driven runs; JSONL event logs saved under `runs/`. | (support) |

## 7. MVP scope

**In (first cut):**
- FR3 governance framework + hot-reload — built & tested standalone first.
- FR2 one scenario: airtime-commons meeting **+ one deception probe** (one agent
  secretly instructed to deceive/over-claim) → provides ground-truth labels for
  detection metrics.
- 2–3 policies: airtime-quota (intervention) + an **LLM deception/greed monitor**
  (detection, flags only) + optional reputation.
- FR1 real LLM agents over A2A via **OpenRouter**, small N (3–4), with a **mock
  backend** for cost-free plumbing tests.
- FR4 basic dashboard: live graph + metrics.

**Later:** deeper-greedy scenarios (deception/scheming/collusion); more policies
(institutional sanction, reputation+punishment, LLM deception-monitor,
universalization nudge); richer dashboard, run replay & comparison.

## 8. Evaluation, metrics & benchmarking

**How we measure whether governance works** = a **controlled A/B comparison** on
the same scenario + fixed agent/persona config, varying *only* the policy set
(including a **"no-governance" baseline**). LLM nondeterminism is handled by low
temperature + **M trials per condition**, reported as mean ± std.

**Metric catalog**
- *Greed / fairness*: Jain airtime-fairness index, Gini of airtime, per-agent
  share, **commons survival** (did the shared budget last until a decision?),
  starvation rate.
- *Welfare*: social welfare (utilitarian Σ, Nash Π), defection rate.
- *Detection quality* (for detection policies): **precision / recall / F1 / AUROC**
  against **ground truth** — we *know* which agent was instructed to be the
  greedy/deceptive probe, so every flag is labelable (mirrors research §3-1
  monitor metrics, e.g. pAUROC).
- *Decision quality*: did the meeting reach a good joint outcome? (task rubric or
  LLM-judge).
- *System / cost*: tokens & $ per run (OpenRouter usage), wall-clock, rounds.

**Benchmark harness**: a `bench` command runs `M trials × {policy sets}` on a
scenario, aggregates the metric catalog into a CSV/table, and reports **deltas vs
baseline** — so comparisons are statistical, not vibes (GovSim's survival-rate is
the model). All runs persist JSONL under `runs/` for offline re-analysis.

**Success criteria (MVP)**
1. One command runs a scenario and opens the dashboard.
2. No-governance baseline: the greedy/deceptive agent visibly dominates (low Jain
   fairness / commons exhausted / deception undetected) — shown live + in metrics.
3. Enabling policies improves the metrics by a **measured, reported delta**.
4. The deception monitor's **precision/recall is reported** against the probe's ground truth.
5. Editing a policy changes behavior with **no restart**; all governance logic tested.

## 9. Key decisions & open questions

**Decided:**
- **LLM backend = OpenRouter** — one API key → any model, with built-in usage/cost
  tracking. Behind an adapter so the model is swappable; runs are **cost-bounded**
  (max rounds, hard token cap). Needs `OPENROUTER_API_KEY`.
- **MVP depth**: shallow airtime-greed **+ one deception probe** (an agent secretly
  instructed to deceive) → yields ground-truth labels for detection metrics.
- **Dashboard**: FastAPI + WebSocket + Cytoscape.js.
- **N agents** = 3–4 for MVP.
- **Build order**: governance framework → scenario+agents (mock → real LLM via
  OpenRouter) → dashboard. Python 3.11 venv; A2A via `a2a-sdk` v1.x.

**Open:**
- Default OpenRouter model for MVP + per-run $ ceiling? *(recommend a cheap, fast
  model first, e.g. `anthropic/claude-3.5-haiku` or an inexpensive open model)*

## 10. Risks

- **LLM API cost** → mitigate with mock backend for plumbing + hard-bounded runs.
- **A2A SDK churn** (recent 0.3→1.0 breaking change) → pin version, isolate behind an adapter.
- **Over-scoping** → keep MVP to one scenario + a few policies.

---

## 11. Status — MVP SHIPPED (2026-06-15)

All MVP legs are built, tested, and pushed (`origin/main`). Real-LLM evidence:
- **A-gate**: governance flips a collapsing/unfair baseline → fair/surviving.
  Powered 10v10 (claude-3.5-haiku): baseline collapses 9/10, governed survives
  10/10, delivered-Jain 0.625→0.908. **GATE PASSED** (`docs/gate_calibration.md`).
- **Deception probe**: a card-blind plausibility-prior monitor catches real-LLM
  under-reporting at **P 1.0 / R 0.71 / F1 0.83** (`docs/probe_detection.md`).
- **Bench**: one catalog (fairness/survival/welfare/cost/detection).
- **A2A**: meeting runs over real a2a-sdk HTTP; truncation verified over the wire.
- **Dashboard**: FastAPI+WS+Cytoscape A/B theater — Run A/B, 🔴 Live one-touch
  govern, 🚩 Deception probe, Governance toggle. 114 tests / ~98% cov.

## 12. v0.2 candidates — for CEO/eng review

Three asks surfaced while demoing the dashboard; gather feedback before building.

- **E1 — Beginner-friendly dashboard UX.** A first-time viewer should use every
  feature without reading docs. Inline explainers for the jargon (**commons** =
  the shared token budget the agents draw from; **airtime** = how much an agent
  speaks; **verdict** allow/modify/deny = what governance did), a node/gauge
  **legend**, empty-state guidance ("Press ▶ Run A/B to start"), and per-button
  one-line "what this does". UX-writing pass, no new backend.

- **E2 — In-dashboard policy editor (the evolution-substrate demo).** Write/paste
  a `Policy` subclass in the UI → server writes it into a live (non-frozen) policy
  dir → hot-reload picks it up → it governs the next/live run. Makes the thesis
  ("policies are `.py`; the hot-reload substrate is an evolution substrate, LLMs
  can author policies") tangible. **Security**: executes user-provided Python
  server-side → LOCAL single-user only; gate behind a localhost-only flag and a
  clear warning; never expose publicly. Builds on the existing PolicyLoader hot-reload.

- **E3 — Experiment history.** Persist each run's report + config and let the user
  list / re-open / compare past experiments. Foundation already exists: every run
  writes JSONL under `runs/` and gate/bench write `*-report.json`. Add an index
  (run id, scenario, policy set hash, key metrics, timestamp) + a history view in
  the dashboard, and a diff between two runs. Turns one-shot demos into a logbook.

**Review goal**: validate E1–E3 priority/scope and surface any higher-leverage
feature (e.g., policy GAN red-team/blue-team loop, decision-quality LLM-judge,
multi-scenario library, shareable run permalinks) before committing build effort.

### CEO review decision (2026-06-16, /plan-ceo-review, SELECTIVE EXPANSION)

**Goal clarified: a PPT presentation/demo, NOT a paper.** That reweights everything.

- **ACCEPTED — build all three: E1 + E3 + E2.** For a live talk, E2 (author a policy
  on-screen → hot-reload → agent behavior changes instantly) is the "wow" moment that
  lands the thesis; E1 makes the live demo self-explanatory; E3 shows reproducibility.
- **E2 security**: presenter's own machine → user-Python exec is acceptable. STILL gate
  it localhost-only with a clear warning so it's never exposed publicly.
- **DEFERRED (paper-leverage, not needed for a PPT)**: multi-model matrix,
  decision-quality LLM-judge, policy GAN loop → TODOS.md.
- **Sequencing for the demo**: E1 (audience can follow) → E2 (the live wow) → E3
  (reproducibility). Static run-export is optional polish (slide screenshots suffice).

### v0.2 status — E1+E2+E3 SHIPPED (2026-06-16)

All three demo features are built, tested, and pushed (`origin/main`). 131 tests
/ 1 skipped, all dashboard legs live-verified over real HTTP+WS.

- **E1 — beginner-friendly UX** (`theater.html`): jargon glosses (commons =
  shared token budget; airtime = how much an agent speaks; verdict allow/modify/
  deny), a colour/size/bar legend, empty-state guidance, and per-button "what
  this does" lines. Pure UX pass — the WS contract/JS logic is unchanged.
- **E2 — in-dashboard policy editor** (the live wow): paste a `Policy` subclass
  → `POST /policies` writes it into a per-app editor dir (a writable copy of the
  repo set) → the next governed run obeys it. Localhost-only gate + filename
  validation + compile-check before write. Verified: a pasted deny-A policy
  muted agent A across all 16 governed turns.
- **E3 — experiment history**: every run persisted (config + full event log)
  under `runs/`; `GET /history` lists past runs, `GET /history/{id}` returns the
  replayable log; the History panel re-opens a run by re-feeding events through
  the same renderer. Survives server restart.

### v0.2 follow-up — conversation visibility + governance presets (2026-06-16)

Two PRD requirements that the first v0.2 pass had not reflected, now shipped:

- **Conversation visibility (PRD §2 "visualize conversations", §6 FR4).** Turn
  events were token-counts only — the actual text was invisible. Turn events now
  carry the prompt the agent saw, its original output, and the delivered text
  (capped). Each dashboard feed row is clickable → expands to PROMPT / AGENT
  OUTPUT / DELIVERED with an original→delivered diff, so you can see exactly what
  a greedy agent tried to say and what the policy let through. (meeting + probe.)
- **Named governance presets (PRD §4 "swap policy Y→Z live").** Only a toggle +
  editor existed. A header dropdown now offers None / Airtime quota / Strict
  quota; selecting one applies it to the governed side (`/presets`,
  `/presets/{name}/apply`). Browser e2e covers both (7/7).
