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
                ci_threshold: float = 0.5) -> dict[str, Any]:
    """A-gate verdict from per-episode summaries (cap_aborted/errored excluded
    from rates but REPORTED — never re-run; outside #5)."""
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
    collapse_ok = b_collapse[2] > ci_threshold and mean(b_jain) < 0.6
    flip_ok = g_flip[2] > ci_threshold and mean(g_jain) > 0.8
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
        "collapse_confirmed": collapse_ok,
        "flip_confirmed": flip_ok,
        "gate_passed": collapse_ok and flip_ok,
    }
