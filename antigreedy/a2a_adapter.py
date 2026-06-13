"""A2A adapter — governance interception at the real a2a-sdk executor boundary.

The a2a-sdk had a breaking 0.3→1.0 change (design §44-45); ALL of its surface is
isolated to this one module so the rest of the codebase never imports it.

``GovernedAgentExecutor`` wraps any inner ``AgentExecutor``. The inner agent's
OUTPUT — its airtime — is captured and routed through the SAME governance
substrate as the in-process loop BEFORE it reaches the EventQueue, i.e. before
any peer sees it (the protocol-native interception claim). The wrapper itself
implements the InterceptPoint contract (eng decision 1: one substrate, two
transports — the shared ``intercept_contract`` suite validates both).

Single-writer rule (eng decision 3): the wrapper governs and gates delivery but
does NOT mutate SharedState — commons charging stays with the orchestrator.
"""
from __future__ import annotations

from a2a.helpers.proto_helpers import get_message_text
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, Part

from antigreedy.backends import rough_tokens
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import AgentAction, PolicyResult, SharedState, Verdict


class _CaptureQueue:
    """Duck-typed EventQueue that buffers events for pre-delivery governance."""
    def __init__(self) -> None:
        self.events: list[object] = []

    def enqueue_event(self, event: object) -> None:
        self.events.append(event)


def _with_text(original: Message, new_text: str) -> Message:
    """A copy of ``original`` carrying ``new_text`` as its sole text part
    (immutability: the incoming proto is never mutated in place)."""
    clone = Message()
    clone.CopyFrom(original)
    del clone.parts[:]
    clone.parts.append(Part(text=new_text))
    return clone


class GovernedAgentExecutor(AgentExecutor):
    """Wrap an inner ``AgentExecutor``; govern its airtime pre-delivery."""

    def __init__(self, inner: AgentExecutor, loader: PolicyLoader,
                 state: SharedState, *, agent_id: str, scenario: str = "") -> None:
        self._inner = inner
        self._ip = InProcessInterceptPoint(loader, state)  # shared governance core
        self.agent_id = agent_id
        self.scenario = scenario

    # --- InterceptPoint contract ------------------------------------------
    async def submit(self, action: AgentAction) -> PolicyResult:
        return await self._ip.submit(action)

    def policy_set_hash(self) -> str:
        return self._ip.policy_set_hash()

    # --- AgentExecutor (A2A-native) ---------------------------------------
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        capture = _CaptureQueue()
        await self._inner.execute(context, capture)
        for event in capture.events:
            await self._forward(event, event_queue)

    async def _forward(self, event: object, event_queue: EventQueue) -> None:
        if not isinstance(event, Message):
            event_queue.enqueue_event(event)  # non-airtime: not governed
            return
        text = get_message_text(event)
        action = AgentAction(agent_id=self.agent_id, action_type="message",
                             payload={"content": text},
                             token_estimate=rough_tokens(text),
                             scenario=self.scenario)
        result = await self.submit(action)
        if result.verdict is Verdict.DENY or result.verdict is Verdict.DELAY:
            return  # gagged / held: nothing reaches peers this turn
        if result.verdict is Verdict.MODIFY and result.modified_payload is not None:
            event = _with_text(event, result.modified_payload.get("content", text))
        event_queue.enqueue_event(event)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await self._inner.cancel(context, event_queue)
