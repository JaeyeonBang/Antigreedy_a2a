"""Social-psychology strategies must reduce greed too — same test as the quota
strategies, applied to the four social-psych policies (reputation/gossip +
ostracism, universalization, conditional cooperation). 7 agents; greed =
top_share (airtime monopoly), fairness = Jain.
"""
import asyncio
import tempfile
from pathlib import Path

import pytest

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.events import EventStream
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState
from antigreedy.scenario.meeting import MeetingConfig, run_episode

AGENTS_7 = list("ABCDEFG")
SOCIAL = {
    "reputation+ostracism": "policies/presets/social_reputation",
    "universalization": "policies/presets/social_universalization",
    "conditional_cooperation": "policies/presets/social_conditional",
    "social_stack": "policies/presets/social_stack",
}


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


@pytest.fixture(scope="module")
def baseline():
    return _metrics(Path(tempfile.mkdtemp()))   # no strategy → greedy


@pytest.mark.parametrize("name,path", list(SOCIAL.items()))
def test_social_strategy_reduces_greed_7_agents(name, path, baseline):
    m = _metrics(path)
    # adding the social-psych strategy lowers airtime monopoly and raises fairness
    assert m["top_share"] < baseline["top_share"], f"{name}: greed not reduced"
    assert m["jain_delivered"] > baseline["jain_delivered"], f"{name}: fairness not improved"
    # a meaningful reduction (>=15%) vs the ungoverned baseline
    assert m["top_share"] <= baseline["top_share"] * 0.85, \
        f"{name}: greed reduction too small ({m['top_share']} vs {baseline['top_share']})"


def test_reputation_policies_emit_gossip_and_ostracism():
    # the reputation preset broadcasts gossip and ostracises the dominator
    events: list[dict] = []
    stream = EventStream("t", "c", 0, sink=events.append)
    state = SharedState()
    intercept = InProcessInterceptPoint(
        PolicyLoader("policies/presets/social_reputation"), state)
    cfg = MeetingConfig(run_id="t", condition="c", episode=0, agents=AGENTS_7,
                        personas={a: "" for a in AGENTS_7}, budget=1400, max_rounds=6)
    asyncio.run(run_episode(cfg, MockBackend(make_meeting_script(dominator="A")),
                            intercept, stream, state))
    kinds = {e["type"] for e in events}
    assert "gossip" in kinds            # gossip broadcast
    assert "ostracism" in kinds         # the greedy dominator gets ostracised


def test_integrated_stack_runs_all_three_mechanisms():
    # 통합 스택: 배제 + 평판 + 보편화가 한 체인에서 모두 작동
    events: list[dict] = []
    stream = EventStream("t", "c", 0, sink=events.append)
    state = SharedState()
    intercept = InProcessInterceptPoint(PolicyLoader("policies/presets/social_stack"), state)
    cfg = MeetingConfig(run_id="t", condition="c", episode=0, agents=AGENTS_7,
                        personas={a: "" for a in AGENTS_7}, budget=1400, max_rounds=6)
    asyncio.run(run_episode(cfg, MockBackend(make_meeting_script(dominator="A")),
                            intercept, stream, state))
    kinds = {e["type"] for e in events}
    # the three mechanisms each leave a trace
    assert "gossip" in kinds and "ostracism" in kinds
    m = [e for e in events if e["type"] == "episode_end"][0]["data"]["metrics"]
    assert m["top_share"] < 0.4 and m["jain_delivered"] > 0.75   # strongly governed
