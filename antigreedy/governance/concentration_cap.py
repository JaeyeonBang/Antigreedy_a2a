"""ConcentrationCapPolicy — Phase A of the Identity-DAO design (docs/design_identity_dao.md §3.1).

A per-turn cap on `k * remaining_commons`, weighted by how far the agent has
*over-concentrated* the shared pool. The weight curve is the experimental variable
(Weyl 2017: a vote-pricing rule is robustly optimal iff it is quadratic):

    o = max(0, share - fair) / fair            # normalized over-concentration, share=mine/total
    flat     w = 1                              # ignores history  == dumb cap (control)
    linear   w = max(0, 1 - o)                  # existing gossip rep curve (control)
    quad     w = 1 / (1 + o^2)                  # QV convex congestion pricing  (treatment)
    cap      = max(floor, int(remaining * k * w))

Truncates (MODIFY) anything over the cap, like FractionCapPolicy — so the only
difference across arms is the *curve*, isolating "does the quadratic curve buy us
a better fairness/welfare frontier than a flat or linear cap?" (design §5 Phase A).
"""
from __future__ import annotations

from antigreedy.governance.policy import Policy
from antigreedy.governance.types import AgentAction, InteractionHistory, SharedState

CHARS_PER_TOKEN = 4
_CURVES = ("flat", "linear", "quad")


def _overage(agent_id: str, state: SharedState) -> float:
    """Normalized over-concentration o = max(0, share - fair)/fair from the turn log.
    0 when the agent is at or below its fair share; grows as it monopolizes."""
    log = state.turn_log
    total = sum(d for _, _, d in log)
    if total <= 0:
        return 0.0
    mine = sum(d for a, _, d in log if a == agent_id)
    n = state.commons.get("n_agents") or max(1, len({a for a, _, _ in log}))
    fair = 1.0 / n
    share = mine / total
    return max(0.0, share - fair) / fair if fair > 0 else 0.0


def _weight(curve: str, o: float) -> float:
    if curve == "flat":
        return 1.0
    if curve == "linear":
        return max(0.0, 1.0 - o)
    if curve == "quad":
        return 1.0 / (1.0 + o * o)
    raise ValueError(f"unknown curve {curve!r}; expected one of {_CURVES}")


class ConcentrationCapPolicy(Policy):
    """Concentration-weighted per-turn cap. ``curve`` selects flat / linear / quad."""
    priority = 25

    def __init__(self, curve: str = "quad", k: float = 0.5, floor: int = 30) -> None:
        if curve not in _CURVES:
            raise ValueError(f"unknown curve {curve!r}; expected one of {_CURVES}")
        self.curve = curve
        self.k = k
        self.floor = floor
        self.name = f"concentration_cap_{curve}"

    def evaluate(self, action: AgentAction, state: SharedState,
                 history: InteractionHistory):
        if action.action_type != "message":
            return self.allow(reason="not a message")
        remaining = state.commons.get("token_budget_remaining")
        if remaining is None or action.token_estimate <= 0:
            return self.allow(reason="no commons tracked")
        o = _overage(action.agent_id, state)
        w = _weight(self.curve, o)
        cap = max(self.floor, int(remaining * self.k * w))
        if action.token_estimate <= cap:
            return self.allow(reason=f"{self.curve} cap: {action.token_estimate}<={cap} (o={o:.2f})")
        content = action.payload.get("content", "")
        return self.modify(
            {**action.payload, "content": content[: cap * CHARS_PER_TOKEN], "_truncated": True},
            reason=f"{self.curve} cap o={o:.2f} w={w:.2f}: {action.token_estimate}>{cap}",
            flags={"airtime_greedy": True})
