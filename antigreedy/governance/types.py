"""Core value objects for the governance layer (dependency-free)."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Verdict(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    MODIFY = "modify"
    DELAY = "delay"


@dataclass(frozen=True)
class AgentAction:
    """An action an agent is attempting (most often: speaking a turn).

    ``token_estimate`` is the ATTEMPTED size (tokens the agent tried to use).
    Delivered size is decided post-verdict by the charging rule (eng decision 8:
    attempted vs delivered are recorded separately).
    """
    agent_id: str
    action_type: str = "message"
    payload: dict[str, Any] = field(default_factory=dict)
    token_estimate: int = 0
    scenario: str = ""
    round: int = 0
    target_agent_id: str | None = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class PolicyResult:
    verdict: Verdict = Verdict.ALLOW
    modified_payload: dict[str, Any] | None = None
    delay_seconds: float = 0.0
    reason: str = ""
    policy_name: str = ""
    flags: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SharedState:
    """Mutable world state. Lives OUTSIDE policy instances so hot-reload never
    drops bookkeeping. Single-writer rule (eng decision 3): only the episode
    orchestrator mutates this."""
    commons: dict[str, Any] = field(default_factory=dict)
    airtime_delivered: dict[str, int] = field(default_factory=dict)
    airtime_attempted: dict[str, int] = field(default_factory=dict)
    turn_log: list[tuple[str, int, int]] = field(default_factory=list)  # (agent, attempted, delivered)
    reputation: dict[str, float] = field(default_factory=dict)
    payoff: dict[str, float] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def record_turn(self, agent_id: str, attempted: int, delivered: int) -> None:
        self.airtime_attempted[agent_id] = self.airtime_attempted.get(agent_id, 0) + attempted
        self.airtime_delivered[agent_id] = self.airtime_delivered.get(agent_id, 0) + delivered
        self.turn_log.append((agent_id, attempted, delivered))
        if "token_budget_remaining" in self.commons:
            self.commons["token_budget_remaining"] -= delivered


InteractionHistory = list[tuple[AgentAction, PolicyResult]]
