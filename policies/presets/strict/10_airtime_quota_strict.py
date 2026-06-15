"""Strict airtime quota — a tighter preset of the default quota policy.

Same two rules as policies/10_airtime_quota.py, but a smaller per-turn share and
a sub-1.0 fair-share factor, so governance bites sooner and harder. Used by the
dashboard "Strict" governance preset to show how swapping the governance set
changes agent behavior live.
"""
from antigreedy.governance.policy import Policy

MAX_SHARE_PER_TURN = 0.08      # default is 0.15 — trim turns at half the size
HARD_FLOOR_TOKENS = 30
FAIR_SHARE_FACTOR = 0.6        # default is 1.0 — deny hogs well before an equal share
CHARS_PER_TOKEN = 4


class StrictAirtimeQuotaPolicy(Policy):
    name = "airtime_quota_strict"
    priority = 30

    def evaluate(self, action, state, history):
        if action.action_type != "message":
            return self.allow(reason="not a message")
        remaining = state.commons.get("token_budget_remaining")
        if remaining is None or action.token_estimate <= 0:
            return self.allow(reason="no commons tracked")
        total = state.commons.get("token_budget_total", remaining)
        n = state.commons.get("n_agents") or max(1, len(state.airtime_attempted))
        fair = total / n
        used = state.airtime_delivered.get(action.agent_id, 0)
        if used >= fair * FAIR_SHARE_FACTOR:
            return self.deny(
                reason=f"strict: cumulative share exhausted ({used}>={fair * FAIR_SHARE_FACTOR:.0f})",
                flags={"airtime_greedy": True},
                events=[{"event": "policy_block",
                         "data": {"agent_id": action.agent_id, "rule": self.name,
                                  "used": used, "fair_share": fair}}])
        cap = max(HARD_FLOOR_TOKENS, int(remaining * MAX_SHARE_PER_TURN))
        if action.token_estimate <= cap:
            return self.allow(reason=f"within strict share ({action.token_estimate}<={cap})")
        content = action.payload.get("content", "")
        return self.modify(
            {**action.payload, "content": content[: cap * CHARS_PER_TOKEN], "_truncated": True},
            reason=f"strict airtime greedy: {action.token_estimate}>{cap}, truncated",
            flags={"airtime_greedy": True},
            events=[{"event": "policy_truncate",
                     "data": {"agent_id": action.agent_id, "rule": self.name,
                              "requested": action.token_estimate, "cap": cap}}])
