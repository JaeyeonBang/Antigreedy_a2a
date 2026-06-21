"""사회심리 전략 ② — 비싼 처벌 + 배제 (Ostracism).

이론(Fehr & Gächter 2000; Feinberg et al. 2014): 공공재 게임에서 협력은 처벌 없이
유지되기 어렵다. 금전적 처벌의 '2차 무임승차' 문제를 피하는 저비용 대안이 배제 —
비협력자를 상호작용에서 빼는 것(실험상 순이익까지 증가).

구현: 평판(과거 발언 점유 기반, read-only 파생)이 임계치 미만인 에이전트의 이번 턴을
배제(deny)한다. 배제는 영구가 아니라 자기교정적 — 배제되면 점유가 떨어져 평판이 회복되고
다시 참여가 허용된다. priority 20 으로 평판 캡(25)보다 먼저 실행되어 체인을 단락시킨다.
가십·평판 전략(25_reputation_gossip)과 같은 프리셋에서 결합된다.
"""
from antigreedy.governance.policy import Policy

REP_THRESHOLD = 0.45   # 평판이 이 값 미만이면 배제


def _reputation(agent_id, state):
    log = state.turn_log
    total = sum(d for _, _, d in log)
    if total <= 0:
        return 1.0, 0.0
    mine = sum(d for a, _, d in log if a == agent_id)
    n = state.commons.get("n_agents") or max(1, len({a for a, _, _ in log}))
    fair = 1.0 / n
    share = mine / total
    rep = max(0.1, min(1.0, 1.0 - max(0.0, share - fair) / fair))
    return rep, share


class OstracismPolicy(Policy):
    name = "ostracism"
    priority = 20

    def evaluate(self, action, state, history):
        if action.action_type != "message":
            return self.allow(reason="not a message")
        if not state.turn_log:
            return self.allow(reason="배제 근거 없음 (기록 없음)")
        rep, share = _reputation(action.agent_id, state)
        if rep < REP_THRESHOLD:
            return self.deny(
                reason=f"배제(ostracism) — 평판 {rep:.2f}<{REP_THRESHOLD} (점유 {share:.2f})",
                flags={"ostracized": True, "airtime_greedy": True},
                events=[{"event": "ostracism", "data": {
                    "agent_id": action.agent_id, "reputation": round(rep, 2)}}])
        return self.allow(reason=f"평판 {rep:.2f} — 참여 허용")
