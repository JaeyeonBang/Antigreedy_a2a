# TODOS

> Deferred work captured at /plan-eng-review (2026-06-13). Each item has enough
> context to pick up cold. Source: design doc `~/.gstack/projects/JaeyeonBang-Antigreedy_a2a/qkdwodus777-main-design-20260613-010056.md`.

## 1. Counterfactual replay (branch re-generation)
- **What:** Re-run a recorded episode under a CHANGED policy, re-generating the
  conversation after the first divergence (blocked/modified message).
- **Why:** Causal attribution ("this policy would have blocked message #47") and
  free A/B over recorded runs. MVP ships recorded-run replay only (deterministic
  re-render); counterfactual divergence is approximate without re-generation.
- **Pros:** Unlimited cheap experiments; strongest analysis story.
- **Cons:** Divergence semantics are deep; needs cached-LLM + live-LLM hybrid.
- **Depends on:** Replay-ready envelope (shipped in MVP), recorder, LLM cache.

## 2. Policy GAN / governance arms race
- **What:** Red-team agent generates exploit personas; blue-team generates counter
  policy `.py` files; overnight self-play with a survival leaderboard.
- **Why:** Hot-reload substrate is an evolution substrate (policies are .py; LLMs
  write .py). Nobody in GovSim-family or gateway-world has this.
- **Cons:** Cost; needs the full testbed stable first.
- **Depends on:** MVP complete (bench + probe + substrate).

## 3. Metric catalog round-out (AUROC/F1, Gini, decision quality, starvation, reputation policy)
- **What:** Restore the PRD §8 metrics descoped from MVP; add an LLM-judge for
  decision quality; implement the optional reputation policy.
- **Why:** Publication-grade evaluation breadth once episode volume justifies curves.
- **Depends on:** Bench harness + power analysis (phase 1.5 entry condition).

## 4. Structured-output upgrade for LLMBackend
- **What:** If protocol-parsing failure rates are high with cheap models, add a
  native structured-output mode (JSON schema / tool-call) to the backend contract.
- **Why:** AGREE/BID/DECISION parsing currently lives in the `protocol` module by
  design (eng decision 5/#14); revisit only if parse error rate > ~5%.
- **Depends on:** A-gate spike telemetry on parse failures.
