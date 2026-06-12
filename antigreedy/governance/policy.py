"""Policy ABC — the single governance extension point (drop-in, hot-reloadable).

Hot-reload contract: policies are re-instantiated on reload; durable state
belongs in SharedState, never on self.
"""
from __future__ import annotations
import abc
from typing import Any
from antigreedy.governance.types import (
    AgentAction, InteractionHistory, PolicyResult, SharedState, Verdict,
)


class Policy(abc.ABC):
    name: str = "unnamed_policy"
    priority: int = 100
    is_hard_gate: bool = False

    @abc.abstractmethod
    def evaluate(self, action: AgentAction, state: SharedState,
                 history: InteractionHistory) -> PolicyResult: ...

    def on_load(self) -> None: ...
    def on_unload(self) -> None: ...

    def allow(self, reason: str = "", **kw: Any) -> PolicyResult:
        return PolicyResult(Verdict.ALLOW, reason=reason, policy_name=self.name, **kw)

    def deny(self, reason: str = "", **kw: Any) -> PolicyResult:
        return PolicyResult(Verdict.DENY, reason=reason, policy_name=self.name, **kw)

    def modify(self, payload: dict, reason: str = "", **kw: Any) -> PolicyResult:
        return PolicyResult(Verdict.MODIFY, modified_payload=payload, reason=reason,
                            policy_name=self.name, **kw)

    def delay(self, seconds: float, reason: str = "", **kw: Any) -> PolicyResult:
        return PolicyResult(Verdict.DELAY, delay_seconds=seconds, reason=reason,
                            policy_name=self.name, **kw)

    def __repr__(self) -> str:
        return f"<Policy {self.name} p={self.priority}>"
