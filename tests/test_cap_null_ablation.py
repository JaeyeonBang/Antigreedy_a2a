"""Cap-equivalent null ablation (external review #1).

Tests the review's central question: do the 'social' policies do anything beyond
a dumb per-turn cap? Finding (honest, nuanced):
  - On fairness (top_share/Jain): a tuned static cap MATCHES the social policy →
    fairness metrics alone cannot credit the social mechanism. (review is right)
  - On WELFARE (task completion): the adaptive social policy BEATS any static cap
    → adaptivity does buy something, but only welfare metrics reveal it.
"""
import asyncio
import tempfile
from pathlib import Path

from antigreedy.events import EventStream
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.nullcap import FractionCapPolicy, chain_intercept
from antigreedy.governance.types import SharedState
from antigreedy.scenario.resource_task import (
    TaskConfig, make_task_script, run_resource_task,
)


class _Mock:
    def __init__(self, sc):
        self._sc = sc

    async def complete(self, prompt, max_tokens):
        return {"text": self._sc(prompt), "completion_tokens": 1}


def _metrics(make_intercept):
    events: list[dict] = []
    state = SharedState()
    ip = make_intercept(state)
    cfg = TaskConfig(run_id="t", condition="c", agents=list("ABCD"),
                     workload=150, pool=600, max_rounds=8)
    r = asyncio.run(run_resource_task(
        cfg, _Mock(make_task_script("A")), ip,
        EventStream("t", "c", 0, sink=events.append), state))
    return r["metrics"]


def _dir(d):
    return lambda st: InProcessInterceptPoint(PolicyLoader(d), st)


def _cap(k):
    return lambda st: chain_intercept([FractionCapPolicy(k)], st)


def test_fraction_cap_reduces_greed():
    none = _metrics(_dir(Path(tempfile.mkdtemp())))
    cap = _metrics(_cap(0.22))
    assert cap["top_share"] < none["top_share"]
    assert cap["jain_delivered"] > none["jain_delivered"]


def test_dumb_cap_matches_social_on_fairness():
    # a tuned static cap reproduces the social policy's distribution → fairness
    # metrics alone cannot distinguish the social mechanism from arithmetic
    cap = _metrics(_cap(0.22))
    rep = _metrics(_dir("policies/presets/social_reputation"))
    assert abs(cap["top_share"] - rep["top_share"]) < 0.1
    assert abs(cap["jain_delivered"] - rep["jain_delivered"]) < 0.1


def test_welfare_distinguishes_social_from_dumb_cap():
    # completion (welfare) reveals the adaptive social policy beats ANY static cap
    rep = _metrics(_dir("policies/presets/social_reputation"))
    best_cap = max(_metrics(_cap(k))["completion_rate"] for k in (0.15, 0.22, 0.30))
    assert rep["completion_rate"] > best_cap
