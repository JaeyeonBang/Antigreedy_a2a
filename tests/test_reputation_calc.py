"""평판 단일출처 모듈 회귀 — linear_reputation이 기존 인라인 공식과 동일함을 고정."""
from __future__ import annotations

from antigreedy.governance.types import SharedState
from antigreedy.governance.reputation_calc import linear_reputation, share_of, _n_agents


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
