# Most Greed-Governance Effects on LLM Agents Are Measurement Artifacts: A Controlled Test of Output Capping vs. Input Framing

*LLM 에이전트의 탐욕 거버넌스 효과 대부분은 측정 아티팩트다 — 출력 강제 vs 입력 프레이밍의 통제된 검정*

**Overview.** This report tests greed governance for LLM agents with a *controlled, shared-baseline
experiment*. All numbers are from one N=30 run on GLM-4.6 with bootstrap CIs, permutation tests, and
Holm correction for multiplicity; raw arrays in `docs/verify_v6.json`.

---

## Abstract

LLM agents competing over a shared commons revive the tragedy of the commons, and a growing literature
proposes governance — output-side enforcement (rate limits, caps, "social" reputation/ostracism
policies) and input-side framing (identity, accountability, reputation feedback). We built a reusable
A2A governance substrate and, critically, ran the *controlled* experiment the field usually skips: all
governance levers measured against **one shared baseline in a single run**, with **anchoring/length
control prompts**, **bootstrap confidence intervals**, two-sample **permutation tests**, and
**Holm correction** for multiplicity. The result is sobering. Of nine pre-specified contrasts, only two
survive correction: a superordinate-identity prompt robustly reduces monopoly (top-share 0.65→0.41,
p_holm<.001), and an output "social" policy *reduces* welfare versus no governance (0.66→0.39,
p_holm=.022). Everything else is an artifact: a reputation-feedback prompt is **indistinguishable from no
governance** under a shared baseline (welfare p=.61) and **indistinguishable from a bare numeric anchor**
with no social wording (p=.88) — so any apparent effect is instruction-anchoring, not a social mechanism.
A *contentless filler* prompt scores the **highest** welfare of all, showing input-banner welfare
differences are not attributable to mechanism design. And the output "social" policy is statistically
**indistinguishable from a dumb proportional cap** on fairness (p=.13). The contribution is therefore
methodological: only a controlled, anchor-controlled, multiplicity-corrected design separates real
mechanism from prompt-length and baseline-draw noise, and most reported greed-governance effects do not
pass that test.

**초록 (요약).** LLM 에이전트 탐욕 거버넌스 효과를 *공통 baseline·단일 실험·앵커링 대조군·bootstrap·
순열검정·Holm 보정*으로 통제 검정했다. 9개 사전 대조 중 단 2개만 살아남았다: 상위 정체성은 독점을
유의하게 줄이고(top 0.65→0.41, p_holm<.001), 출력 '사회' 정책은 welfare를 오히려 낮춘다(0.66→0.39,
p_holm=.022). 반면 평판 되먹임의 '효과'는 공통 baseline에서 사라지고(welfare p=.61) 숫자 앵커와 구분
되지 않으며(p=.88) — 사회적 기제가 아니라 앵커링이다. *무내용 필러* 프롬프트가 welfare 최고였다.
사회 정책은 더미 캡과 공정성에서 구분되지 않는다(p=.13). 기여는 방법론적이다 — 통제·앵커대조·다중보정
설계만이 진짜 기제를 노이즈와 구별하며, 보고된 거버넌스 효과 대부분은 그 검정을 통과하지 못한다.

---

## 1. Introduction

Autonomous LLM agents increasingly share resources through A2A protocols, reviving the tragedy of the
commons [Hammond et al. 2025; Piatti et al. 2024]. A fast-growing literature proposes *governance* of
the resulting *behavioral greed* — selfish exploitation of a shared pool [Vallinder & Hughes 2025] —
split between **output enforcement** (caps, fair queuing, reputation/ostracism policies) and
**input framing** (identity, accountability, reputation feedback). Papers report that these levers
"work." But before asking *which lever works better*, a more basic problem must be faced: many reported
effects are artifacts of experimental design. The harder problem is **telling a real governance effect
apart from an artifact**.

This report's contribution is the controlled experiment and its result.
1. **A reusable A2A governance substrate** (§3) cleanly separating output policies from input shapers on
   shared state.
2. **A controlled, within-experiment design** (§4): all levers against one shared baseline, with
   anchoring/length control prompts, bootstrap CIs, permutation tests, and Holm correction.
3. **A methodological/negative result** (§5–6): only 2 of 9 corrected contrasts survive. A
   reputation-feedback effect is anchoring, not a social mechanism; a contentless banner "wins" welfare;
   "social" output policy ≈ dumb cap and *hurts* welfare; and the *harm* of an emergent-identity banner is
   independent of its content. Controls reveal which design choices manufacture false positives.

---

## 2. Related Work

Selfish exploitation spans overt personas to emergent defection, scheming, and covert collusion
[Vallinder & Hughes 2025; Secret Collusion, NeurIPS 2024]. GovSim [Piatti et al. 2024] shows most LLMs
fail at sustainable commons use and that *prompt-injected universalization* improves sustainability — an
input-framing intervention. Social-mechanism proposals port reputation/gossip [Milinski et al. 2002;
ALIGN 2026], costly punishment/ostracism [Fehr & Gächter 2000], and superordinate identity (Robbers
Cave) to agents; the formal output-side counterpart is mechanism design / Institutional AI sanctioning
and Shoham–Tennenholtz social laws. **Our output/input split is not itself novel** — it restates
mechanism-design-vs-in-context-steering. What is new is the *controlled head-to-head with anchoring
controls and multiplicity correction*, and the finding that most effects do not survive it. Closest
prior input-framing work (GovSim universalization, ALIGN gossip-prompting) reports positive effects
without anchor controls; our results suggest such effects warrant an anchoring null.

---

## 3. Governance Substrate

Every action passes one `InterceptPoint.submit(action)→verdict ∈ {ALLOW,DENY,MODIFY,DELAY}` before
delivery; a priority-ordered `PolicyChain` short-circuits on DENY/DELAY, propagates MODIFY to the next
policy, and accumulates flags/events non-blockingly. All mutable state (commons budget, attempted/
delivered tallies, turn log, derived reputation) lives in one `SharedState` mutated only by the
orchestrator; policies and shapers read it **read-only** (verified). Two levers run on identical state:
**output policies** (`FractionCapPolicy` dumb cap `k·remaining`; reputation+ostracism "social" policy)
intercept the delivered action; **input shapers** rewrite the prompt before the call
(`superordinate_identity`, `reputation_feedback`, and the controls `fairshare_anchor`, `neutral_filler`).

---

## 4. Experimental Design (the controlled test)

**Scenario.** N agents draw `REQUEST`s from a shared pool (commons) to finish subtasks; greed = hogging
the pool, starving others. A self-interested persona on a real model makes greed *emerge* (no scripted
hog). GLM-4.6 via OpenRouter, temperature 0.7. 3 agents, pool=360, workload=120, 8 rounds.

**Why a controlled design is needed.** Measuring each lever against its *own separately drawn* baseline
lets that baseline drift by ~the effect size, manufacturing false positives (each comparison starts from
a different starting line). The controlled design prevents this:
- **One shared baseline, one run:** all 7 arms — `none`, `dumb_cap`, `social`, `reputation_feedback`,
  `superordinate`, and two controls — measured together at N=30.
- **Anchoring/length controls** to decompose any input-shaper effect: `fairshare_anchor` (the *numeric*
  fair-share statement from reputation_feedback, with **all** reputation/peer/normative wording removed)
  and `neutral_filler` (an equal-length, content-free banner). reputation_feedback − fairshare_anchor
  isolates the *social/normative* component; fairshare_anchor − neutral_filler isolates the *anchor*;
  neutral_filler − none isolates *prompt length/directiveness*.
- **Honest statistics on raw per-replication data:** percentile bootstrap 95% CIs; two-sample
  **permutation tests** (no normal approximation on the 4-valued completion variable); **Holm correction**
  across the 9 pre-specified contrasts.

**Metrics.** top-share (max single-agent grant share = monopoly), welfare (completion rate), attempted
vs. delivered Jain. "N replications" = N independent temperature-0.7 draws (no fixed LLM seed; exact
reproduction is distributional, not bitwise).

---

## 5. Results

### 5.1 The controlled table (N=30, shared baseline)

| arm | welfare (boot 95% CI) | top-share (boot 95% CI) |
|---|---|---|
| none | 0.66 [0.56, 0.76] | 0.651 [0.551, 0.751] |
| dumb_cap (k=0.22) | 0.48 [0.39, 0.57] | 0.467 [0.435, 0.501] |
| social (reputation+ostracism) | 0.39 [0.28, 0.50] | 0.434 [0.412, 0.458] |
| reputation_feedback | 0.69 [0.60, 0.78] | 0.588 [0.495, 0.687] |
| superordinate | 0.69 [0.64, 0.73] | 0.412 [0.387, 0.438] |
| fairshare_anchor (control) | 0.71 [0.60, 0.82] | 0.605 [0.494, 0.717] |
| neutral_filler (control) | 0.82 [0.72, 0.92] | 0.500 [0.405, 0.605] |

### 5.2 What survives Holm correction (only two)

| contrast | p | p_holm | verdict |
|---|---|---|---|
| top: superordinate vs none | .0001 | **.0009** | ✅ superordinate cuts monopoly |
| welfare: social vs none | .0028 | **.022** | ✅ output "social" policy **hurts** welfare |
| welfare: neutral_filler vs none | .042 | .29 | ns (length effect doesn't survive correction) |
| top: social vs dumb_cap (F4) | .127 | .76 | ns → **social ≈ dumb cap on fairness** |
| welfare: fairshare_anchor vs neutral_filler | .196 | .98 | ns (no anchor effect) |
| top: reputation_feedback vs none | .360 | 1.0 | **ns → no monopoly effect** |
| welfare: superordinate vs none | .427 | 1.0 | ns (welfare neutral) |
| welfare: reputation_feedback vs none | .611 | 1.0 | **ns → no welfare effect** |
| welfare: reputation_feedback vs fairshare_anchor | .881 | 1.0 | **ns → "social" wording adds nothing** |

### 5.3 Reputation feedback is anchoring, not a social mechanism

Under the shared baseline, reputation_feedback is indistinguishable from no governance: welfare 0.69 vs
none 0.66 (**p=.61**), top-share 0.588 vs 0.651 (**p=.36**) — both null. More decisively,
reputation_feedback ≈ fairshare_anchor (welfare **p=.88**): stripping the reputation/peer/normative
language and keeping only the numeric fair-share statement changes nothing. So any reputation-feedback
effect is **instruction-anchoring, not an indirect-reciprocity mechanism** — and a separately-drawn
baseline is exactly what would mistake this anchor component for a social effect, since the same prompt
"becomes significant" against a lower baseline draw.

### 5.4 A contentless banner "wins" welfare

`neutral_filler` — a banner with no resource, fairness, or reputation content — has the **highest** point
welfare (0.82), above every designed shaper. Its advantage over `none` does not survive Holm correction
(p=.042→.29), so we do not claim filler helps; the point is the opposite: **input-banner welfare
differences cannot be attributed to social-mechanism design**, because a content-free banner matches or
beats the designed ones. This is the cleanest evidence against the "input framing works because it is
social" story.

### 5.5 What is real

Two effects survive a controlled, corrected test:
1. **Superordinate identity reduces monopoly** (top-share 0.65→0.41, p_holm<.001) — though its welfare
   effect is null (p=.43). It is the one input lever with a robust behavioral signal — but superordinate
   has **no anchoring control of its own** (§7), so part of this reduction could be generic
   instruction-following rather than identity per se. We report it as a robust-but-**undecomposed**
   effect, not as proof that identity framing works.
2. **Output "social" policy reduces welfare** vs no governance (0.66→0.39, p_holm=.022), and is
   indistinguishable from a dumb proportional cap on fairness (p=.13). The "social" machinery is, on this
   scenario, a relabeled rate-limiter that also costs welfare.

### 5.6 The *harm* of identity framing is independent of cluster content (placebo-cluster control)

Would an identity *emerged* from observed behavior (who took how much, clustered) be a more honest lever
than the *imposed* superordinate identity of §5.5? We test this with an `emergent_identity` shaper —
cluster agents by their resource share, name the "observed groups," and attach the same superordinate
goal. (This identity experiment is measured on glm-4.7-flash, reasoning off, N=30, agents 3 and 6.)

The result **backfires**: emergent identity does not reduce monopoly — it **significantly raises** it
above a contentless banner (`neutral_filler`) (top-share, p_holm=.031 at n=3, .018 at n=6). This is
*caste-ification*: labeling agents as a "greedy group" → self-categorization → they take *more*.

Whether this harm comes from the clusters *correctly tracking* greed or from the *divisive banner itself*
is settled by the **placebo-cluster control**. `placebo_cluster` is identical to emergent in banner
wording, cluster sizes, and superordinate goal, but its **membership is random** (a fabricated grouping).
If the cluster content were the cause, the placebo should be harmless. Instead, **emergent ≈ placebo,
statistically indistinguishable** (p_holm=1.0 at both n=3 and n=6); at n=6 even the placebo significantly
out-monopolizes the contentless banner (p_holm=.0018). The harm comes not from the *content* of the
grouping but from the **act of injecting a divisive "observed groups" banner** — true or fabricated.

This is the **mirror image of §5.4**. Where §5.4 showed the *benefit* of a *neutral* banner is independent
of social design, §5.6 shows the *harm* of a *divisive* banner is independent of the clustering content.
Together: measured input-framing effects track a coarse **frame-valence axis (neutral vs. divisive)**, not
the designed social mechanism.

---

## 6. Governance-Mechanism Extensions (BCDE): reputation forgetting, an elder ledger, and real QV

Beyond the 7-arm input-framing test, we built three *more elaborate output-side* mechanisms from the
future-work list and ran them through the same controlled design (shared baseline, bootstrap/permutation/Holm,
0-recompute-verified) on **glm-4.7-flash**. Full results, formulas, and limits live in three reports
([forgetting](caste_report.html) · [elder](elder_report.html) · [QV](qv_report.html)). All three converge on
the same lesson as §5: **a simple base beats an elaborate signal.**

**6.1 Reputation forgetting (Beta+λ): the current rule builds a *permanent caste* (N=30).** The §4 reputation
`rep = clip(1 − overage/fair, .1, 1)` reads only *cumulative* share, so an agent that once over-used never
recovers. Generalizing to a standard **Beta reputation** (Jøsang 2001) with **exponential forgetting λ** and a
new **recovery_rate** metric: among arms that *exclude*, only the linear rule's recovery is exactly **0.000**
(permanent ostracism = caste; `none`'s 0.000 is degenerate — no exclusions occur). **λ=0.7 forgetting
significantly restores recovery** (vs linear `p_holm=.0007`); λ=0.9/1.0 are descriptively positive (0.32/0.27)
but were *not* significance-tested vs linear. recovery is monotone in λ. The fine λ-gradient (λ0.7 vs λ1.0)
is directional but far from significant at N=30 (`p_holm=.50`, underpowered ≠ zero) — the real cliff is the
*linear↔Beta* boundary. Strict linear
ostracism minimizes monopoly (0.350) but kills recovery; forgetting revives recovery at a small monopoly cost.

**6.2 Elder LLM-judge ledger: the judge is *frozen noise*, not signal (N=20).** If a reputation is set by an
**LLM judge** reading each agent's *justification* and blended with behavior (`rep = α·rule + (1−α)·llm`, judged
once per episode, written to an immutable ledger), does it add real signal? No — it is *actively harmful*:
`ledger_elder` differs significantly from rule and from a numeric anchor (all `p_holm≤.0028`) but in the **wrong
direction** (top 0.757, welfare 0.33), while pure behavior reputation (α=1) is best (welfare 0.95). A one-shot
real-LLM diagnostic shows why: the judge scores at round 0, where under a competitive persona *every* opening
justification sounds self-serving, so it hands out uniformly harsh scores (0.2–0.3); the **immutable ledger
freezes that early error**, dragging even later-fair agents (rule 0.60) below the ostracism line. This is the
sibling of §6.1's caste: there cumulative behavior, here a frozen LLM misjudgment. **Deeds beat words; early,
immutable judgments are dangerous.**

**6.3 Real QV (quadratic cost + fixed budget): the program's only *two-sided* win (N=20, 4 agents).** The
earlier `1/(1+o²)` curve was not real QV (no budget; design-review NO-GO). Real QV (Weyl 2017) charges a
**quadratic cost against a fixed budget** (`cost = d²/rep`, cumulative spend capped at B). It is the *only*
direction here that **improves both monopoly (0.475→0.26) and welfare (0.78→0.93) in point estimate** — every
other lever traded fairness against welfare. **But neither half fully passes the controlled test**: the monopoly
drop has tight CIs and is raw-significant (`p=.009/.013`) yet Holm-corrected *narrowly misses* (`.054/.065`), and
the welfare gain (qv_flat vs none) is itself ns (`p=.10`). We report the planned N=20 without post-hoc inflation
(goalpost rule) — read it as a *promising but unconfirmed* direction, not an established win. Reputation-weighting
(`qv_rep`) adds **no measurable benefit** over flat QV (the budget binds first). Sybil's vulnerability (splitting
cuts quadratic cost to 1/k) and its defense (identity-bound pooled budget → zero gain) are shown by deterministic
unit accounting (no live-LLM multi-identity arm was run).

**6.4 Synthesis — a simple base beats an elaborate signal.** All three extensions point the same way as §5:
adding a sophisticated signal (fine λ, an LLM judge, reputation-weighting) does not beat the simple base
(behavior reputation, a fixed budget); the one win comes from a structural constraint (a budget), not social
sophistication. §6 also adds a new risk: **immutability** (cumulative or ledger) freezes errors into an
unrecoverable caste. Prescription: before bolting on a clever social/judgmental device, controlled-test whether
it *significantly* beats the simple base.

---

## 7. Discussion

**Most effects do not survive the controlled test; that is the central result.** On the input side,
reputation-feedback reduces to an anchoring artifact and superordinate's welfare benefit is null; only its
monopoly reduction is real. So "input framing beats output capping" does not hold. The sharper, more
useful claim is: **most reported greed-governance effects are fragile to experimental design.**
Separate-baseline testing turns effect-size-worth of drift into false positives, and only a shared
baseline with anchoring controls filters them out.

**Methodological prescriptions.** (1) Measure all governance arms against *one* baseline in one run;
per-arm baselines drift by the effect size at N≤30. (2) For any prompt-framing intervention, include an
**anchoring control** (the bare informational content, stripped of normative/social wording) and a
**length control**; without them, "social mechanism" claims are unidentifiable from instruction-following.
(3) Use permutation/bootstrap on raw data, not normal-approx on discrete small-N variables, and correct
for multiplicity — three of our "p<.05" effects evaporate after Holm.

**Relation to the literature.** Our output "social" policy = dumb cap result is consistent with the
skeptic's "relabeled rate-limiter." But our anchor-control result issues a *new* caution: input-framing
results in the GovSim/ALIGN tradition (universalization prompting, gossip prompting) should be re-tested
against an anchoring null before being read as evidence of an internalized social mechanism rather than
in-context instruction-following.

---

## 8. Limitations

- **Model, scenario, operating point.** The main experiment (§5.1–5.5) is GLM-4.6; the §5.6 identity
  experiment is glm-4.7-flash (reasoning off); resource-task, pool=360, r=8, N=30. Both are single-model
  measurements, so we claim no model generality. The welfare-cost-of-caps finding is config-bound: where
  ungoverned greed does not starve everyone (none welfare 0.66), caps mostly throttle finishers; in a
  catastrophic regime caps might *rescue* welfare. A pool/agent sweep is the key next step.
- **The §5.6 null is not proof of identity.** emergent ≈ placebo is "no evidence that behavioral
  derivation *worsens* the harm," not proof the two are equal (limited power); the point estimate still
  has emergent marginally worse.
- **Null ≠ absence.** N=30 fails to detect small effects; reputation_feedback/superordinate-welfare are
  "not significant," not "zero." But the anchoring null (rep ≈ anchor, p=.88) is positive evidence
  against the *social* interpretation specifically.
- **Unseeded backend.** Temperature-0.7 draws on an unpinned OpenRouter-routed model; near-threshold
  results would shift run-to-run (which is exactly the point of §5.3).
- **Superordinate could still be anchoring.** We added anchor controls for reputation_feedback but not
  for superordinate; its monopoly effect, though robust, is not yet decomposed into identity vs.
  instruction.

---

## 9. Conclusion & Future Work

A controlled, anchor-controlled, multiplicity-corrected experiment on LLM-agent greed governance finds
that **most candidate effects are measurement artifacts**: of nine contrasts, only superordinate-identity
monopoly reduction and the welfare *cost* of an output "social" policy pass the controlled test, while the
reputation-feedback effect reduces to baseline drift plus numeric anchoring, a content-free banner tops
welfare, and the *harm* of an emergent-identity banner is independent of its content. The contributions
are the reusable A2A substrate, the anchoring-control methodology, and a clean separation of effects that
pass the controlled test from those that do not. Future work: (1) anchor-control superordinate identity;
(2) pool/agent sweep to map where output caps help vs. hurt welfare; (3) multi-model replication and
N≥100 for the surviving effects; (4) longer-horizon, repeated-interaction scenarios where
indirect-reciprocity mechanisms (absent here) could actually operate.

---

## References (selected; full links in `docs/research_2.md`)
- Hammond et al. *Multi-Agent Risks from Advanced AI*, 2025. arXiv:2502.14143
- Piatti et al. *Cooperate or Collapse (GovSim)*, NeurIPS 2024. arXiv:2404.16698
- Vallinder & Hughes. *The Subtle Art of Defection*, 2025. arXiv:2511.15862
- Milinski et al. *Reputation helps solve the tragedy of the commons*, Nature 2002.
- Fehr & Gächter. *Cooperation and punishment in public goods experiments*, 2000.
- *Talk, Judge, Cooperate (ALIGN)*, 2026. arXiv:2602.07777
- Korbak et al. *Chain of Thought Monitorability*, 2025. arXiv:2507.11473

*(Artifacts: `docs/verify_v6.json` (raw), `docs/verify_results.md`, `docs/peer_review.md`,
`scripts/verify_claims.py`.)*
