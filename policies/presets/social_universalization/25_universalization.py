"""사회심리 전략 ⑤ — 보편화 추론 (Universalization, Kant).

이론(GovSim 2024): "모두가 이렇게 행동하면 어떻게 될까?"라는 칸트식 보편화는 인간
협력의 강력한 휴리스틱. GovSim에서 보편화 추론을 주입하자 공유지 지속가능성이 유의하게
향상됐다 — 대부분 모델의 실패 원인인 '내 행동이 그룹 균형에 미치는 장기 효과를 가설화하지
못함'을 정확히 겨냥.

구현: 이번 턴 크기를 n명이 모두 취했을 때 잔여 커먼즈를 초과하면(= 보편화 불가능) 지속
불가능하므로, 보편화 가능한 1/n 몫으로 축약한다. 순수 read-only.
"""
from antigreedy.governance.policy import Policy

FLOOR = 30
CHARS_PER_TOKEN = 4


class UniversalizationPolicy(Policy):
    name = "universalization"
    priority = 25

    def evaluate(self, action, state, history):
        if action.action_type != "message":
            return self.allow(reason="not a message")
        remaining = state.commons.get("token_budget_remaining")
        if remaining is None or action.token_estimate <= 0:
            return self.allow(reason="no commons tracked")
        n = state.commons.get("n_agents") or max(1, len(state.airtime_attempted))
        # 보편화 검사: 모두가 이만큼 쓰면 커먼즈가 버티는가?
        if action.token_estimate * n <= remaining:
            return self.allow(reason=f"보편화 가능 ({action.token_estimate}×{n}≤{remaining})")
        universal_cap = max(FLOOR, remaining // n)
        content = action.payload.get("content", "")
        return self.modify(
            {**action.payload, "content": content[: universal_cap * CHARS_PER_TOKEN],
             "_truncated": True},
            reason=f"보편화 불가 ({action.token_estimate}×{n}>{remaining}) → 1/n 몫 {universal_cap}로 축약",
            flags={"airtime_greedy": True, "unsustainable": True},
            events=[{"event": "universalization", "data": {
                "agent_id": action.agent_id, "requested": action.token_estimate,
                "universal_cap": universal_cap, "n": n}}])
