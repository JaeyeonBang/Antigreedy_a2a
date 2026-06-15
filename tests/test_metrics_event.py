"""Metrics readout: the episode_end event carries fairness metrics (Jain over
delivered/attempted airtime + per-agent shares) so the dashboard can SHOW how
fair the meeting was — the "measure greed vs cooperation" goal (PRD §8)."""
import asyncio
import pathlib
import tempfile

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.events import EventStream
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState
from antigreedy.scenario.meeting import MeetingConfig, run_episode


def _run(policy_dir):
    events: list[dict] = []
    stream = EventStream("t", "c", 0, sink=events.append)
    state = SharedState()
    intercept = InProcessInterceptPoint(PolicyLoader(policy_dir), state)
    cfg = MeetingConfig(run_id="t", condition="c", episode=0,
                        agents=["A", "B", "C", "D"],
                        personas={a: "" for a in "ABCD"},
                        budget=400, max_rounds=4)
    asyncio.run(run_episode(cfg, MockBackend(make_meeting_script(dominator="A")),
                            intercept, stream, state))
    return [e for e in events if e["type"] == "episode_end"][0]["data"]


def test_episode_end_has_fairness_metrics(tmp_path):
    m = _run(tmp_path)["metrics"]   # tmp_path = empty policy dir (ungoverned)
    assert 0.0 <= m["jain_delivered"] <= 1.0
    assert 0.0 <= m["jain_attempted"] <= 1.0
    assert set(m["delivered"]) <= set("ABCD")
    assert "top_share" in m and 0.0 <= m["top_share"] <= 1.0


def test_governance_improves_fairness():
    governed = _run("policies")["metrics"]
    base = _run(pathlib.Path(tempfile.mkdtemp()))["metrics"]
    # the greedy dominator makes the ungoverned run less fair than the governed one
    assert governed["jain_delivered"] >= base["jain_delivered"]
