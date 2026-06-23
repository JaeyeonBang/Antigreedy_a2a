"""카스트 지표(Phase 1) 단위 테스트 — modularity_q(Newman)·recovery_rate(회복률).

두 지표 모두 turn_log/군집의 *순수함수*. modularity는 알려진 그래프로, recovery_rate는
'초기 과점 후 침묵' 합성 로그로 검증(망각 λ<1이 회복률을 올린다 = Phase 1 red-green).
"""
from __future__ import annotations

import functools

from antigreedy.governance.types import SharedState
from antigreedy.governance.reputation_calc import linear_reputation, beta_reputation
from antigreedy.caste_metrics import modularity_q, recovery_rate


# --- modularity_q (Newman) ---

def test_modularity_two_clear_communities_is_positive():
    # 두 삼각형 {1,2,3},{4,5,6} 내부 완전연결 + 다리 3-4 하나
    edges = {(1, 2): 1, (1, 3): 1, (2, 3): 1,
             (4, 5): 1, (4, 6): 1, (5, 6): 1,
             (3, 4): 1}
    comm = {1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 1}
    assert modularity_q(comm, edges) > 0.3


def test_modularity_single_community_is_zero():
    edges = {(1, 2): 1, (1, 3): 1, (2, 3): 1, (3, 4): 1, (4, 5): 1, (4, 6): 1, (5, 6): 1}
    comm = {n: 0 for n in range(1, 7)}
    assert abs(modularity_q(comm, edges)) < 1e-9


def test_modularity_no_edges_is_zero():
    assert modularity_q({1: 0, 2: 1}, {}) == 0.0


def test_modularity_singletons_are_negative():
    # 모든 노드가 자기 군집 → Q < 0 (community 구조 없음)
    edges = {(1, 2): 1, (2, 3): 1, (1, 3): 1}
    comm = {1: 0, 2: 1, 3: 2}
    assert modularity_q(comm, edges) < 0.0


# --- recovery_rate (저평판 진입 후 회복) ---

def _rounds_state(rounds, n=3):
    st = SharedState(commons={"n_agents": n})
    order = ["A", "B", "C", "D", "E"][:n]
    for rd in rounds:
        for a in order:
            d = rd.get(a, 0)
            st.turn_log.append((a, d, d))
    return st


def _early_hog_then_silent():
    # A: 0~1라운드 심하게 과점, 이후 5라운드 완전 침묵(배제 후 자기교정 모사)
    return ([{"A": 200, "B": 10, "C": 10}] * 2
            + [{"A": 0, "B": 50, "C": 50}] * 5)


def test_recovery_rate_in_unit_interval():
    st = _rounds_state(_early_hog_then_silent())
    rf = functools.partial(beta_reputation, lam=0.7)
    r = recovery_rate(st.turn_log, 3, rf)
    assert 0.0 <= r <= 1.0


def test_recovery_rate_forgetting_beats_permanent():
    # ★ red-green: 망각 λ=0.7이 λ=1.0보다 회복률이 높다(같은 로그, rep_fn만 다름).
    log = _rounds_state(_early_hog_then_silent()).turn_log
    r_forget = recovery_rate(log, 3, functools.partial(beta_reputation, lam=0.7))
    r_keep = recovery_rate(log, 3, functools.partial(beta_reputation, lam=1.0))
    assert r_forget > r_keep


def test_recovery_rate_zero_when_never_recovers():
    # A가 끝까지 과점만 → 저평판에서 회복 못 함 → 0
    st = _rounds_state([{"A": 200, "B": 5, "C": 5}] * 6)
    r = recovery_rate(st.turn_log, 3, functools.partial(beta_reputation, lam=0.7))
    assert r == 0.0


def test_recovery_rate_zero_when_never_low():
    # 항상 공정 → 저평판 진입 자체가 없음 → 0 (회복 이벤트 없음)
    st = _rounds_state([{"A": 10, "B": 10, "C": 10}] * 5)
    r = recovery_rate(st.turn_log, 3, linear_reputation)
    assert r == 0.0
