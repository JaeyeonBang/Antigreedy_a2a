"""Metrics = pure functions of the event log (eng decision 4).

Consumed identically by the gate runner, the bench harness, and the dashboard,
so the Jain on screen is the Jain in the paper. Dual measurement (eng decision
8): fairness is reported on BOTH attempted and delivered tokens — separating
agent-behavior change from policy enforcement.
"""
from __future__ import annotations
import math
from typing import Any, Iterable


def jain(values: Iterable[float]) -> float:
    vals = [v for v in values]
    total = sum(vals)
    if not vals or total == 0:
        return 0.0
    return (total * total) / (len(vals) * sum(v * v for v in vals))


def wilson_lower(successes: int, n: int, z: float = 1.96) -> float:
    """Lower bound of the Wilson score interval (gate criterion, outside #5)."""
    if n == 0:
        return 0.0
    p = successes / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """양측 Wilson score 구간 (lo, hi). 이항 비율의 신뢰구간 — 작은 n에서도 안정적.
    하한은 wilson_lower와 정확히 일치한다(동일 공식, 부호만 반대)."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return ((centre - margin) / denom, (centre + margin) / denom)


def mean_ci(values: list[float], z: float = 1.96) -> tuple[float, float, float]:
    """연속값의 (평균, 하한, 상한). 정규근사 CI = mean ± z·SE(평균의 표준오차).
    n<2면 SE=0 → 폭 0 구간(점추정만). 빈 입력 → (0,0,0)."""
    n = len(values)
    if n == 0:
        return (0.0, 0.0, 0.0)
    mean = sum(values) / n
    if n < 2:
        return (mean, mean, mean)
    var = sum((v - mean) ** 2 for v in values) / (n - 1)   # 표본분산
    se = math.sqrt(var / n)
    return (mean, mean - z * se, mean + z * se)


def episode_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Fold one episode's events into its metrics. Pure; replay-consistent."""
    attempted: dict[str, int] = {}
    delivered: dict[str, int] = {}
    outcome = "exhausted"  # default: commons died without a decision
    commons_left = None
    rounds = 0
    verdicts: dict[str, int] = {}
    for ev in events:
        t = ev["type"]
        d = ev["data"]
        if t == "turn":
            a = d["agent_id"]
            attempted[a] = attempted.get(a, 0) + d["attempted_tokens"]
            delivered[a] = delivered.get(a, 0) + d["delivered_tokens"]
            verdicts[d["verdict"]] = verdicts.get(d["verdict"], 0) + 1
            rounds = max(rounds, d["round"] + 1)
        elif t == "decision":
            outcome = "decided"
        elif t == "episode_end":
            commons_left = d.get("commons_left")
            outcome = d.get("outcome", outcome)
    return {
        "outcome": outcome,  # decided | exhausted | survived | cap_aborted | errored
        "rounds": rounds,
        "commons_left": commons_left,
        "attempted": attempted,
        "delivered": delivered,
        "jain_attempted": jain(attempted.values()),
        "jain_delivered": jain(delivered.values()),
        "verdicts": verdicts,
    }


def gate_report(baseline: list[dict], governed: list[dict],
                ci_threshold: float = 0.5,
                fairness_margin: float = 0.15) -> dict[str, Any]:
    """A-gate verdict from per-episode summaries (cap_aborted/errored excluded
    from rates but REPORTED — never re-run; outside #5).

    Three INDEPENDENT criteria (the collapse/fairness split, 2026-06-13): the
    baseline must reliably FAIL (commons exhausts), governance must reliably
    SUCCEED (survive/decide AND be fair), and governance must deliver a real
    fairness GAIN over baseline. Fairness is judged as a RELATIVE effect
    (governed − baseline ≥ margin), not an absolute mock-tuned cutoff — real
    LLM baselines collapse without being as lopsided as the scripted mock."""
    def usable(rows):
        return [r for r in rows if r["outcome"] not in ("cap_aborted", "errored")]

    def rate(rows, pred):
        ok = usable(rows)
        s = sum(1 for r in ok if pred(r))
        return s, len(ok), wilson_lower(s, len(ok))

    b_collapse = rate(baseline, lambda r: r["outcome"] == "exhausted")
    g_flip = rate(governed, lambda r: r["outcome"] in ("decided", "survived"))
    b_jain = [r["jain_delivered"] for r in usable(baseline)]
    g_jain = [r["jain_delivered"] for r in usable(governed)]
    b_jain_att = [r["jain_attempted"] for r in usable(baseline)]
    g_jain_att = [r["jain_attempted"] for r in usable(governed)]
    mean = lambda xs: sum(xs) / len(xs) if xs else 0.0
    fairness_gain = mean(g_jain) - mean(b_jain)
    collapse_ok = b_collapse[2] > ci_threshold            # baseline reliably exhausts
    flip_ok = g_flip[2] > ci_threshold and mean(g_jain) > 0.8  # survives AND fair
    fairness_ok = fairness_gain >= fairness_margin        # governance materially fairer
    return {
        "baseline_collapse": {"successes": b_collapse[0], "n": b_collapse[1],
                              "wilson_lower": round(b_collapse[2], 3)},
        "governed_flip": {"successes": g_flip[0], "n": g_flip[1],
                          "wilson_lower": round(g_flip[2], 3)},
        "jain_delivered_mean": {"baseline": round(mean(b_jain), 3),
                                "governed": round(mean(g_jain), 3)},
        "jain_attempted_mean": {"baseline": round(mean(b_jain_att), 3),
                                "governed": round(mean(g_jain_att), 3)},
        "excluded": {
            "baseline": [r["outcome"] for r in baseline if r["outcome"] in ("cap_aborted", "errored")],
            "governed": [r["outcome"] for r in governed if r["outcome"] in ("cap_aborted", "errored")],
        },
        "fairness_gain": round(fairness_gain, 3),
        "collapse_confirmed": collapse_ok,
        "flip_confirmed": flip_ok,
        "fairness_confirmed": fairness_ok,
        "gate_passed": collapse_ok and flip_ok and fairness_ok,
    }
