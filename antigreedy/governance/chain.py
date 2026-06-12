"""PolicyChain — priority order; DENY/DELAY short-circuit; MODIFY propagates;
flags/events accumulate across the chain (detection without blocking)."""
from __future__ import annotations
from dataclasses import replace
from antigreedy.governance.policy import Policy
from antigreedy.governance.types import (
    AgentAction, InteractionHistory, PolicyResult, SharedState, Verdict,
)


class PolicyChain:
    def __init__(self, policies: list[Policy]) -> None:
        self.policies = sorted(policies, key=lambda p: p.priority)

    def evaluate(self, action: AgentAction, state: SharedState,
                 history: InteractionHistory | None = None) -> PolicyResult:
        history = history if history is not None else []
        current = action
        flags: dict = {}
        events: list = []
        for policy in self.policies:
            r = policy.evaluate(current, state, history)
            flags.update(r.flags)
            events.extend(r.events)
            if r.verdict in (Verdict.DENY, Verdict.DELAY):
                r.flags, r.events = flags, events
                return r
            if r.verdict == Verdict.MODIFY and r.modified_payload is not None:
                current = replace(current, payload=r.modified_payload)
        changed = current.payload != action.payload
        return PolicyResult(
            verdict=Verdict.MODIFY if changed else Verdict.ALLOW,
            modified_payload=current.payload if changed else None,
            reason="chain pass", policy_name="chain", flags=flags, events=events)
