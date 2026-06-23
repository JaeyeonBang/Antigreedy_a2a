"""BetaOstracismPolicy (Phase 1) — Beta+λ 평판으로 구동되는 배제+캡 정책 단위 테스트."""
from __future__ import annotations

from antigreedy.governance.types import AgentAction, SharedState, Verdict
from antigreedy.governance.beta_ostracism import BetaOstracismPolicy


def _state(rounds, n=3, pool=1000):
    st = SharedState(commons={"n_agents": n, "token_budget_remaining": pool})
    order = ["A", "B", "C", "D", "E"][:n]
    for rd in rounds:
        for a in order:
            d = rd.get(a, 0)
            st.turn_log.append((a, d, d))
    return st


def _act(agent, tokens=100):
    return AgentAction(agent_id=agent, action_type="message", token_estimate=tokens,
                       payload={"content": "u" * (tokens * 4), "request": tokens})


def test_no_log_allows():
    pol = BetaOstracismPolicy(lam=0.9)
    st = SharedState(commons={"n_agents": 3, "token_budget_remaining": 1000})
    assert pol.evaluate(_act("A"), st, []).verdict == Verdict.ALLOW


def test_severe_hog_is_ostracized():
    st = _state([{"A": 200, "B": 5, "C": 5}] * 3)
    pol = BetaOstracismPolicy(lam=1.0)
    res = pol.evaluate(_act("A"), st, [])
    assert res.verdict == Verdict.DENY
    assert res.flags.get("ostracized") is True


def test_fair_agent_allowed_under_cap():
    st = _state([{"A": 10, "B": 10, "C": 10}] * 3)
    pol = BetaOstracismPolicy(lam=1.0)
    res = pol.evaluate(_act("A", tokens=20), st, [])
    assert res.verdict == Verdict.ALLOW


def test_non_message_allowed():
    pol = BetaOstracismPolicy(lam=0.9)
    act = AgentAction(agent_id="A", action_type="other")
    assert pol.evaluate(act, _state([{"A": 200, "B": 5, "C": 5}]), []).verdict == Verdict.ALLOW


def test_forgetting_re_admits_recovered_hog():
    # 2회 과점 후 침묵 → λ=1(영구)은 아직 배제, λ<1(망각)은 회복돼 재참여 허용.
    rounds = [{"A": 200, "B": 10, "C": 10}, {"A": 200, "B": 10, "C": 10},
              {"A": 0, "B": 50, "C": 50}]
    st = _state(rounds)
    denied_keep = BetaOstracismPolicy(lam=1.0).evaluate(_act("A"), st, []).verdict
    res_forget = BetaOstracismPolicy(lam=0.6).evaluate(_act("A", tokens=20), st, []).verdict
    assert denied_keep == Verdict.DENY      # 영구 누적: 아직 배제
    assert res_forget != Verdict.DENY       # 망각: 재참여 허용
