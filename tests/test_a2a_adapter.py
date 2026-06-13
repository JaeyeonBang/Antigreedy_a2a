"""A2A interception checkpoint (T5, design §5): the a2a-sdk executor is
wrappable and the agent's OUTPUT (airtime) is governed PRE-DELIVERY — before it
reaches the EventQueue (i.e. before peers see it). The SAME InterceptPoint
contract suite that validates the in-process loop validates the A2A wrapper
(eng decision 1: one substrate, two transports).
"""
import asyncio
from pathlib import Path

from a2a.helpers.proto_helpers import get_message_text
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.types import Message, Part, Role, SendMessageRequest, Task

from antigreedy.a2a_adapter import GovernedAgentExecutor
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState
from tests.test_intercept_meeting import intercept_contract

REPO_POLICIES = Path(__file__).resolve().parent.parent / "policies"


# --- test doubles -----------------------------------------------------------
class _RecordingQueue:
    """Duck-typed EventQueue: records what would reach peers."""
    def __init__(self):
        self.events = []

    def enqueue_event(self, event):
        self.events.append(event)


class _FakeInner(AgentExecutor):
    """An A2A agent that emits a single text turn of the given content."""
    def __init__(self, *events):
        self._events = events

    async def execute(self, context, event_queue):
        for ev in self._events:
            event_queue.enqueue_event(ev)

    async def cancel(self, context, event_queue):
        event_queue.enqueue_event(Message(
            message_id="cancelled", role=Role.ROLE_AGENT,
            parts=[Part(text="cancelled")]))


def _agent_msg(text):
    return Message(message_id="out", role=Role.ROLE_AGENT, parts=[Part(text=text)])


def _ctx(text="hi"):
    req = SendMessageRequest(message=Message(
        message_id="in", role=Role.ROLE_USER, parts=[Part(text=text)]))
    return RequestContext(call_context=None, request=req)


def _govern(inner, policy_dir, state, agent_id="A"):
    return GovernedAgentExecutor(inner, PolicyLoader(policy_dir), state,
                                 agent_id=agent_id)


def _run(executor, ctx=None):
    q = _RecordingQueue()
    asyncio.run(executor.execute(ctx or _ctx(), q))
    return q.events


# --- contract suite: the A2A wrapper IS an InterceptPoint -------------------
def test_a2a_executor_satisfies_intercept_contract():
    def mk():
        state = SharedState(commons={"token_budget_remaining": 1000})
        ge = _govern(_FakeInner(_agent_msg("x")), REPO_POLICIES, state)
        return ge, state
    intercept_contract(mk)


# --- executor-wrap interception: verdict gates delivery ---------------------
def test_allow_delivers_full_output(tmp_path):
    d = tmp_path / "empty"; d.mkdir()
    events = _run(_govern(_FakeInner(_agent_msg("converge and decide")), d,
                          SharedState()))
    assert len(events) == 1
    assert get_message_text(events[0]) == "converge and decide"


def test_deny_drops_output_pre_delivery(tmp_path):
    d = tmp_path / "pol"; d.mkdir()
    (d / "deny_a.py").write_text(
        "from antigreedy.governance.policy import Policy\n"
        "class D(Policy):\n"
        "    name, priority = 'deny_dom', 5\n"
        "    def evaluate(self, a, s, h):\n"
        "        return self.deny(reason='gag') if a.agent_id=='A' else self.allow()\n")
    events = _run(_govern(_FakeInner(_agent_msg("I will monopolize " * 50)), d,
                          SharedState(), agent_id="A"))
    assert events == []  # nothing reached the queue → peers never saw it


def test_modify_truncates_output(tmp_path):
    state = SharedState()
    state.commons.update(token_budget_remaining=400, token_budget_total=400,
                         n_agents=4)
    big = "I must elaborate at great length on my proposal. " * 50
    events = _run(_govern(_FakeInner(_agent_msg(big)), REPO_POLICIES, state,
                          agent_id="A"))
    assert len(events) == 1
    out = get_message_text(events[0])
    assert 0 < len(out) < len(big)  # truncated, not dropped


def test_non_message_event_passes_through_ungoverned(tmp_path):
    d = tmp_path / "pol"; d.mkdir()
    (d / "deny_all.py").write_text(
        "from antigreedy.governance.policy import Policy\n"
        "class D(Policy):\n"
        "    name, priority = 'deny_all', 5\n"
        "    def evaluate(self, a, s, h):\n"
        "        return self.deny(reason='gag')\n")
    task = Task(id="t1", context_id="c1")
    events = _run(_govern(_FakeInner(task), d, SharedState()))
    assert events == [task]  # non-airtime events are not governed


def test_multiple_turns_each_governed(tmp_path):
    d = tmp_path / "pol"; d.mkdir()
    (d / "deny_a.py").write_text(
        "from antigreedy.governance.policy import Policy\n"
        "class D(Policy):\n"
        "    name, priority = 'deny_a', 5\n"
        "    def evaluate(self, a, s, h):\n"
        "        return self.deny() if a.agent_id=='A' else self.allow()\n")
    inner = _FakeInner(_agent_msg("one"), _agent_msg("two"))
    events = _run(_govern(inner, d, SharedState(), agent_id="A"))
    assert events == []  # both turns from A are gagged


def test_cancel_delegates_to_inner(tmp_path):
    d = tmp_path / "empty"; d.mkdir()
    ge = _govern(_FakeInner(), d, SharedState())
    q = _RecordingQueue()
    asyncio.run(ge.cancel(_ctx(), q))
    assert len(q.events) == 1
    assert get_message_text(q.events[0]) == "cancelled"
