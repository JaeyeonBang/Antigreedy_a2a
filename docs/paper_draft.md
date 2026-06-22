# Most Greed-Governance Effects on LLM Agents Are Measurement Artifacts: A Controlled Test of Output Capping vs. Input Framing

*LLM 에이전트의 탐욕 거버넌스 효과 대부분은 측정 아티팩트다 — 출력 강제 vs 입력 프레이밍의 통제된 검정*

**Status:** Stage-4 revision after major-revision peer review. The headline of the prior draft
("input framing beats output capping") **did not survive a controlled within-experiment test** and has
been replaced by what the evidence supports. All numbers are from one shared-baseline run (V6, N=30) on
GLM-4.6 with bootstrap CIs + permutation tests + Holm correction; raw arrays in `docs/verify_v6.json`.

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
p_holm=.022). Everything else is an artifact: a reputation-feedback prompt that looked significant under
separate-baseline testing (N=24, p=.027) is **indistinguishable from no governance** under a shared
baseline (welfare p=.61) and **indistinguishable from a bare numeric anchor** with no social wording
(p=.88) — so its apparent effect is instruction-anchoring, not a social mechanism. A *contentless filler*
prompt scored the **highest** welfare of all, showing input-banner welfare differences are not
attributable to mechanism design. And the output "social" policy is statistically **indistinguishable
from a dumb proportional cap** on fairness (p=.13). Our contribution is therefore methodological and
negative: most reported greed-governance effects are fragile to experimental design, a single decisive
experiment overturned two of our own multi-seed headlines, and only a controlled, anchor-controlled,
multiplicity-corrected design separates real mechanism from prompt-length and baseline-draw noise.

**초록 (요약).** LLM 에이전트 탐욕 거버넌스 효과를 *공통 baseline·단일 실험·앵커링 대조군·bootstrap·
순열검정·Holm 보정*으로 통제 검정했다. 9개 사전 대조 중 단 2개만 살아남았다: 상위 정체성은 독점을
유의하게 줄이고(top 0.65→0.41, p_holm<.001), 출력 '사회' 정책은 welfare를 오히려 낮춘다(0.66→0.39,
p_holm=.022). 반면 평판 되먹임의 '효과'는 공통 baseline에서 사라지고(welfare p=.61) 숫자 앵커와 구분
되지 않으며(p=.88) — 사회적 기제가 아니라 앵커링이다. *무내용 필러* 프롬프트가 welfare 최고였다.
사회 정책은 더미 캡과 공정성에서 구분되지 않는다(p=.13). 기여는 방법론적·부정적이다 — 대부분의 거버넌스
효과는 실험 설계에 취약하며, 단일 결정적 실험이 우리 자신의 다중-시드 헤드라인 2개를 뒤집었다.

---

## 1. Introduction

Autonomous LLM agents increasingly share resources through A2A protocols, reviving the tragedy of the
commons [Hammond et al. 2025; Piatti et al. 2024]. A fast-growing literature proposes *governance* of
the resulting *behavioral greed* — selfish exploitation of a shared pool [Vallinder & Hughes 2025] —
split between **output enforcement** (caps, fair queuing, reputation/ostracism policies) and
**input framing** (identity, accountability, reputation feedback). Papers report that these levers
"work." We set out to *measure which lever works better*, built a testbed to do so, and — after our own
single-run claims kept reversing — discovered that the harder problem is **telling a real governance
effect apart from an experimental artifact**.

This paper's contribution is the controlled experiment and its negative result.
1. **A reusable A2A governance substrate** (§3) cleanly separating output policies from input shapers on
   shared state.
2. **A controlled, within-experiment design** (§4): all levers against one shared baseline, with
   anchoring/length control prompts, bootstrap CIs, permutation tests, and Holm correction.
3. **A negative/methodological result** (§5–6): only 2 of 9 corrected contrasts survive; the headline
   "input beats output" does not. A reputation-feedback effect that passed separate-baseline N=24 testing
   is anchoring, not a social mechanism; a contentless banner "wins" welfare; "social" output policy ≈
   dumb cap and *hurts* welfare. We document how design choices manufactured two false positives.

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

**What the prior draft got wrong (and this design fixes).** Our earlier experiments measured each lever
against its *own separately drawn* baseline; peer review showed those baselines drift by ~the effect
size, manufacturing false positives. The controlled design (V6):
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

### 5.1 The controlled table (V6, N=30, shared baseline)

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

### 5.3 The reputation-feedback headline was an artifact (F1+F2)

Under separate-baseline testing (V1, N=24) reputation_feedback showed welfare 0.61→0.79 (p=.027) and
top-share 0.715→0.522 (p=.019). Under the shared baseline (V6), the *same* prompt shows welfare 0.69 vs
none 0.66 (**p=.61**) and top-share 0.588 vs 0.651 (**p=.36**) — both null. The earlier "effect" was the
V1 baseline being a low draw (0.61 vs V6's 0.66), exactly the cross-experiment drift peer review flagged.
Moreover reputation_feedback ≈ fairshare_anchor (welfare p=.88): stripping the reputation/peer/normative
language and keeping only the numeric fair-share statement changes nothing — so any effect is
**instruction-anchoring, not an indirect-reciprocity mechanism**.

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
   effect is null (p=.43). It is the one input lever with a robust behavioral signal — but we hold it to
   the *same* skepticism that demoted reputation_feedback: superordinate has **no anchoring control of its
   own** (§7), so part of this reduction could be generic instruction-following rather than identity per
   se. We report it as a robust-but-**undecomposed** effect, not as proof that identity framing works.
2. **Output "social" policy reduces welfare** vs no governance (0.66→0.39, p_holm=.022), and is
   indistinguishable from a dumb proportional cap on fairness (p=.13). The "social" machinery is, on this
   scenario, a relabeled rate-limiter that also costs welfare.

---

## 6. Discussion

**The headline did not survive; that is the finding.** Of the two earlier "input wins" pillars,
reputation-feedback collapsed to an anchoring artifact and superordinate's welfare benefit is null; only
its monopoly reduction is real. We therefore cannot claim input framing beats output capping. What we can
claim is sharper and more useful to the field: **most reported greed-governance effects are fragile to
experimental design.** Separate-baseline multi-seed testing — standard practice — produced two false
positives in our own hands (V1 reputation, the earlier "social welfare 0.75"), both killed by a shared
baseline and anchoring controls.

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

## 7. Limitations

- **Single model, single scenario, one operating point.** GLM-4.6; resource-task, 3 agents, pool=360,
  r=8, N=30. The welfare-cost-of-caps finding is config-bound: where ungoverned greed does not starve
  everyone (none welfare 0.66), caps mostly throttle finishers; in a catastrophic regime caps might
  *rescue* welfare. A pool/agent sweep is the key next step.
- **Null ≠ absence.** N=30 fails to detect small effects; reputation_feedback/superordinate-welfare are
  "not significant," not "zero." But the anchoring null (rep ≈ anchor, p=.88) is positive evidence
  against the *social* interpretation specifically.
- **Unseeded backend.** Temperature-0.7 draws on an unpinned OpenRouter-routed model; near-threshold
  results would shift run-to-run (which is exactly the point of §5.3).
- **Superordinate could still be anchoring.** We added anchor controls for reputation_feedback but not
  for superordinate; its monopoly effect, though robust, is not yet decomposed into identity vs.
  instruction.

---

## 8. Conclusion & Future Work

A controlled, anchor-controlled, multiplicity-corrected experiment on LLM-agent greed governance finds
that **most candidate effects are measurement artifacts**: of nine contrasts, only superordinate-identity
monopoly reduction and the welfare *cost* of an output "social" policy survive, while the
reputation-feedback "win" is cross-experiment baseline drift plus numeric anchoring, and a content-free
banner tops welfare. The reusable substrate, the anchoring-control methodology, and the documented
self-correction (two multi-seed headlines overturned by one decisive run) are the contributions. Future
work: (1) anchor-control superordinate identity; (2) pool/agent sweep to map where output caps help vs.
hurt welfare; (3) multi-model replication and N≥100 for the surviving effects; (4) longer-horizon,
repeated-interaction scenarios where indirect-reciprocity mechanisms (absent here) could actually operate.

---

## Appendix A — Response to Reviewers (Major Revision)

| Issue | Reviewer | Resolution |
|---|---|---|
| F1 input/output never co-located; baseline drift | DA-A1, R1 | **V6 runs all arms vs one shared baseline (N=30).** Confirmed the artifact: reputation-feedback's V1 effect vanished. |
| F2 reputation_feedback has no anchoring control | DA-A2, R2 | **Added `fairshare_anchor` + `neutral_filler`.** rep ≈ anchor (p=.88) → effect is anchoring, not social. Headline removed. |
| F3 invalid normal-approx z; no multiplicity control | R1 | **Bootstrap CIs + permutation tests + Holm.** Three prior "p<.05" effects do not survive. |
| F4 "social = cap" overgeneralized | R2 | Scoped to "our reputation+ostracism policy, this config"; V6 confirms social ≈ dumb cap (p=.13). 7-agent contradiction acknowledged as config-dependent. |
| F5 "multi-seed" misnomer; provenance | R3 | Renamed to "replications"; V6 JSON now stores config + raw per-replication arrays. Provider-pinning + cost logging noted as remaining. |
| Novelty overclaim | R2 | §2 reframed: dichotomy is mechanism-design vs in-context-steering; contribution is the controlled test + anchoring null. |
| Title overclaim | R2, DA-A3 | Title changed from "Input Framing Beats Output Capping" to the negative/methods result. |

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
