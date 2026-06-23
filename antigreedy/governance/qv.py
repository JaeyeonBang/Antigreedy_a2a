"""QuadraticVotingPolicy (Phase 3, C축) — 진짜 QV: 2차 비용 + 고정 예산 + 평판가중.

Phase A의 1/(1+o²) 캡은 *예산이 없어* 진짜 QV가 아니었다(리뷰 NO-GO). 진짜 QV(Weyl 2017)는
강도(intensity)의 **2차 비용**을 **고정 예산 B**에 부과한다 — 한 곳에 몰아 쓰면 비용이 제곱으로
폭증해 독점이 자기억제된다. 여기에 **평판 가중**(cost = d²/rep)을 더하면, 사용자가 물었던
"QV+평판 결합본"이 된다: 저평판일수록 같은 수요가 더 비싸 투표력이 약해진다.

구현은 *recompute-on-read*(단일 기록자 준수): 누적 지출을 turn_log에서 매번 재계산하므로 정책은
상태를 변경하지 않는다. 남은 예산으로 살 수 있는 최대 수요까지 캡(초과분 MODIFY).
"""
from __future__ import annotations

import math

from antigreedy.governance.policy import Policy
from antigreedy.governance.types import AgentAction, InteractionHistory, SharedState
from antigreedy.governance.reputation_calc import linear_reputation

CHARS_PER_TOKEN = 4


def unit_cost(d: float, rep: float, use_rep: bool = True) -> float:
    """수요 d의 2차 비용 = d²/rep (평판가중) 또는 d²(무가중). 저평판일수록 비쌈."""
    r = rep if use_rep else 1.0
    r = max(r, 1e-6)
    return (d * d) / r


def affordable(remaining: float, rep: float, use_rep: bool = True) -> float:
    """남은 예산으로 살 수 있는 최대 수요 = sqrt(remaining·rep) (2차 비용의 역)."""
    r = rep if use_rep else 1.0
    return math.sqrt(max(0.0, remaining * r))


def sybil_total_cost(total: float, k: int, rep: float, shared_budget: bool) -> float:
    """수요 total을 k개 신원으로 쪼갰을 때의 총 2차 비용.

    shared_budget=False(신원당 예산): k·((total/k)²/rep) = total²/(k·rep) → 1/k로 깎임(Sybil 취약점).
    shared_budget=True(신원-귀속 합산 예산): total²/rep (k 무관) → 분할 이득 0(방어)."""
    r = max(rep, 1e-6)
    if shared_budget:
        return (total * total) / r
    return k * ((total / k) ** 2 / r)


class QuadraticVotingPolicy(Policy):
    """진짜 QV 캡: 누적 2차 지출이 예산 B를 넘지 못하게 한다. ``use_rep``로 평판가중 on/off."""
    priority = 25

    def __init__(self, use_rep: bool = True, budget_B: float = 10000.0, floor: int = 30) -> None:
        self.use_rep = use_rep
        self.budget_B = budget_B
        self.floor = floor
        self.name = f"qv_{'rep' if use_rep else 'flat'}"

    def _spent(self, agent: str, state: SharedState, rep: float) -> float:
        return sum(unit_cost(d, rep, self.use_rep)
                   for a, _, d in state.turn_log if a == agent)

    def evaluate(self, action: AgentAction, state: SharedState,
                 history: InteractionHistory):
        if action.action_type != "message":
            return self.allow(reason="not a message")
        if action.token_estimate <= 0:
            return self.allow(reason="empty request")
        rep, share = linear_reputation(action.agent_id, state)
        spent = self._spent(action.agent_id, state, rep)
        remaining = self.budget_B - spent
        cap = max(self.floor, int(affordable(remaining, rep, self.use_rep)))
        if action.token_estimate <= cap:
            return self.allow(reason=f"QV 예산 내 ({action.token_estimate}≤{cap}, 지출 {spent:.0f}/{self.budget_B:.0f})")
        content = action.payload.get("content", "")
        return self.modify(
            {**action.payload, "content": content[: cap * CHARS_PER_TOKEN], "_truncated": True},
            reason=f"QV 2차비용 초과: {action.token_estimate}>{cap} (rep {rep:.2f}, 지출 {spent:.0f})",
            flags={"airtime_greedy": True, "qv_capped": True})
