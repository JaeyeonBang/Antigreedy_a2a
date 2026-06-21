# Antigreedy

**A research testbed for governing selfish exploitation ("behavioral greed") in
multi-agent LLM systems.** One interception substrate hosts *heterogeneous*
governance policies — a count-based airtime quota and a content-based deception
monitor — and measures, with a real LLM, whether they actually work.

The gap it fills: research benchmarks measure greedy behavior but can't intercept
it live; enterprise agent gateways intercept live but their policy unit is
security (authn/quota/DLP), not *behavior*. Antigreedy is the middle — a
protocol-native interception layer where **the policy unit is a behavioral
hypothesis**, hot-swappable mid-experiment, with objective ground-truth probes
and fairness/detection metrics.

## Results (real LLM, claude-3.5-haiku via OpenRouter)

| Leg | Result |
|---|---|
| **A-gate** (airtime commons) | Governance flips a collapsing, unfair baseline into a fair, surviving one. Powered 10v10: baseline collapses 9/10; governed survives 10/10; delivered-Jain **0.625 → 0.908** (attempted-Jain ~unchanged → enforcement, not behavior change). **GATE PASSED.** ([docs/gate_calibration.md](docs/gate_calibration.md)) |
| **Deception probe** | A content monitor with a domain *plausibility prior* catches real-LLM under-reporting at **P 1.0 / R 0.71 / F1 0.83** (phase-1.5 gate passed). A framing-blind LLM judge scored 0 on the same data — an honest, documented negative. ([docs/probe_detection.md](docs/probe_detection.md)) |
| **Bench** | One catalog over both arms: fairness (Jain), survival, welfare (maximin airtime), cost, and detection P/R/F1. |

## The demo (A/B theater)

```bash
python -m antigreedy.dashboard      # → http://127.0.0.1:8000
```

Four controls, all over WebSocket + Cytoscape (no build step):

- **▶ Run A/B** — an ungoverned meeting collapses its token commons (one agent
  monopolizes airtime) next to a governed run that survives. Same agents, same
  seed; only the policy set differs.
- **🔴 Live** — one-touch governance: a greedy agent collapses the commons; click
  **Apply governance** and it's rescued on the very next turn (no restart). Click
  **Remove governance** and watch it collapse again.
- **🚩 Deception probe** — a probe agent secretly under-reports; the theater lights
  it up red live. (Deception is prompt-driven: the probe agent gets a secret
  "you must DECEIVE the group / under-report" instruction — click its turn row to
  read the actual prompt.)
- **Governance** toggle — add/remove governance for the next A/B run.

The dashboard UI is **Korean**, beginner-friendly (jargon glosses, a legend,
empty-state guidance), and includes:

- **거버넌스 프리셋** — pick a ready-made governance set (None / Airtime quota /
  Strict) and apply it to the governed side.
- **정책 편집기** — write a `Policy` subclass in the browser → it governs the next
  run (localhost-only; runs your pasted Python server-side).
- **에이전트 수 / 커먼즈 예산** — dial the meeting (2–8 agents, budget 400/1200/3000)
  to show collapse vs survival at different scales.
- **대화 보기** — click any turn row to see the prompt, the agent's output, and what
  governance delivered (with an original→delivered diff).
- **공정성 메트릭** — per-run Jain fairness index + per-agent airtime-share bars.
- **실험 기록** — every run is saved; re-open to replay, compare two runs side by
  side, or export a run as JSON.

Browser e2e (`tests/e2e/`, Playwright) covers all of the above — 12 cases.

## How it works

- **InterceptPoint** — one transport-agnostic interception contract. The same
  contract suite validates the in-process loop AND the real a2a-sdk executor
  wrapper, so gate results transfer to the full A2A testbed.
- **Governance substrate** — a `Policy` ABC (allow / deny / modify / delay +
  flags), a priority chain, and a hot-reload loader (drop a `.py`, governance
  applies live). Durable state lives in `SharedState`, never on the policy.
- **A2A** — the airtime meeting runs over real a2a-sdk HTTP servers; the dominator's
  airtime arrives truncated across the wire (`python -m pytest tests/test_a2a_e2e.py`).
- **Metrics are a pure function of the event log** — the gate, the bench, and the
  dashboard all read the same JSONL, so the number on screen is the number in the
  paper. Fairness is reported on BOTH attempted and delivered tokens (dual
  measurement: separates agent-behavior change from policy enforcement).

## Quickstart

```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,a2a,dashboard]"
pytest -q                                    # 197 passed, 1 skipped

# A-gate (mock = free; openrouter = real LLM, needs OPENROUTER_API_KEY)
python -m antigreedy.gate  --backend mock
# note: anthropic/claude-3.5-haiku now 404s on OpenRouter — use claude-3-haiku
python -m antigreedy.gate  --backend openrouter --model anthropic/claude-3-haiku \
  --episodes 10 --budget 4000 --max-tokens 2500

# Full bench catalog
python -m antigreedy.bench --backend mock --episodes 5

# A/B theater
python -m antigreedy.dashboard
```

## Layout

```
antigreedy/
  governance/    Policy ABC, chain, hot-reload loader, InterceptPoint, SharedState
  scenario/      airtime-commons meeting (the A/B scenario)
  probe/         deception probe: private cards, monitor, plausibility detector
  a2a_*.py       a2a-sdk adapter + meeting-over-A2A + real-HTTP transport
  dashboard/     FastAPI + WebSocket + Cytoscape A/B theater (+ live one-touch)
  gate.py        A-gate runner (baseline vs governed, Wilson CI)
  bench.py       metric-catalog harness
  metrics.py     Jain, Wilson, episode_summary, gate_report (pure)
docs/            PRD, calibration + detection findings
```

## Honest findings

Two results are kept as documented findings, not tuned away:

1. The gate's original collapse criterion AND-ed an absolute, mock-tuned fairness
   cutoff into "baseline failed"; it was redesigned into three independent criteria
   (collapse / flip / *relative* fairness gain) — a model-agnostic verdict, not a
   lowered bar. See `docs/gate_calibration.md`.
2. A card-blind LLM judge cannot detect plainly-stated number under-reporting
   (deceptive advocacy reads like honest advocacy → P/R 0). A content monitor with a
   plausibility prior can (F1 0.83). See `docs/probe_detection.md`.

## Status

Research-stage. The publishable artifact is the **A-gate + probe + bench**; the A2A
servers and dashboard are the distribution layer. [MIT licensed](LICENSE); not
affiliated with any vendor.
