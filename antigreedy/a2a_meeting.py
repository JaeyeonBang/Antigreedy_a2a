"""Meeting-over-A2A wiring (T5 Phases 2-3).

A governed agent runs server-side as an a2a ``AgentExecutor``: it produces its
turn through the shared governance substrate (``InProcessTurnSource``) and
REPORTS the result as one A2A ``Message`` — delivered SPEAK in the message part,
control fields (agree/bid/attempted/verdict/…) in ``metadata``. Governance is
therefore protocol-native (it happens at the executor boundary, before the turn
is serialized into the A2A response), yet AGREE/BID survive every verdict — a
gagged DENY turn still reports its vote, matching the in-process loop exactly.

The orchestrator stays the single writer: ``A2ATurnSource`` only transports and
decodes; ``run_meeting`` charges the commons. All a2a-sdk surface is confined to
this module and ``a2a_adapter`` (the SDK had a breaking 0.3→1.0 change).
"""
from __future__ import annotations

import inspect
from typing import Protocol

from a2a.helpers.proto_helpers import get_message_text
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, Part, Role, SendMessageRequest

from antigreedy.backends import LLMBackend
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import SharedState, Verdict
from antigreedy.turnsource import InProcessTurnSource, TurnResult, TurnSource


# --- TurnResult <-> A2A Message codec --------------------------------------
def turn_to_message(tr: TurnResult) -> Message:
    """Encode a governed turn: delivered SPEAK in the part, control in metadata."""
    parts = [Part(text=tr.delivered_text)] if tr.delivered_text else []
    msg = Message(message_id="turn", role=Role.ROLE_AGENT, parts=parts)
    msg.metadata.update({
        "original_text": tr.original_text,
        "attempted_tokens": tr.attempted_tokens,
        "agree": tr.agree, "bid": tr.bid, "parse_ok": tr.parse_ok,
        "verdict": tr.verdict.value, "policy_name": tr.policy_name,
        "reason": tr.reason, "flags": dict(tr.flags),
    })
    return msg


def message_to_turn(msg: Message) -> TurnResult:
    md = msg.metadata
    return TurnResult(
        delivered_text=get_message_text(msg),
        original_text=str(md["original_text"]),
        attempted_tokens=int(md["attempted_tokens"]),
        agree=bool(md["agree"]), bid=bool(md["bid"]), parse_ok=bool(md["parse_ok"]),
        verdict=Verdict(str(md["verdict"])),
        policy_name=str(md["policy_name"]), reason=str(md["reason"]),
        flags={k: bool(v) for k, v in dict(md["flags"]).items()})


# --- Agent server-side executor --------------------------------------------
class MeetingAgentExecutor(AgentExecutor):
    """One meeting participant as an A2A agent. Reads the prompt from the request,
    produces a governed turn via the shared source, reports it as a Message."""

    def __init__(self, agent_id: str, source: TurnSource) -> None:
        self.agent_id = agent_id
        self._source = source

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        prompt = context.get_user_input()
        round_no = 0
        msg = context.message
        if msg is not None and "round" in msg.metadata:
            round_no = int(msg.metadata["round"])
        tr = await self._source.take(self.agent_id, round_no, prompt)
        # The real a2a EventQueue.enqueue_event is a coroutine; the in-process
        # transport's queue is sync. Support both.
        maybe = event_queue.enqueue_event(turn_to_message(tr))
        if inspect.isawaitable(maybe):
            await maybe

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        return None  # meeting turns are one-shot; nothing to cancel


# --- transport seam ---------------------------------------------------------
class AgentTransport(Protocol):
    async def send(self, agent_id: str, request: SendMessageRequest) -> Message: ...


class _CaptureQueue:
    def __init__(self) -> None:
        self.events: list[object] = []

    def enqueue_event(self, event: object) -> None:
        self.events.append(event)


class InProcessTransport:
    """Routes turn requests by invoking the agent executor directly (no socket),
    exercising the real a2a RequestContext/Message path. The HTTP transport
    (Phase 4) is a drop-in replacement implementing the same AgentTransport."""

    def __init__(self, registry: dict[str, AgentExecutor]) -> None:
        self._registry = registry

    async def send(self, agent_id: str, request: SendMessageRequest) -> Message:
        executor = self._registry[agent_id]
        cap = _CaptureQueue()
        await executor.execute(RequestContext(call_context=None, request=request), cap)
        for ev in cap.events:
            if isinstance(ev, Message):
                return ev
        raise RuntimeError(f"agent {agent_id!r} produced no message")


# --- client-side TurnSource over A2A ----------------------------------------
class A2ATurnSource:
    """A TurnSource that routes each turn to a governed agent over an
    AgentTransport and decodes the reported Message back into a TurnResult."""

    def __init__(self, transport: AgentTransport, policy_set_hash: str) -> None:
        self._transport = transport
        self._psh = policy_set_hash

    async def take(self, agent: str, round_no: int, prompt: str) -> TurnResult:
        req = SendMessageRequest(message=Message(
            message_id=f"req-{agent}-{round_no}", role=Role.ROLE_USER,
            parts=[Part(text=prompt)]))
        req.message.metadata.update({"round": round_no})
        msg = await self._transport.send(agent, req)
        return message_to_turn(msg)

    def policy_set_hash(self) -> str:
        return self._psh


def make_a2a_turn_source(agents: list[str], backend: LLMBackend,
                         loader: PolicyLoader, state: SharedState, *,
                         max_tokens: int = 300) -> A2ATurnSource:
    """Wire N agent servers (sharing ONE intercept → one history/state, parity
    with the in-process loop) behind an in-process transport."""
    intercept = InProcessInterceptPoint(loader, state)
    source = InProcessTurnSource(backend, intercept, max_tokens=max_tokens)
    registry: dict[str, AgentExecutor] = {
        a: MeetingAgentExecutor(a, source) for a in agents}
    return A2ATurnSource(InProcessTransport(registry), intercept.policy_set_hash())
