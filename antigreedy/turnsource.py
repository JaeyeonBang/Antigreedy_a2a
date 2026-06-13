"""TurnSource — the per-turn execution seam (T5 Phase 1).

The meeting orchestrator (``scenario.meeting.run_meeting``) owns the round loop,
DECISION/exhaustion logic, commons charging, and event emission. HOW a single
turn is produced and governed is delegated to a ``TurnSource``:

  - ``InProcessTurnSource`` runs backend + governance in this process (the
    original meeting logic, extracted verbatim);
  - the A2A path (Phase 3) routes the turn to a governed agent server.

Both return a transport-agnostic ``TurnResult`` so ONE orchestrator drives both.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from antigreedy.backends import LLMBackend
from antigreedy.governance.intercept import InterceptPoint
from antigreedy.governance.types import AgentAction, Verdict
from antigreedy.protocol import parse_turn


@dataclass
class TurnResult:
    """Everything the orchestrator needs to charge, transcribe, and emit a turn,
    independent of the transport that produced it."""
    delivered_text: str           # post-verdict text to broadcast/charge ("" if dropped/held)
    original_text: str            # untruncated speak (delay re-delivery keeps this)
    attempted_tokens: int
    agree: bool
    bid: bool
    parse_ok: bool
    verdict: Verdict
    policy_name: str = ""
    reason: str = ""
    flags: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)  # policy events to emit


class TurnSource(Protocol):
    async def take(self, agent: str, round_no: int, prompt: str) -> TurnResult: ...
    def policy_set_hash(self) -> str: ...


class InProcessTurnSource:
    """Single-process turn execution: backend.complete → parse → intercept.submit
    → apply verdict. Extracted unchanged from the original meeting loop."""

    def __init__(self, backend: LLMBackend, intercept: InterceptPoint, *,
                 max_tokens: int = 300, scenario: str = "meeting") -> None:
        self._backend = backend
        self._intercept = intercept
        self._max_tokens = max_tokens
        self._scenario = scenario

    async def take(self, agent: str, round_no: int, prompt: str) -> TurnResult:
        result = await self._backend.complete(prompt, self._max_tokens)
        attempted = int(result["completion_tokens"])
        turn = parse_turn(result["text"])
        action = AgentAction(agent_id=agent, action_type="message",
                             payload={"content": turn.speak}, token_estimate=attempted,
                             scenario=self._scenario, round=round_no)
        pr = await self._intercept.submit(action)
        delivered_text = turn.speak
        if pr.verdict == Verdict.DENY or pr.verdict == Verdict.DELAY:
            delivered_text = ""
        elif pr.verdict == Verdict.MODIFY and pr.modified_payload is not None:
            delivered_text = pr.modified_payload.get("content", "")
        return TurnResult(
            delivered_text=delivered_text, original_text=turn.speak,
            attempted_tokens=attempted, agree=turn.agree, bid=turn.bid,
            parse_ok=turn.parse_ok, verdict=pr.verdict, policy_name=pr.policy_name,
            reason=pr.reason, flags=pr.flags, events=pr.events)

    def policy_set_hash(self) -> str:
        return self._intercept.policy_set_hash()
