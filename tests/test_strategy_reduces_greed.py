"""Strategy test cases: adding a governance strategy must REDUCE greed.

Greed here = airtime monopoly: `top_share` (the biggest single agent's share of
delivered airtime, 1.0 = total monopoly) and the inverse of Jain fairness. We run
the SAME greedy meeting (a dominator agent) with 7 agents under three strategies —
none (no policy) → quota → strict — and assert greed goes down as strategy is
added/tightened, and fairness goes up. This is the project thesis, measured.
"""
import asyncio
import tempfile
from pathlib import Path

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.events import EventStream
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState
from antigreedy.scenario.meeting import MeetingConfig, run_episode

AGENTS_7 = list("ABCDEFG")          # 7 agents
STRICT_DIR = Path("policies/presets/strict")


def _metrics(policy_dir, *, agents=AGENTS_7, budget=1400, rounds=6):
    events: list[dict] = []
    stream = EventStream("t", "c", 0, sink=events.append)
    state = SharedState()
    intercept = InProcessInterceptPoint(PolicyLoader(policy_dir), state)
    cfg = MeetingConfig(run_id="t", condition="c", episode=0, agents=list(agents),
                        personas={a: "" for a in agents}, budget=budget, max_rounds=rounds)
    asyncio.run(run_episode(cfg, MockBackend(make_meeting_script(dominator="A")),
                            intercept, stream, state))
    return [e for e in events if e["type"] == "episode_end"][0]["data"]["metrics"]


def test_adding_a_strategy_reduces_greed_with_7_agents():
    none = _metrics(Path(tempfile.mkdtemp()))   # no strategy → greedy baseline
    quota = _metrics("policies")                 # + quota strategy
    strict = _metrics(STRICT_DIR)                # + strict strategy

    # greed (max airtime monopoly) drops once a strategy is added
    assert quota["top_share"] < none["top_share"]
    # ...and fairness rises
    assert quota["jain_delivered"] > none["jain_delivered"]
    # a stricter strategy reduces greed at least as much
    assert strict["top_share"] <= quota["top_share"] + 1e-9
    # baseline really is greedy (dominator takes a large share of a 7-way split)
    assert none["top_share"] > 1.0 / len(AGENTS_7)


def test_governed_share_approaches_fair_split():
    # with a strategy, no single agent should hold a runaway share
    quota = _metrics("policies")
    # fair share for 7 agents is ~0.143; governed top share stays far below monopoly
    assert quota["top_share"] < 0.5
