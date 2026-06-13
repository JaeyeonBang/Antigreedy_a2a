"""Meeting over A2A (T5 Phases 2-3): a governed agent server reports its turn as
an A2A Message (delivered SPEAK in the part, control fields in metadata), an
in-process transport routes it, and A2ATurnSource decodes it back into a
TurnResult so the SAME run_meeting orchestrator drives the meeting over A2A.

Key parity property: governance affects only the airtime (SPEAK); AGREE/BID
survive every verdict — a gagged (DENY) agent still reports its vote, exactly
as the in-process loop does.
"""
import asyncio
import tempfile
from pathlib import Path

from antigreedy.a2a_meeting import (
    make_a2a_turn_source, message_to_turn, turn_to_message,
)
from antigreedy.backends import MockBackend, make_meeting_script
from antigreedy.events import EventStream
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState, Verdict
from antigreedy.metrics import episode_summary
from antigreedy.protocol import build_prompt
from antigreedy.scenario.meeting import MeetingConfig, run_meeting
from antigreedy.turnsource import TurnResult

REPO_POLICIES = Path(__file__).resolve().parent.parent / "policies"
TOPIC = "Allocate the shared compute budget."


def _tr(**kw):
    base = dict(delivered_text="hello", original_text="hello world",
                attempted_tokens=12, agree=True, bid=False, parse_ok=True,
                verdict=Verdict.MODIFY, policy_name="chain", reason="trunc",
                flags={"airtime_greedy": True}, events=[])
    base.update(kw)
    return TurnResult(**base)


# --- Phase 2: codec ---------------------------------------------------------
def test_codec_roundtrip_preserves_turn():
    tr = _tr()
    out = message_to_turn(turn_to_message(tr))
    assert out.delivered_text == tr.delivered_text
    assert out.original_text == tr.original_text
    assert out.attempted_tokens == tr.attempted_tokens
    assert out.agree is True and out.bid is False and out.parse_ok is True
    assert out.verdict is Verdict.MODIFY
    assert out.policy_name == "chain"
    assert out.flags.get("airtime_greedy") is True


def test_codec_empty_delivery_roundtrips():
    out = message_to_turn(turn_to_message(_tr(delivered_text="", verdict=Verdict.DENY)))
    assert out.delivered_text == ""
    assert out.verdict is Verdict.DENY
    assert out.agree is True  # vote survives a gag


# --- Phase 3: transport + A2ATurnSource -------------------------------------
def _a2a_source(policy_dir, state, dominator="A", agents=("A", "B", "C", "D")):
    backend = MockBackend(make_meeting_script(dominator=dominator))
    return make_a2a_turn_source(list(agents), backend, PolicyLoader(policy_dir), state)


def _take(source, agent, round_no=0, budget=400):
    prompt = build_prompt(agent, "", TOPIC, "", round_no, budget)
    return asyncio.run(source.take(agent, round_no, prompt))


def test_a2a_turnsource_modify_truncates_over_transport():
    state = SharedState()
    state.commons.update(token_budget_remaining=400, token_budget_total=400, n_agents=4)
    tr = _take(_a2a_source(REPO_POLICIES, state), "A")
    assert isinstance(tr, TurnResult)
    assert tr.verdict is Verdict.MODIFY
    assert 0 < len(tr.delivered_text) < len(tr.original_text)


def test_a2a_deny_still_reports_vote():
    with tempfile.TemporaryDirectory() as td:
        pol = Path(td)
        (pol / "deny_a.py").write_text(
            "from antigreedy.governance.policy import Policy\n"
            "class D(Policy):\n"
            "    name, priority = 'deny_a', 5\n"
            "    def evaluate(self, a, s, h):\n"
            "        return self.deny() if a.agent_id=='A' else self.allow()\n")
        tr = _take(_a2a_source(pol, SharedState(), dominator=None), "A", round_no=3)
        assert tr.verdict is Verdict.DENY
        assert tr.delivered_text == ""
        assert tr.agree is True  # gagged agent's AGREE: yes still reported


def test_policy_set_hash_exposed():
    src = _a2a_source(REPO_POLICIES, SharedState())
    assert isinstance(src.policy_set_hash(), str) and len(src.policy_set_hash()) >= 8


def test_agent_cancel_is_noop():
    from antigreedy.a2a_meeting import MeetingAgentExecutor
    ge = MeetingAgentExecutor("A", _a2a_source(REPO_POLICIES, SharedState()))
    assert asyncio.run(ge.cancel(None, None)) is None


def test_transport_raises_when_no_message():
    import pytest
    from a2a.server.agent_execution import AgentExecutor
    from a2a.types import SendMessageRequest, Message, Part, Role
    from antigreedy.a2a_meeting import InProcessTransport

    class _Silent(AgentExecutor):
        async def execute(self, context, event_queue):
            pass  # emits nothing

        async def cancel(self, context, event_queue):
            pass

    req = SendMessageRequest(message=Message(
        message_id="r", role=Role.ROLE_USER, parts=[Part(text="hi")]))
    with pytest.raises(RuntimeError, match="no message"):
        asyncio.run(InProcessTransport({"A": _Silent()}).send("A", req))


# --- Phase 3: full meeting over A2A == in-process behavior ------------------
def _run_a2a(policy_dir, state, budget=400, max_rounds=4, dominator="A"):
    src = _a2a_source(policy_dir, state, dominator=dominator)
    stream = EventStream("t", "governed", 0)
    cfg = MeetingConfig(run_id="t", condition="governed", episode=0,
                        personas={a: "" for a in "ABCD"}, budget=budget,
                        max_rounds=max_rounds)
    out = asyncio.run(run_meeting(cfg, src, stream, state))
    return out, stream.events


def test_a2a_governed_truncates_dominator():
    _, events = _run_a2a(REPO_POLICIES, SharedState(), budget=400)
    s = episode_summary(events)
    assert s["delivered"]["A"] < s["attempted"]["A"] * 0.6  # dominator truncated


def test_a2a_baseline_collapses(tmp_path):
    d = tmp_path / "empty"; d.mkdir()
    out, _ = _run_a2a(d, SharedState(), budget=150, max_rounds=8, dominator="A")
    assert out["outcome"] == "exhausted"
