"""평판 단일출처 모듈 회귀 — linear_reputation이 기존 인라인 공식과 동일함을 고정."""
from __future__ import annotations

from antigreedy.governance.types import SharedState
from antigreedy.governance.reputation_calc import (
    linear_reputation, share_of, _n_agents, beta_reputation, _round_indices,
)


def _state(shares: dict[str, int]) -> SharedState:
    st = SharedState(commons={"n_agents": len(shares)})
    for a, d in shares.items():
        st.turn_log.append((a, d, d))  # (agent, attempted, delivered)
    return st


def test_empty_log_is_full_reputation():
    rep, share = linear_reputation("A", _state({}))
    assert rep == 1.0 and share == 0.0


def test_fair_share_keeps_full_reputation():
    # 균등이면 share == fair == 1/3 → rep 1.0
    rep, share = linear_reputation("B", _state({"A": 100, "B": 100, "C": 100}))
    assert abs(share - 1 / 3) < 1e-9
    assert rep == 1.0


def test_severe_hog_hits_floor():
    # A: share 300/420=.714, fair .333, overage 1.143 → rep clip 하한 0.1
    rep, share = linear_reputation("A", _state({"A": 300, "B": 60, "C": 60}))
    assert abs(share - 300 / 420) < 1e-9
    assert rep == 0.1


def test_below_fair_is_full_reputation():
    rep, _ = linear_reputation("B", _state({"A": 300, "B": 60, "C": 60}))
    assert rep == 1.0  # share .143 ≤ fair .333


def test_double_fair_share_is_floor_boundary():
    # share == 2*fair 면 overage == 1 → rep == 0.0 → clip 0.1
    # A=200,B=50,C=50: total 300, A share .667 = 2*.333, overage 1.0 → rep 0.1
    rep, _ = linear_reputation("A", _state({"A": 200, "B": 50, "C": 50}))
    assert rep == 0.1


def test_share_of_matches_reputation_share():
    st = _state({"A": 300, "B": 60, "C": 60})
    assert abs(share_of("A", st) - linear_reputation("A", st)[1]) < 1e-12


def test_n_agents_falls_back_to_distinct_log():
    st = SharedState(commons={})  # no n_agents
    st.turn_log.extend([("A", 10, 10), ("B", 10, 10)])
    assert _n_agents(st) == 2


# --- Beta+λ 평판 (Phase 1: 망각계수가 회복을 살리나?) ---

def _rounds_state(rounds: list[dict[str, int]], n: int = 3) -> SharedState:
    """라운드별 {agent: delivered} 리스트를 round-robin turn_log로 펼친다(A,B,C 순)."""
    st = SharedState(commons={"n_agents": n})
    order = ["A", "B", "C", "D", "E"][:n]
    for rd in rounds:
        for a in order:
            d = rd.get(a, 0)
            st.turn_log.append((a, d, d))
    return st


def test_round_indices_round_robin_with_skip():
    # A,B,C / B,C (A 빠짐) / C (B,A 빠짐) → 라운드 0,0,0,1,1,2
    log = [("A", 1, 1), ("B", 1, 1), ("C", 1, 1),
           ("B", 1, 1), ("C", 1, 1),
           ("C", 1, 1)]
    assert _round_indices(log, 3) == [0, 0, 0, 1, 1, 2]


def test_beta_empty_log_is_full_reputation():
    rep, share = beta_reputation("A", _rounds_state([]), lam=0.9)
    assert rep == 1.0 and share == 0.0


def test_beta_always_fair_is_high():
    st = _rounds_state([{"A": 10, "B": 10, "C": 10}] * 4)
    rep, _ = beta_reputation("A", st, lam=1.0)
    assert rep > 0.5  # 매 라운드 공정 → 좋은 의사관측치 누적


def test_beta_always_hog_is_low():
    st = _rounds_state([{"A": 100, "B": 5, "C": 5}] * 4)
    rep, _ = beta_reputation("A", st, lam=1.0)
    assert rep < 0.45  # 매 라운드 과점 → 낮은 평판 (배제 임계 미만)


def test_beta_forgetting_lifts_reputation_after_early_defection():
    # ★ 핵심 인과: 초기 1회 과점 후 계속 공정 → 망각(λ<1)이 회복을 살린다.
    st = _rounds_state([{"A": 100, "B": 10, "C": 10},   # round0: A 과점 (오래된 잘못)
                        {"A": 10, "B": 10, "C": 10},     # round1~3: A 공정 (최근)
                        {"A": 10, "B": 10, "C": 10},
                        {"A": 10, "B": 10, "C": 10}])
    rep_keep = beta_reputation("A", st, lam=1.0)[0]    # 영구 누적 (망각 없음)
    rep_forget = beta_reputation("A", st, lam=0.5)[0]  # 빠른 망각
    assert rep_forget > rep_keep  # 오래된 잘못을 잊어 평판이 더 회복


def test_beta_forgetting_punishes_recent_defection():
    # 대칭 확인: 초기 공정 후 최근 과점이면 망각(λ<1)이 평판을 더 *낮춘다*(최근 가중).
    st = _rounds_state([{"A": 10, "B": 10, "C": 10},
                        {"A": 10, "B": 10, "C": 10},
                        {"A": 10, "B": 10, "C": 10},
                        {"A": 100, "B": 10, "C": 10}])   # round3: 최근 과점
    rep_keep = beta_reputation("A", st, lam=1.0)[0]
    rep_forget = beta_reputation("A", st, lam=0.5)[0]
    assert rep_forget < rep_keep


def test_beta_asymmetric_lambda_makes_bad_marks_stickier():
    # E-세탁 대비: lam_down>lam → 나쁜 기록(s)이 더 느리게 잊혀 평판이 더 낮게 유지.
    st = _rounds_state([{"A": 100, "B": 10, "C": 10},
                        {"A": 10, "B": 10, "C": 10},
                        {"A": 10, "B": 10, "C": 10},
                        {"A": 10, "B": 10, "C": 10}])
    rep_sym = beta_reputation("A", st, lam=0.5)[0]                 # 대칭 망각
    rep_sticky = beta_reputation("A", st, lam=0.5, lam_down=0.95)[0]  # 나쁜 기록만 천천히 망각
    assert rep_sticky < rep_sym
