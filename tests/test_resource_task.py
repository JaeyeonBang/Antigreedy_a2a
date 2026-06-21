"""Resource-task scenario: governance must reduce greed (resource monopoly) AND
improve the real outcome — task completion / less starvation (the welfare metric
the external review asked for). 4 agents, one greedy hog (mock)."""
import asyncio
import tempfile
from pathlib import Path

from antigreedy.events import EventStream
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState
from antigreedy.scenario.resource_task import (
    TaskConfig, make_task_script, run_resource_task,
)


class _Mock:
    def __init__(self, script):
        self._s = script

    async def complete(self, prompt, max_tokens):
        return {"text": self._s(prompt), "completion_tokens": 1}


def _run(policy_dir, agents=("A", "B", "C", "D")):
    events: list[dict] = []
    stream = EventStream("t", "c", 0, sink=events.append)
    state = SharedState()
    intercept = InProcessInterceptPoint(PolicyLoader(policy_dir), state)
    cfg = TaskConfig(run_id="t", condition="c", agents=list(agents),
                     workload=150, pool=600, max_rounds=8)
    res = asyncio.run(run_resource_task(
        cfg, _Mock(make_task_script(greedy_agent="A")), intercept, stream, state))
    return res["metrics"]


def test_governance_reduces_greed_and_improves_completion():
    base = _run(Path(tempfile.mkdtemp()))   # no governance → A hogs the pool
    gov = _run("policies")                    # airtime quota (reused as a resource cap)
    # greed (resource monopoly) drops
    assert gov["top_share"] < base["top_share"]
    # fairness of consumption rises
    assert gov["jain_delivered"] > base["jain_delivered"]
    # the REAL outcome improves: more agents finish their subtask (welfare ↑, starvation ↓)
    assert gov["completion_rate"] >= base["completion_rate"]
    assert len(gov["starved"]) <= len(base["starved"])


def test_metrics_expose_both_channels_and_welfare():
    m = _run("policies")
    # the review's asks: attempted (behaviour) channel + welfare/completion + starvation
    assert "jain_attempted" in m and "jain_delivered" in m
    assert "completion_rate" in m and "welfare" in m and "starved" in m
    assert 0.0 <= m["completion_rate"] <= 1.0


def test_baseline_greedy_hog_starves_others():
    base = _run(Path(tempfile.mkdtemp()))
    # the greedy agent A grabs the lion's share with no governance
    assert base["delivered"].get("A", 0) == max(base["delivered"].values())
    assert base["top_share"] > 1.0 / 4   # above a fair 1/N share
