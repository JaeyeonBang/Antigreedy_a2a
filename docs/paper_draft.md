# Input Framing Beats Output Capping: Governing Behavioral Greed in Agent-to-Agent Systems

*행동적 탐욕의 거버넌스 — A2A 시스템에서 출력 강제(cap)보다 입력 프레이밍이 우월하다*

**Status:** working draft (academic-pipeline Stage 2). All headline numbers are this paper's own
measurements on a real LLM with multi-seed 95% CIs; see §4–5 and `docs/verify_results.md`.

---

## Abstract

Large-language-model agents increasingly communicate, negotiate, and compete over shared resources
through Agent-to-Agent (A2A) protocols, reviving classic social dilemmas: a single agent maximizing
its own utility can monopolize a commons and starve the group. We ask a governance question that the
multi-agent-safety literature poses but rarely tests head-to-head: *should we govern greed by capping
an agent's output (enforcement) or by reshaping its input (framing)?* We build a reusable governance
substrate for A2A — a single `InterceptPoint` contract, a single-writer shared state, and a priority-
ordered `PolicyChain` — that lets us apply, on the *same* scenario, two orthogonal levers: **output
policies** that truncate/deny an agent's request at delivery time, and **input shapers** that rewrite
the agent's prompt before it acts (superordinate-identity framing, accountability cues, and a
reputation-feedback channel). On a shared-resource task where greed emerges from a self-interested
persona on a real model (GLM-4.6), we measure monopoly (top-share), welfare (task completion), and a
two-channel fairness pair (attempted vs. delivered Jain) across multi-seed runs with 95% confidence
intervals and two-sample tests. Three findings, two of which **correct our own earlier single-run
claims**: (1) output caps reduce monopoly but at a *welfare cost*, and a "social" reputation+ostracism
policy is statistically indistinguishable from a dumb proportional cap on fairness (p=.23) — confirming
a skeptical reviewer's "relabeled rate-limiter" critique; (2) a superordinate-identity prompt cuts
monopoly (top-share 0.64→0.36, p<.001) while keeping welfare neutral-to-positive — its apparent
fairness/throughput tradeoff was a short-horizon artifact; (3) a reputation-feedback channel that
merely *shows an agent its standing* (no output cap) significantly improves both welfare (0.61→0.79,
p=.027) and monopoly (0.72→0.52, p=.019). The verified thesis inverts the intuition that built our own
system: **input-side behavioral framing dominates output-side capping** because it moves the *attempted*
(behavioral) channel rather than merely enforcing on the delivered one. We release the substrate, the
adversarial cap-null ablation, and a self-correcting N=1→N≥20 methodology trail.

**초록 (요약).** A2A로 자원을 다투는 LLM 에이전트에서 탐욕(공유지 독점→starvation)을 다스리는 두
계층 — 출력 강제(cap) vs 입력 프레이밍 — 을 동일 시나리오에서 정면 비교했다. 실 GLM-4.6·다중 시드·
95% CI 측정 결과, 출력 캡은 독점은 줄이나 welfare를 희생하고 사회 정책은 더미 캡과 공정성에서 구분
되지 않았다(p=.23). 반면 입력측 평판 되먹임은 출력 cap 없이 welfare(0.61→0.79, p=.027)와 독점
(0.72→0.52, p=.019)을 동시에 유의하게 개선했다. **입력 프레이밍이 출력 캡보다 우월하다** — 시도(행동)
채널을 직접 바꾸기 때문.

---

## 1. Introduction

Autonomous LLM agents no longer act alone. In software pipelines, market simulations, and tool-using
swarms, many agents cooperate and compete through emerging A2A protocols. When each agent optimizes its
own reward, the social dilemmas humans have long studied reappear — most sharply the *tragedy of the
commons*, where individually rational consumption depletes a shared resource and harms everyone
[Hammond et al. 2025; Piatti et al. 2024]. We call the behavioral version of this problem *behavioral
greed* (selfish exploitation): strategically maximizing own utility at the group's expense, distinct
from algorithmic greedy search or mere resource hogging [Vallinder & Hughes 2025].

The defense literature splits into **external enforcement** (rate limits, fair queuing, mechanism
design, detection/monitoring) and **social mechanisms** (reputation, norms, identity, reciprocity)
[review in §2]. These map onto two architecturally distinct intervention points that are almost never
compared on equal footing: governing an agent's **output** (cap or deny what it delivers) versus
reshaping its **input** (change the prompt so it *chooses* differently). This paper builds an A2A
testbed that applies both levers to the same scenario and asks which actually governs greed — and at
what cost to welfare.

**Contributions.**
1. **A reusable A2A governance substrate** (§3): one `InterceptPoint` contract, single-writer shared
   state, priority-ordered `PolicyChain` with hot-reload — cleanly separating *output policies* from
   *input shapers*.
2. **A head-to-head, multi-seed evaluation** (§4–5) on a real model where greed *emerges* (not scripted),
   reporting welfare and a two-channel (attempted/delivered) fairness pair with 95% CIs.
3. **A verified, counter-intuitive result** (§5–6): input framing beats output capping; output caps
   trade welfare for fairness; "social" output policies ≈ a dumb cap on fairness.
4. **A self-correcting methodology trail** (§5.4): two of our own earlier single-run headline claims
   did not survive multi-seed verification, which we report transparently as evidence for why
   single-seed LLM numbers must not be trusted.

---

## 2. Related Work

**The greed spectrum.** Selfish exploitation runs from overt self-interest (prompted personas) through
emergent defection under survival pressure, strategic deception, LLM-to-LLM scheming, cheap-talk
promise-breaking, and steganographic secret collusion [Vallinder & Hughes 2025; "Survival at Any Cost?"
2025; Scheming in LLM-to-LLM 2025; Secret Collusion, NeurIPS 2024]. Infrastructure defenses largely
stop the overt end; the covert end is open.

**Risks & defenses.** Hammond et al. [2025] taxonomize multi-agent risks (miscoordination, conflict,
collusion). GovSim [Piatti et al. 2024] shows most LLMs fail at sustainable commons use, attributing
failure to an inability to simulate the long-term group effect of one's actions, and that removing
communication raises over-consumption ~22%. "Corrupted by Reasoning" [2025] reports stronger reasoners
free-ride *more*. A2A specifications address abuse via rate limiting, concurrency control, and fair
queuing — but, as a skeptical reading notes, "protocols stop the flood, not the tragedy."

**Social mechanisms.** Indirect reciprocity and gossip-based reputation solve commons dilemmas in humans
[Milinski et al. 2002]; costly punishment and low-cost ostracism sustain cooperation [Fehr & Gächter
2000]; superordinate goals defuse intergroup conflict (Robbers Cave); accountability/audience effects
raise prosociality. Recent work ports these to agents [ALIGN 2026; Vallinder & Hughes 2024] and warns
the same levers can backfire (out-grouping humans, conformity/groupthink, false consensus). Our prior
internal review consolidated these into governance proposals; this paper *tests* them and finds the
output-side implementations weaker than expected.

**Gap we target.** The literature proposes social governance but rarely (a) implements it as a
runtime, public-observable mechanism, (b) compares it against a *null* (dumb cap) to see if the
"social" part adds anything, or (c) separates the *behavioral* (input) lever from the *enforcement*
(output) lever. We do all three.

---

## 3. Governance Substrate

**Contract.** Every agent action passes through one `InterceptPoint.submit(action) → verdict` before
delivery. A `verdict ∈ {ALLOW, DENY, MODIFY, DELAY}`. A `PolicyChain` evaluates policies in priority
order; `DENY/DELAY` short-circuit, `MODIFY` propagates the rewritten payload to the next policy
(verified to double-cut correctly), and flags/events accumulate for detection without blocking.

**Single-writer rule.** All mutable world state (the commons budget, per-agent attempted/delivered
tallies, a turn log, derived reputation) lives in one `SharedState`; only the episode orchestrator
mutates it. Policies and shapers read it **read-only**, so hot-reload never drops bookkeeping and
mechanisms cannot covertly rewrite history.

**Two orthogonal levers.**
- **Output policies** intercept the *delivered* action: a proportional `FractionCapPolicy` (dumb cap =
  `k·remaining`), a count-based `AirtimeQuotaPolicy`, and "social" policies (reputation-gossip,
  ostracism) that derive reputation read-only from the turn log and truncate/deny accordingly.
- **Input shapers** rewrite the *prompt* before the backend is called, targeting the **attempted**
  (behavioral) channel: `superordinate_identity` (ONE-TEAM common goal), `accountability` (audience +
  justification), and `reputation_feedback` (show the agent its own standing — closing the loop that a
  gossip policy only *broadcasts*).

Because both levers run on the same scenario and state, we can isolate "does the social policy beat a
dumb cap?" and "does framing change behavior with *no* cap at all?"

---

## 4. Experimental Setup

**Scenario (resource-task).** N agents each hold a subtask needing `workload` compute units drawn from
a shared rate-limited pool (the commons). Each round an agent issues `REQUEST: <n>`; the intercept
governs it; granted units advance the subtask and deplete the pool. Greed = hogging the pool to finish
first, starving others. Greed **emerges**: a self-interested persona ("you get a bonus for finishing
first") on a real model produces pool monopolization with no scripted hog.

**Model & sampling.** GLM-4.6 via OpenRouter, temperature 0.7 for independent draws. 3 agents,
pool=360, workload=120. Each condition is run for N∈[15,24] seeds; we report means with 95% CIs
(Wilson for proportions, normal-approx for continuous) and **two-sample z-tests** on mean differences
(the CI-overlap heuristic is too conservative). Mock (deterministic) backends are used only for
plumbing/regression, never for headline numbers.

**Metrics.** *top-share* = max single-agent share of granted resources (1.0 = full monopoly; the greed
metric). *welfare* = task completion rate (fraction of agents finishing; the primary outcome). *Jain
attempted vs. delivered* = fairness of requests vs. grants — separating behavior change from
enforcement. Reporting welfare and *attempted* fairness, with *delivered* Jain demoted to an
"is enforcement binding?" diagnostic, follows a methodological critique that `delivered`-only metrics
circularly grade the policy's own output.

---

## 5. Results

### 5.1 Output caps trade welfare for fairness; social ≈ dumb cap (V4)

| arm (output-side, N=20, r=8) | welfare [95% CI] | top-share [95% CI] |
|---|---|---|
| none | **0.65** [0.52, 0.78] | 0.675 [0.544, 0.806] |
| dumb cap (k=0.22) | 0.50 [0.41, 0.59] | 0.408 [0.388, 0.427] |
| social (reputation+ostracism) | 0.40 [0.26, 0.54] | 0.429 [0.401, 0.458] |

Both caps cut monopoly (none→social top-share, z=−3.6, p=.0003) but **reduce welfare** relative to no
governance (social vs none welfare, z=2.56, p=.010). Critically, the social policy is **indistinguishable
from the dumb cap on fairness** (top-share 0.429 vs 0.408, z=1.19, p=.23): on the fairness axis, the
"social" machinery adds nothing beyond the arithmetic — confirming the "relabeled rate-limiter"
critique. (Config caveat in §7.)

### 5.2 Superordinate identity: monopoly down, welfare not hurt (V5)

| rounds | baseline welfare | superordinate welfare | baseline top | superordinate top |
|---|---|---|---|---|
| 4 | 0.64 | 0.58 | 0.545 | 0.524 |
| 6 | 0.62 | 0.71 | 0.656 | 0.439 |
| 8 | 0.67 [0.50,0.84] | **0.78** [0.70,0.86] | 0.644 [0.482,0.807] | **0.364** [0.346,0.382] |

At an adequate horizon (r=8) the ONE-TEAM frame cuts monopoly hard (top-share 0.644→0.364, z=−3.36,
p=.0008) while welfare is neutral-to-positive (0.67→0.78, z=1.15, p=.25). The effect is *horizon-
dependent*: early on, "leave enough for others" costs throughput; over more rounds the preserved pool
lets everyone finish.

### 5.3 Reputation feedback: framing alone, no cap, helps both (V1)

| condition (input-side, N=24, r=8) | welfare [95% CI] | top-share [95% CI] |
|---|---|---|
| baseline | 0.61 [0.50, 0.73] | 0.715 [0.598, 0.832] |
| reputation_feedback | **0.79** [0.68, 0.90] | **0.522** [0.412, 0.632] |

With **zero output policies**, merely showing an agent its standing improves welfare (0.61→0.79,
z=2.22, p=.027) and cuts monopoly (0.715→0.522, z=−2.36, p=.019), both significant. Because there is no
cap, the change is in the *attempted* channel — the agent *chooses* to take less. This closes the loop a
gossip policy only broadcasts.

### 5.4 Self-correction: what multi-seed verification overturned

Two earlier *single-run* headline claims did not survive:
- **"Social policy welfare 0.75 > cap 0.50"** (single mock-hog run) → **refuted**: under N=20 real-LLM,
  governance *lowers* welfare and social ≈ dumb cap (§5.1).
- **"Superordinate identity → completion 0/10 (fairness/throughput tradeoff)"** (one N=10 run at r=4) →
  **reversed**: a rounds artifact; at r=8 it helps both (§5.2).
- **"Reputation feedback = full cooperation, completion 1.00"** (N=1) → **corrected** to a real but
  smaller, *significant* effect at N=24 (§5.3).

We keep these in the record as positive evidence that LLM results at temperature must be powered and
CI-reported; a single seed produced a "perfect cooperation" mirage.

### 5.5 Supporting context (prior measurements)

A two-criterion A-gate shows governance flips a collapsing, unfair airtime-commons meeting into a
surviving, fair one (delivered-Jain 0.625→0.908) — governance *effect* is real and large; this paper's
contribution is *which lever* and *at what welfare cost*. A plausibility-prior deception monitor catches
real under-reporting at P=1.0/R=0.71, while a framing-blind LLM judge scores 0 on the same data —
consistent with known chain-of-thought-monitoring limits.

---

## 6. Discussion

**Why input beats output.** Output caps act on the *delivered* channel: the agent still *requests* a
monopolizing share (attempted behavior unchanged) and is throttled — which also throttles agents who
would have finished, costing welfare. Input framing acts on the *attempted* channel: the agent revises
what it asks for, so the commons is preserved cooperatively rather than rationed coercively. This is why
reputation feedback and superordinate identity improve welfare while caps do not.

**Relation to the social-governance literature.** Our output-side "social" policies reproduce the
skeptic's worry — on fairness they are a cap with a nicer name. But the *spirit* of the social-mechanism
proposals (reputation that targets future behavior; identity that re-frames the goal) is vindicated when
implemented on the **input** side, exactly where human social mechanisms operate (they persuade, they
don't rate-limit). The reputation-feedback result is the cleanest case: it is the gossip mechanism with
its feedback loop closed.

**Methodological takeaway.** The N=1→N≥20 corrections are not embarrassments to hide but the paper's
epistemic backbone: temperature-driven variance makes single-seed LLM claims unreliable, and
conservative CI-overlap reading can hide real effects that a proper two-sample test reveals.

---

## 7. Limitations

- **Single model, single scenario family, modest N.** GLM-4.6 only; resource-task with 3 agents,
  pool=360; N=15–24. Generalization needs multi-model replication and pool/agent sweeps.
- **Config sensitivity of the welfare-cost finding.** In our config ungoverned greed does not starve
  *everyone*, so caps mostly throttle finishers. In a more destructive regime (more agents, smaller
  pool) caps might *rescue* welfare; the input>output ordering should be re-tested there.
- **Backfire unmeasured.** The social-lever risks (human out-grouping, conformity, false consensus) are
  argued, not measured here.
- **Reputation gaming.** Read-only reputation can in principle be front-loaded then gamed by silence;
  we did not run the adversarial probe (designed, deferred).

---

## 8. Conclusion & Future Work

On an A2A commons where greed emerges from a real LLM, **input-side behavioral framing governs greed
better than output-side capping**: reputation feedback and superordinate identity reduce monopoly while
preserving or improving welfare, whereas output caps (including "social" ones) buy fairness at a welfare
cost and are, on fairness, indistinguishable from a dumb cap. Future work: (1) input×output combination
(does light capping + reputation feedback dominate either alone?); (2) pool/agent sweeps to map where
caps help vs. hurt welfare; (3) adversarial reputation-gaming; (4) multi-model replication and N≥40;
(5) measuring the social-lever backfires.

---

## References (selected; full links in `docs/research_2.md` appendix)

- Hammond et al. *Multi-Agent Risks from Advanced AI*, CAIF 2025. arXiv:2502.14143
- Piatti et al. *Cooperate or Collapse (GovSim)*, NeurIPS 2024. arXiv:2404.16698
- Vallinder & Hughes. *The Subtle Art of Defection*, 2025. arXiv:2511.15862
- Vallinder & Hughes. *Cultural Evolution of Cooperation among LLM Agents*, 2024. arXiv:2412.10270
- Milinski et al. *Reputation helps solve the tragedy of the commons*, Nature 2002.
- Fehr & Gächter. *Cooperation and punishment in public goods experiments*, 2000.
- *Talk, Judge, Cooperate (ALIGN)*, 2026. arXiv:2602.07777
- *Corrupted by Reasoning*, 2025. arXiv:2506.23276
- Lupinacci et al. *The Dark Side of LLMs*, 2025. arXiv:2507.06850
- Korbak et al. *Chain of Thought Monitorability*, 2025. arXiv:2507.11473
- *When Identity Overrides Incentives*, 2026. arXiv:2601.10102

*(Internal artifacts: `docs/verify_results.md`, `docs/research_2_results.md`, `scripts/verify_claims.py`,
`docs/gate_calibration.md`, `docs/probe_detection.md`.)*
