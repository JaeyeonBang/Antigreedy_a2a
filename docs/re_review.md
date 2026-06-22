# Re-Review — `paper_draft.md` (academic-pipeline Stage 3')

Verification review of the Stage-4 revision against the Stage-3 roadmap (F1–F5) + residual-issue
scan. All paper numbers independently re-derived from `docs/verify_v6.json` raw arrays.

## Editorial decision: **ACCEPT WITH MINOR REVISIONS** → Stage 4.5

No new experiment required. The revision resolves the two FATAL flaws (F1 baseline drift, F2 missing
anchoring control) that gated the prior major revision. Remaining items are text-only.

## Integrity (100% pass)

Every cell of §5.1 (14 values) and every contrast of §5.2 (9 p / p_holm) traces exactly to
`verify_v6.json`. Spot checks: `none` welfare 0.6555→0.66 & boot [0.555,0.756]→[0.56,0.76];
`neutral_filler` welfare 0.8222→0.82; `superordinate` top 0.4122→0.41; rep-vs-anchor p .8805→.881;
superordinate-top p 9.999e-05→.0001, p_holm 8.999e-04→.0009. `comp_raw`/`top_raw` are real n=30
per-replication arrays, `failed=0` on all arms. No hallucinated results, no bug-as-insight.

## F1–F5 resolution

| # | Verdict | Evidence |
|---|---|---|
| F1 baseline drift | ✅ RESOLVED | V6 = 7 arms vs one shared `none`, N=30; rep V1 effect confirmed vanished (welfare p=.61) |
| F2 anchoring control | ✅ RESOLVED | `fairshare_anchor`+`neutral_filler` added; rep≈anchor welfare p=.88 → anchoring, not social |
| F3 invalid stats | ✅ RESOLVED | bootstrap CIs + permutation tests + Holm; 3 prior "p<.05" effects die |
| F4 social=cap overclaim | ✅ SCOPED | scoped to this config; social≈dumb_cap top p=.13; 7-agent contradiction acknowledged |
| F5 provenance | 🟡 PARTIAL | renamed "replications", config+raw stored; **git_sha/policy_hash/per-rep cost absent** — disclosed as remaining |

## Residual issues

- **R1 (moderate) — asymmetric skepticism. [FIXED in §5.5]** Paper demoted reputation_feedback for
  lacking an anchoring control, then promoted superordinate (same missing control) as a "robust signal."
  Edit added the symmetric caveat inline: superordinate reported as robust-but-undecomposed.
- **R2 (minor, defensible) — "nine pre-specified contrasts."** The 9 map to the peer-review roadmap
  arms/decompositions defined before V6; no formal pre-registration artifact. Left as-is.
- **R3 (minor) — F5 provenance gap.** `config` lacks git_sha/policy_set_hash/per-rep cost+tokens.
  Honestly disclosed in App-A as remaining; non-blocking for a methods paper.
- **R4 (minor) — unseeded resampler.** Permutation/bootstrap RNG not seeded; near-threshold p
  (neutral_filler .042) would wobble run-to-run. Both surviving effects (.0001, .0028) are far from
  threshold → robust. Seed before any N≥100 follow-up.

## Recommendation

Proceed to **Stage 4.5 FINAL INTEGRITY**. R2–R4 are disclosed limitations, not blockers. If desired,
R3 (enrich JSON provenance) and R4 (seed resampler) can be cleared in a 4' pass, but neither changes a
single reported result.
