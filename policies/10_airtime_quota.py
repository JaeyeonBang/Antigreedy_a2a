"""Airtime-commons quota v2 — the count-based governance policy.

Two rules on one intercept point:
  (1) per-turn cap: one turn may use at most MAX_SHARE_PER_TURN of the REMAINING
      commons (greedy turns are truncated, not denied);
  (2) cumulative fair-share cap: once an agent's DELIVERED airtime exceeds
      FAIR_SHARE_FACTOR x (total_budget / n_agents), further turns are denied —
      monopolization by many medium turns is caught too.

Tunables hot-reload on save (req. ③): edit and watch behavior change live.
"""
from antigreedy.governance.policy import Policy

MAX_SHARE_PER_TURN = 0.15
HARD_FLOOR_TOKENS = 40
FAIR_SHARE_FACTOR = 1.0
CHARS_PER_TOKEN = 4


class AirtimeQuotaPolicy(Policy):
    name = "airtime_quota"
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
                reason=f"cumulative share exhausted ({used}>={fair * FAIR_SHARE_FACTOR:.0f})",
                flags={"airtime_greedy": True},
                events=[{"event": "policy_block",
                         "data": {"agent_id": action.agent_id, "rule": self.name,
                                  "used": used, "fair_share": fair}}])
        cap = max(HARD_FLOOR_TOKENS, int(remaining * MAX_SHARE_PER_TURN))
        if action.token_estimate <= cap:
            return self.allow(reason=f"within share ({action.token_estimate}<={cap})")
        content = action.payload.get("content", "")
        return self.modify(
            {**action.payload, "content": content[: cap * CHARS_PER_TOKEN], "_truncated": True},
            reason=f"airtime greedy: {action.token_estimate}>{cap}, truncated",
            flags={"airtime_greedy": True},
            events=[{"event": "policy_truncate",
                     "data": {"agent_id": action.agent_id, "rule": self.name,
                              "requested": action.token_estimate, "cap": cap}}])
