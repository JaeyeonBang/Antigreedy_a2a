"""Output/prompt visibility: turn events must carry the actual conversation —
the prompt sent to the agent, the agent's original text, and the delivered text
post-governance — so the dashboard can show "what each agent said" and "what
governance did to it" (PRD §2 visualize conversations, §6 FR4)."""
import asyncio

from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.events import EventStream
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState
from antigreedy.scenario.meeting import MeetingConfig, run_episode

REPO_POLICIES = "policies"


def _run_governed():
    events: list[dict] = []
    stream = EventStream("t", "governed", 0, sink=events.append)
    state = SharedState()
    intercept = InProcessInterceptPoint(PolicyLoader(REPO_POLICIES), state)
    cfg = MeetingConfig(run_id="t", condition="governed", episode=0,
                        agents=["A", "B", "C", "D"],
                        personas={a: "" for a in "ABCD"},
                        budget=400, max_rounds=4)
    asyncio.run(run_episode(cfg, MockBackend(make_meeting_script(dominator="A")),
                            intercept, stream, state))
    return [e for e in events if e["type"] == "turn"]


def test_turn_events_carry_prompt_and_text():
    turns = _run_governed()
    assert turns
    # every turn exposes the three conversation fields
    for t in turns:
        d = t["data"]
        assert "prompt" in d and "original_text" in d and "delivered_text" in d
    # the prompt actually reaches the agent (non-empty for real turns)
    assert any(t["data"]["prompt"] for t in turns)
    # the prompt is the structured meeting prompt the agent sees
    assert any("SHARED TOKEN BUDGET" in t["data"]["prompt"] for t in turns)


def test_governance_visibly_changes_text():
    turns = _run_governed()
    # the greedy dominator A is truncated/denied → original differs from delivered
    a_changed = [t for t in turns if t["data"]["agent_id"] == "A"
                 and t["data"]["original_text"] != t["data"]["delivered_text"]]
    assert a_changed, "expected at least one governed A turn where text was changed"
    # a denied turn delivers nothing while its original was non-empty
    denied = [t for t in turns if t["data"]["verdict"] == "deny"]
    if denied:
        assert denied[0]["data"]["delivered_text"] == ""
        assert denied[0]["data"]["original_text"]


def test_text_is_length_capped():
    # payload stays bounded even if an agent rambles
    for t in _run_governed():
        assert len(t["data"]["prompt"]) <= 4000
        assert len(t["data"]["original_text"]) <= 4000
        assert len(t["data"]["delivered_text"]) <= 4000
