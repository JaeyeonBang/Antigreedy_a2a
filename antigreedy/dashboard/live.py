"""One-touch live governance (T6.6).

A single meeting runs un-paused; the operator applies or removes governance with
one click WHILE it runs. ``LiveInterceptPoint`` holds two intercepts (governed +
empty) and a boolean flip — flipping it changes the verdict on the very next
turn, no restart, no policy-file edit. Single-writer rule holds: only the
orchestrator/control path flips the switch; SharedState is still mutated by the
meeting loop alone.

``PacedTurnSource`` inserts a small delay per turn so a human can actually click
mid-run (the mock backend is otherwise instant).
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from antigreedy.backends import LLMBackend
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import AgentAction, PolicyResult, SharedState
from antigreedy.turnsource import InProcessTurnSource, TurnResult, TurnSource


class LiveInterceptPoint:
    """Switch between governed and ungoverned interception in O(1), live."""

    def __init__(self, governed_loader: PolicyLoader, empty_loader: PolicyLoader,
                 state: SharedState) -> None:
        self._on = InProcessInterceptPoint(governed_loader, state)
        self._off = InProcessInterceptPoint(empty_loader, state)
        self.governance_on = False

    async def submit(self, action: AgentAction) -> PolicyResult:
        return await (self._on if self.governance_on else self._off).submit(action)

    def policy_set_hash(self) -> str:
        return self._on.policy_set_hash()


class PacedTurnSource:
    """Delay each turn by ``delay`` seconds so a human can interact mid-run."""

    def __init__(self, inner: TurnSource, delay: float = 0.0) -> None:
        self._inner = inner
        self._delay = delay

    async def take(self, agent: str, round_no: int, prompt: str) -> TurnResult:
        if self._delay:
            await asyncio.sleep(self._delay)
        return await self._inner.take(agent, round_no, prompt)

    def policy_set_hash(self) -> str:
        return self._inner.policy_set_hash()


def make_live(policies_dir: Path, empty_dir: Path, backend: LLMBackend, *,
              max_tokens: int = 300, delay: float = 0.0
              ) -> tuple[LiveInterceptPoint, PacedTurnSource, SharedState]:
    """Build the live intercept (governance starts OFF), a paced source over it,
    and the SharedState the meeting will own. Caller flips ``lip.governance_on``."""
    state = SharedState()
    lip = LiveInterceptPoint(PolicyLoader(policies_dir), PolicyLoader(empty_dir), state)
    src = PacedTurnSource(InProcessTurnSource(backend, lip, max_tokens=max_tokens), delay)
    return lip, src, state
