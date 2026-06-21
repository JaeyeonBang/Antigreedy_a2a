"""사회심리 전략 ⑥ — 조건부 협력 (Conditional Cooperation, tit-for-tat).

이론(Fischbacher, Gächter, Fehr 2001): 사람의 다수는 조건부 협력자 — 남이 협력하면
협력한다. 초기 신뢰 시드(소수 협력자)가 협력 캐스케이드를 점화한다.

구현: 이번 턴 허용량을 '다른 에이전트들의 최근 발언 평균'에 맞춘다 — 동료가 절제하면 나도
절제. 동료 평균보다 크게 쓰려는 무임승차자는 동료 수준으로 축약(미러링). 첫 턴(동료 기록
없음)은 협력을 시드한다. 순수 read-only(turn_log 파생).
"""
from antigreedy.governance.policy import Policy

FLOOR = 30
TOLERANCE = 1.25   # 동료 평균의 1.25배까지 허용
CHARS_PER_TOKEN = 4


class ConditionalCooperationPolicy(Policy):
    name = "conditional_cooperation"
    priority = 25

    def evaluate(self, action, state, history):
        if action.action_type != "message":
            return self.allow(reason="not a message")
        if action.token_estimate <= 0:
            return self.allow(reason="no tokens")
        others = [d for a, _, d in state.turn_log if a != action.agent_id and d > 0]
        if not others:
            return self.allow(reason="협력 시드 (동료 기록 없음)")
        peer_avg = sum(others) / len(others)
        cap = max(FLOOR, int(peer_avg * TOLERANCE))
        if action.token_estimate <= cap:
            return self.allow(reason=f"동료 평균 {peer_avg:.0f} 수준 협력 ({action.token_estimate}≤{cap})")
        content = action.payload.get("content", "")
        return self.modify(
            {**action.payload, "content": content[: cap * CHARS_PER_TOKEN], "_truncated": True},
            reason=f"무임승차 — 동료 평균 {peer_avg:.0f} 초과 → {cap}로 미러링",
            flags={"airtime_greedy": True, "free_riding": True},
            events=[{"event": "conditional_cap", "data": {
                "agent_id": action.agent_id, "peer_avg": round(peer_avg, 1), "cap": cap}}])
