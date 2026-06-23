"""BetaOstracismPolicy (Phase 1) — Beta+λ 평판으로 구동되는 배제 + 평판 캡.

기존 ``OstracismPolicy``(배제)와 ``ReputationGossipPolicy``(캡)는 *영구 누적* 선형 평판
(``linear_reputation``)으로 구동된다 — 한 번 과점하면 누적 점유가 끈질겨 회복이 어렵다(카스트화).
이 정책은 같은 두 작용(배제 deny + 평판비례 캡)을 **망각계수 λ의 Beta 평판**으로 구동한다.
λ=1이면 망각 없음(현행과 유사한 고착), λ<1이면 최근 행동이 지배해 *자기교정*이 가능하다.

단일 정책에 배제와 캡을 합쳐(체인 길이 1로) arm을 단순화한다:
  rep < thresh  → DENY (배제; 자기교정적 — 배제되면 점유가 멎어 λ<1에서 평판 회복)
  rep ≥ thresh  → BASE_SHARE·rep 캡, 초과분 MODIFY(축약)

read-only(단일 기록자 규칙): SharedState를 변경하지 않는다. ``lam_down``으로 비대칭 망각
(나쁜 기록만 더 끈질김)도 받아 Phase 2(E-세탁)에서 재사용한다.
"""
from __future__ import annotations

from antigreedy.governance.policy import Policy
from antigreedy.governance.types import AgentAction, InteractionHistory, SharedState
from antigreedy.governance.reputation_calc import beta_reputation

BASE_SHARE = 0.22   # 평판 1.0일 때 잔여 커먼즈에서 허용하는 최대 점유 (gossip와 동일)
CHARS_PER_TOKEN = 4


class BetaOstracismPolicy(Policy):
    """Beta+λ 평판 기반 배제+캡. ``lam`` 망각계수가 실험 변수(λ-스윕)."""
    priority = 22  # 기존 ostracism(20)·gossip(25) 사이 — 단일 정책으로 둘을 대체

    def __init__(self, lam: float = 1.0, thresh: float = 0.45, floor: int = 30,
                 lam_down: float | None = None) -> None:
        self.lam = lam
        self.thresh = thresh
        self.floor = floor
        self.lam_down = lam_down
        self.name = f"beta_ostracism_l{lam:.2f}"

    def evaluate(self, action: AgentAction, state: SharedState,
                 history: InteractionHistory):
        if action.action_type != "message":
            return self.allow(reason="not a message")
        if not state.turn_log:
            return self.allow(reason="평판 근거 없음 (기록 없음)")
        rep, share = beta_reputation(action.agent_id, state, self.lam, self.lam_down)
        gossip = [{"event": "gossip", "data": {
            "agent_id": action.agent_id, "reputation": round(rep, 2),
            "share": round(share, 2), "lam": self.lam,
            "tone": "negative" if rep < 0.6 else "positive"}}]
        if rep < self.thresh:
            return self.deny(
                reason=f"배제(beta λ={self.lam}) — 평판 {rep:.2f}<{self.thresh} (점유 {share:.2f})",
                flags={"ostracized": True, "airtime_greedy": True, "low_reputation": True},
                events=gossip)
        remaining = state.commons.get("token_budget_remaining")
        if remaining is None or action.token_estimate <= 0:
            return self.allow(reason="no commons tracked", events=gossip)
        cap = max(self.floor, int(remaining * BASE_SHARE * rep))
        if action.token_estimate <= cap:
            return self.allow(reason=f"평판 {rep:.2f} 양호 (점유 {share:.2f})", events=gossip)
        content = action.payload.get("content", "")
        return self.modify(
            {**action.payload, "content": content[: cap * CHARS_PER_TOKEN], "_truncated": True},
            reason=f"평판 {rep:.2f} → {action.token_estimate}>{cap} 축약",
            flags={"airtime_greedy": True, "low_reputation": rep < 0.6}, events=gossip)
