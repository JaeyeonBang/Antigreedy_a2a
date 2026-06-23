"""Phase 3 — 진짜 QV(2차 비용 + 고정 예산 + 평판가중) + Sybil 단위 테스트.

진짜 QV = 강도의 *2차 비용*을 *고정 예산*에 부과(Weyl 2017). Phase A의 1/(1+o²) 곡선은 예산이
없어 "진짜 QV가 아니다"(리뷰 NO-GO). 여기선 누적 2차 지출이 예산 B를 넘지 못하게 캡하고,
평판으로 가중(cost=d²/rep → 저평판이 더 비쌈 = 투표력 약함). Sybil은 한 수요를 여러 신원으로
쪼개 2차 비용을 깎는 공격 — 단위 비용 회계로 취약점과 방어를 결정론적으로 보인다.
"""
from __future__ import annotations

from antigreedy.governance.types import AgentAction, SharedState, Verdict
from antigreedy.governance.qv import (
    QuadraticVotingPolicy, affordable, unit_cost, sybil_total_cost,
)


def _state(rounds, n=3, pool=100000):
    st = SharedState(commons={"n_agents": n, "token_budget_remaining": pool})
    order = ["A", "B", "C", "D", "E"][:n]
    for rd in rounds:
        for a in order:
            d = rd.get(a, 0)
            st.turn_log.append((a, d, d))
    return st


def _act(agent, tokens):
    return AgentAction(agent_id=agent, action_type="message", token_estimate=tokens,
                       payload={"content": "u" * (tokens * 4), "request": tokens})


# --- 2차 비용 / 예산 회계 (순수함수) ---

def test_unit_cost_is_quadratic():
    assert unit_cost(10, rep=1.0, use_rep=True) == 100.0
    assert unit_cost(20, rep=1.0, use_rep=True) == 400.0   # 2배 수요 → 4배 비용


def test_unit_cost_rep_weighting_penalizes_low_rep():
    assert unit_cost(10, rep=0.5, use_rep=True) == 200.0   # 저평판 → 더 비쌈 (÷rep)
    assert unit_cost(10, rep=1.0, use_rep=True) == 100.0
    assert unit_cost(10, rep=0.5, use_rep=False) == 100.0  # 무가중이면 rep 무관


def test_affordable_inverts_quadratic_cost():
    assert affordable(remaining=400.0, rep=1.0, use_rep=True) == 20.0   # sqrt(400)
    assert affordable(remaining=400.0, rep=0.25, use_rep=True) == 10.0  # sqrt(400*0.25)


# --- QuadraticVotingPolicy ---

def test_qv_within_budget_allows():
    pol = QuadraticVotingPolicy(use_rep=True, budget_B=10000)
    assert pol.evaluate(_act("A", 50), _state([]), []).verdict == Verdict.ALLOW  # 50²=2500 ≤ 10000


def test_qv_over_budget_modifies():
    pol = QuadraticVotingPolicy(use_rep=False, budget_B=2500, floor=30)
    res = pol.evaluate(_act("A", 200), _state([]), [])  # cap sqrt(2500)=50 < 200
    assert res.verdict == Verdict.MODIFY


def test_qv_spends_accumulate_across_turns():
    spent_heavy = _state([{"A": 90, "B": 10, "C": 10}, {"A": 90, "B": 10, "C": 10}])  # 90²·2=16200
    pol = QuadraticVotingPolicy(use_rep=False, budget_B=20000)
    assert pol.evaluate(_act("A", 100), spent_heavy, []).verdict == Verdict.MODIFY  # 남은 3800 → cap 61
    assert pol.evaluate(_act("A", 100), _state([]), []).verdict == Verdict.ALLOW    # 남은 20000 → cap 141


def test_qv_rep_weighting_caps_low_rep_harder():
    # A 과점(저평판 .1) vs D 공정(고평판 1.0). 같은 요청 60에 A는 캡, D는 통과.
    st = _state([{"A": 300, "B": 20, "C": 20, "D": 20}], n=4)
    pol = QuadraticVotingPolicy(use_rep=True, budget_B=5000, floor=30)
    assert pol.evaluate(_act("A", 60), st, []).verdict == Verdict.MODIFY  # cap sqrt(5000*.1)=22→floor30
    assert pol.evaluate(_act("D", 60), st, []).verdict == Verdict.ALLOW   # cap sqrt(5000*1)=70≥60


def test_qv_non_message_allowed():
    pol = QuadraticVotingPolicy(use_rep=True, budget_B=1000)
    act = AgentAction(agent_id="A", action_type="other")
    assert pol.evaluate(act, _state([]), []).verdict == Verdict.ALLOW


# --- Sybil: 신원 분할이 2차 비용을 깎는다 + 방어 ---

def test_sybil_split_reduces_cost_under_per_identity_budget():
    # 수요 100: 1신원 100²=10000; 2신원 각 50²=2500 합 5000; 4신원 합 2500. k신원 → 1/k = 취약점.
    assert sybil_total_cost(total=100, k=1, rep=1.0, shared_budget=False) == 10000.0
    assert sybil_total_cost(total=100, k=2, rep=1.0, shared_budget=False) == 5000.0
    assert sybil_total_cost(total=100, k=4, rep=1.0, shared_budget=False) == 2500.0


def test_sybil_defense_shared_identity_bound_budget_neutralizes():
    # 방어: 신원-귀속(비양도) 예산을 컨트롤러에 합산 → 쪼개도 같은 비용(이득 0).
    one = sybil_total_cost(total=100, k=1, rep=1.0, shared_budget=True)
    two = sybil_total_cost(total=100, k=2, rep=1.0, shared_budget=True)
    assert one == two == 10000.0
