"""Null-model control for the cap-equivalent ablation (external review #1).

The review's central concern: the 'social' policies (reputation, universalization,
conditional) may be nothing more than per-turn token caps with fancy names. To
test that, we compare them against a DUMB cap — `cap = k * remaining` with NO
social logic (no reputation, no history, no peer-awareness) — swept over k. If a
plain cap reproduces a social policy's top_share / fairness / completion, the
social mechanism added nothing beyond the arithmetic.
"""
from __future__ import annotations

from antigreedy.governance.chain import PolicyChain
from antigreedy.governance.intercept import InProcessInterceptPoint
from antigreedy.governance.policy import Policy
from antigreedy.governance.types import SharedState

CHARS_PER_TOKEN = 4


class FractionCapPolicy(Policy):
    """A dumb per-turn cap = max(floor, k * remaining_commons). Truncates anything
    larger. No reputation, no gossip, no peer-averaging — pure arithmetic."""
    priority = 25

    def __init__(self, k: float = 0.2, floor: int = 30) -> None:
        self.k = k
        self.floor = floor
        self.name = f"fraction_cap_{int(round(k * 100))}"

    def evaluate(self, action, state, history):
        if action.action_type != "message":
            return self.allow(reason="not a message")
        remaining = state.commons.get("token_budget_remaining")
        if remaining is None or action.token_estimate <= 0:
            return self.allow(reason="no commons tracked")
        cap = max(self.floor, int(remaining * self.k))
        if action.token_estimate <= cap:
            return self.allow(reason=f"within k={self.k} cap ({action.token_estimate}<={cap})")
        content = action.payload.get("content", "")
        return self.modify(
            {**action.payload, "content": content[: cap * CHARS_PER_TOKEN], "_truncated": True},
            reason=f"dumb cap k={self.k}: {action.token_estimate}>{cap}",
            flags={"airtime_greedy": True})


class _ChainLoader:
    """Minimal loader-shim so a list of Policy INSTANCES can drive an
    InProcessInterceptPoint without writing files (for ablation sweeps)."""
    def __init__(self, policies: list[Policy]) -> None:
        self._policies = policies

    @property
    def chain(self) -> PolicyChain:
        return PolicyChain(self._policies)

    def policy_set_hash(self) -> str:
        return "ablation:" + ",".join(p.name for p in self._policies)


def chain_intercept(policies: list[Policy], state: SharedState) -> InProcessInterceptPoint:
    """Build an InterceptPoint from in-memory Policy instances (ablation helper)."""
    return InProcessInterceptPoint(_ChainLoader(policies), state)
