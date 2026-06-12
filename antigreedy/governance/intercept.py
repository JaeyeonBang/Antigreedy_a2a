"""InterceptPoint — the transport-agnostic interception contract (eng decision 1).

Both the in-process scenario loop and the A2A executor wrapper implement this;
ONE contract test suite validates both, so gate results transfer to the full
testbed. This file carries the project's core claim: one substrate, many
heterogeneous policies.
"""
from __future__ import annotations
from typing import Protocol

from antigreedy.governance.loader import PolicyLoader
from antigreedy.governance.types import (
    AgentAction, InteractionHistory, PolicyResult, SharedState,
)


class InterceptPoint(Protocol):
    """submit() runs the action through governance and returns the verdict."""
    async def submit(self, action: AgentAction) -> PolicyResult: ...
    def policy_set_hash(self) -> str: ...


class InProcessInterceptPoint:
    """InterceptPoint for the single-process scenario loop (A-gate spike)."""

    def __init__(self, loader: PolicyLoader, state: SharedState) -> None:
        self._loader = loader
        self._state = state
        self._history: InteractionHistory = []

    async def submit(self, action: AgentAction) -> PolicyResult:
        result = self._loader.chain.evaluate(action, self._state, self._history)
        self._history.append((action, result))
        return result

    def policy_set_hash(self) -> str:
        return self._loader.policy_set_hash()
