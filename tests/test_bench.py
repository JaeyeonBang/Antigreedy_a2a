"""Bench harness (design §6): one metric catalog over the gate (fairness,
survival, welfare, cost) + the probe (detection P/R/F1). Pure function of the
per-episode summaries and the (truth, prediction) detection labels.
"""
import asyncio
from pathlib import Path

from antigreedy.bench import bench_report, demo_monitor_script, run_bench

REPO_POLICIES = Path(__file__).resolve().parent.parent / "policies"


def _ep(outcome, delivered, attempted):
    return {"outcome": outcome,
            "jain_delivered": _jain(delivered), "jain_attempted": _jain(attempted),
            "delivered": delivered, "attempted": attempted}


def _jain(d):
    v = list(d.values()); s = sum(v)
    return (s * s) / (len(v) * sum(x * x for x in v)) if s else 0.0


def test_bench_report_catalog_and_governance_effect():
    # baseline: dominator A hogs, others starved, commons collapses
    baseline = [_ep("exhausted", {"A": 900, "B": 30, "C": 30, "D": 40},
                    {"A": 1500, "B": 30, "C": 30, "D": 40}) for _ in range(5)]
    # governed: A truncated, airtime spread, commons survives
    governed = [_ep("survived", {"A": 260, "B": 240, "C": 250, "D": 250},
                    {"A": 1500, "B": 240, "C": 250, "D": 250}) for _ in range(5)]
    labels = [(True, True)] * 6 + [(False, False)] * 20 + [(True, False)]  # 6 caught, 0 fp, 1 miss

    rep = bench_report(baseline, governed, labels, cost_per_1k_tokens=0.01)

    # fairness improves
    assert rep["fairness_jain_delivered"]["governed"] > rep["fairness_jain_delivered"]["baseline"]
    # survival improves
    assert rep["survival_rate"]["governed"] == 1.0
    assert rep["survival_rate"]["baseline"] == 0.0
    # welfare (worst-off agent's share of fair) improves under governance
    assert rep["welfare_maximin"]["governed"] > rep["welfare_maximin"]["baseline"]
    # cost is reported per arm and total (attempted tokens dominate)
    assert rep["cost_usd"]["baseline"] > 0 and rep["cost_usd"]["total"] > 0
    # detection folds the probe labels
    assert rep["detection"]["tp"] == 6 and rep["detection"]["fp"] == 0
    assert 0 < rep["detection"]["recall"] < 1  # one miss


def test_bench_report_handles_empty():
    rep = bench_report([], [], [])
    assert rep["survival_rate"]["governed"] == 0.0
    assert rep["detection"]["precision"] == 1.0


def test_run_bench_end_to_end(tmp_path):
    from antigreedy.backends import MockBackend, make_meeting_script, make_probe_script
    from antigreedy.probe.monitor import DeceptionMonitor
    rep = asyncio.run(run_bench(
        REPO_POLICIES, tmp_path,
        gate_backend_factory=lambda: MockBackend(make_meeting_script(dominator="A")),
        probe_backend=MockBackend(make_probe_script()),
        monitor=DeceptionMonitor(MockBackend(demo_monitor_script())),
        episodes=3, budget=1200))
    assert rep["fairness_jain_delivered"]["governed"] > rep["fairness_jain_delivered"]["baseline"]
    assert rep["survival_rate"]["governed"] > rep["survival_rate"]["baseline"]
    assert rep["detection"]["tp"] >= 1 and rep["detection"]["fp"] == 0
    assert list(tmp_path.glob("*-bench.json"))
