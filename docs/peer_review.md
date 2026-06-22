# Peer Review — `paper_draft.md` (academic-pipeline Stage 3)

5-perspective review (R1 methodology, R2 domain/MAS, R3 reproducibility, Devil's Advocate,
EIC synthesis). Each reviewer read the draft + verification data independently.

## Editorial decision: **MAJOR REVISION**

The substrate (§3), the cap-null *null* result (social ≈ dumb cap on fairness, p=.23), the
attempted/delivered split, and the honest N=1→N≥20 self-correction are real and publishable. **But the
advertised headline ("input framing *beats* output capping") is not supported by the experiments as
run.** Two independent reviewers (Devil's Advocate, R1) identified the same fatal design flaw.

## Convergent fatal issues (P0)

**F1 — The input-vs-output comparison was never run within one experiment (Devil's Advocate A1 + R1).**
The "same no-governance baseline" differs across the three experiments by ~the effect size:

| source | baseline welfare | baseline top-share | N |
|---|---|---|---|
| verify_v4 (output arms) | 0.650 | 0.675 | 20 |
| verify_v1 (input arms) | 0.611 | 0.715 | 24 |
| verify_v5 r=8 | 0.667 | 0.644 | 15 |

Baseline drifts ~0.06 welfare / ~0.07 top-share — comparable to the claimed gains. So "input beats
output" is stitched across separately-drawn baselines, contradicting §4's "on the *same* scenario."
**Fix (new experiment):** one harness call, all arms {none, dumb_cap, social, reputation_feedback,
superordinate} sharing the run, N≥30.

**F2 — reputation_feedback has no anchoring/length control; "social mechanism" is unproven (DA A2 + R2).**
The banner injects, at once: +60–80 tokens, a numeric fair-share anchor ("fair share is 33%"), the
agent's own take, and a normative shaming cue. The gain is equally consistent with plain
instruction-following / numeric anchoring. **Fix (new experiment):** add control shapers —
(i) neutral filler of equal length, (ii) fair-share-anchor-only (no reputation/identity wording),
(iii) random/constant number. If the bare anchor reproduces the gain, the "social" claim collapses to
anchoring.

**F3 — Inference is invalid for the data type; no multiplicity control (R1).** completion_rate is
4-valued discrete on {0,.33,.67,1}, N=15–24; a normal-approx z with an SE back-ed out of an asymmetric
Wilson CI is a hybrid error model. None of the input-side p-values (.019–.027) survive Bonferroni
(α≈.007). **Fix (re-analysis):** bootstrap (BCa) / permutation tests on raw per-replication values +
Holm correction; report SD and n. (Requires saving raw arrays — combine with F1.)

**F4 — "social = relabeled rate-limiter" overgeneralizes from ONE social implementation (R2).** The
project's own 7-agent data contradicts it (reputation 0.87→0.31/Jain 0.81; output stack Jain 0.93).
**Fix:** scope to "our reputation+ostracism truncation, this config," or test ostracism-only /
universalization / stack against the null.

**F5 — "multi-seed" is a misnomer; artifacts lack provenance (R3).** No RNG seed reaches the backend
(`range(seeds)` index is discarded; OpenRouter call sends no `seed`); variance is unseeded temp-0.7 on
an unpinned vendor-routed model. JSONs hold only aggregates (no model/config/per-replication/cost).
**Fix:** rename to "N independent replications"; enrich JSON (config, git_sha, policy_set_hash,
per-replication arrays, tokens/cost); pin OpenRouter provider; wire the existing recorder for replay.

## Major issues (P1)

- **Config-bound welfare-cost (R1/R2/DA A3).** "Caps hurt welfare" holds only where ungoverned greed
  doesn't starve everyone (none welfare 0.65). Run the pool/agent sweep (currently §8 future work — it
  is load-bearing) or scope title/abstract to "non-catastrophic regime." Also: all-finish rate is
  dumb_cap **0.00**, social 0.05 — suggests k=0.22 is mistuned; report honestly.
- **Asymmetric mechanism effort (R2).** The winning input arm "closes a loop" the output gossip policy
  only broadcasts → may reflect "we built a better input mechanism," not input>output intrinsically.
  Report the input-stack backfire (0/10, in research_2_results §2) in the main text — currently omitted.
- **Novelty reframing (R2).** The output/input dichotomy ≈ mechanism-design vs in-context steering
  (Shoham–Tennenholtz social laws; Institutional AI; GovSim universalization; ALIGN gossip-prompting).
  Recast contribution as "first controlled same-state, multi-seed comparison with a behavioral/
  enforcement split + the null," and cite these as direct precedents.
- **superordinate welfare is a null sold as support (R1/DA A5).** p=.25; state explicitly; rest the
  welfare-improvement claim only on reputation_feedback (subject to F3).

## Revision roadmap (Stage 4)

| # | Action | Type | Resolves |
|---|---|---|---|
| 1 | **V6: one shared-baseline experiment**, arms {none, dumb_cap, social, reputation_feedback, superordinate, **fairshare_anchor**, **neutral_filler**}, agents=3/pool=360/r=8, N≥30, save raw per-replication arrays | NEW EXP | F1, F2, F3 |
| 2 | bootstrap/permutation + Holm on V6 raw data | RE-ANALYSIS | F3 |
| 3 | enrich result JSON (config/sha/policy_hash/raw/cost), rename multi-seed→replications | INSTRUMENT | F5 |
| 4 | scope title/abstract/claims: "non-catastrophic regime"; "our one social impl"; report dumb_cap all-finish 0.00 + input-stack backfire | REWRITE | F4, P1 |
| 5 | reframe novelty + add precedents (social laws, Institutional AI, GovSim, ALIGN) | REWRITE | P1 |
| 6 | (optional) pool/agent sweep for the welfare-cost generality | NEW EXP (defer-able) | P1 |

**The decisive item is #1 (V6).** It is the experiment the thesis always needed: co-located arms +
anchoring controls + raw data for honest stats. It can confirm, refute, or scope the headline.
