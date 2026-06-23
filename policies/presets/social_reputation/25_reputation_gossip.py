"""사회심리 전략 ① — 간접 상호성 · 가십 · 평판 (Indirect Reciprocity & Gossip).

이론(Nowak & Sigmund 1998; Milinski et al. Nature 2002; ALIGN 2026): 평판은
명시적 처벌 없이 공유지의 비극을 푼다. 목격된 행동을 가십으로 방송 → 분산 평판 형성.

구현: 각 에이전트의 평판을 과거 발언 점유(turn_log)에서 read-only로 파생한다
(단일 기록자 규칙 준수 — 정책은 SharedState를 변경하지 않음). 공정 점유 이하이면
평판 1.0, 초과할수록 하락. 평판이 낮을수록(과거에 발언을 독점) 이번 턴 허용량을
줄인다 = 가십에 의한 점진적 비용 부과. 매 턴 gossip 이벤트를 방송한다.
"""
from antigreedy.governance.policy import Policy
from antigreedy.governance.reputation_calc import linear_reputation as _reputation

BASE_SHARE = 0.22   # 평판 1.0일 때 잔여 커먼즈에서 허용하는 최대 점유
FLOOR = 30
CHARS_PER_TOKEN = 4


class ReputationGossipPolicy(Policy):
    name = "reputation_gossip"
    priority = 25

    def evaluate(self, action, state, history):
        if action.action_type != "message":
            return self.allow(reason="not a message")
        remaining = state.commons.get("token_budget_remaining")
        if remaining is None or action.token_estimate <= 0:
            return self.allow(reason="no commons tracked")
        rep, share = _reputation(action.agent_id, state)
        gossip = [{"event": "gossip", "data": {
            "agent_id": action.agent_id, "reputation": round(rep, 2),
            "share": round(share, 2), "tone": "negative" if rep < 0.6 else "positive"}}]
        cap = max(FLOOR, int(remaining * BASE_SHARE * rep))
        if action.token_estimate <= cap:
            return self.allow(reason=f"평판 {rep:.2f} 양호 (점유 {share:.2f})", events=gossip)
        content = action.payload.get("content", "")
        return self.modify(
            {**action.payload, "content": content[: cap * CHARS_PER_TOKEN], "_truncated": True},
            reason=f"평판 {rep:.2f} 낮음 → {action.token_estimate}>{cap} 축약",
            flags={"airtime_greedy": True, "low_reputation": rep < 0.6}, events=gossip)
