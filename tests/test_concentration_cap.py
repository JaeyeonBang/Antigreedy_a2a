"""Phase A (Identity-DAO design §3.1, §5): ConcentrationCapPolicy.

A per-turn cap whose weight on `k * remaining` depends on the agent's cumulative
over-concentration o = max(0, share - fair)/fair, with three curves:
  flat     w = 1                  (== dumb cap, ignores history — control)
  linear   w = max(0, 1 - o)      (== existing gossip rep curve — control)
  quad     w = 1 / (1 + o^2)      (★ QV convex congestion pricing)

These tests are deterministic (no LLM): they pin the exact cap arithmetic and the
allow/modify boundary so the experiment compares *curves*, not implementation noise.
"""
from __future__ import annotations

from antigreedy.governance.concentration_cap import ConcentrationCapPolicy
from antigreedy.governance.types import AgentAction, SharedState


def _state(shares: dict[str, int], remaining: int, n: int = 3) -> SharedState:
    st = SharedState(commons={"token_budget_remaining": remaining, "n_agents": n})
    for agent, delivered in shares.items():
        st.turn_log.append((agent, delivered, delivered))  # (agent, attempted, delivered)
    return st


def _msg(agent: str, est: int) -> AgentAction:
    return AgentAction(agent_id=agent, action_type="message",
                       payload={"content": "x" * (est * 4)}, token_estimate=est)


def _cap_boundary(policy, state, agent):
    """Smallest token_estimate that gets MODIFIED = cap + 1; return the cap."""
    cap = 0
    for est in range(1, 400):
        r = policy.evaluate(_msg(agent, est), state, [])
        if r.verdict.value == "modify":
            cap = est - 1
            break
    return cap


def test_under_fair_share_all_curves_full_cap():
    # A at exactly fair share (1/3): o = 0 -> every curve weight = 1
    st = _state({"A": 100, "B": 100, "C": 100}, remaining=300)
    for curve in ("flat", "linear", "quad"):
        p = ConcentrationCapPolicy(curve=curve, k=0.5, floor=10)
        assert _cap_boundary(p, st, "A") == 150  # int(300 * 0.5 * 1)


def test_quadratic_formula_exact_for_severe_hog():
    # A=300/360 -> share .8333, fair .3333, o = 1.5 ; w = 1/(1+2.25)=0.30769
    st = _state({"A": 300, "B": 30, "C": 30}, remaining=300)
    p = ConcentrationCapPolicy(curve="quad", k=0.5, floor=10)
    assert _cap_boundary(p, st, "A") == 46  # int(300 * 0.5 * 0.307692) = 46


def test_linear_guillotines_at_double_fair_share():
    # o = 1.5 -> linear w = max(0, 1-1.5) = 0 -> cap falls to the floor
    st = _state({"A": 300, "B": 30, "C": 30}, remaining=300)
    p = ConcentrationCapPolicy(curve="linear", k=0.5, floor=10)
    assert _cap_boundary(p, st, "A") == 10


def test_flat_ignores_history():
    # Same severe hog, flat weight stays 1 -> cap unchanged by share
    st = _state({"A": 300, "B": 30, "C": 30}, remaining=300)
    p = ConcentrationCapPolicy(curve="flat", k=0.5, floor=10)
    assert _cap_boundary(p, st, "A") == 150


def test_quad_more_lenient_than_linear_on_mild_overage():
    # A=180/360 -> share .5, o = 0.5 ; linear w=.5 (cap 75), quad w=.8 (cap 120)
    st = _state({"A": 180, "B": 90, "C": 90}, remaining=300)
    lin = ConcentrationCapPolicy(curve="linear", k=0.5, floor=10)
    quad = ConcentrationCapPolicy(curve="quad", k=0.5, floor=10)
    cap_lin = _cap_boundary(lin, st, "A")
    cap_quad = _cap_boundary(quad, st, "A")
    # o = 1/3 float dust makes o=0.5000000000000001 deterministically, so
    # linear w=0.4999.. -> int(74.99..)=74 (never 75); quad w=0.8 -> 120. Fixed, not flaky.
    assert cap_lin == 74
    assert cap_quad == 120
    assert cap_quad > cap_lin  # graduated: quad does not over-punish mild overage


def test_quad_cap_monotonically_shrinks_with_concentration():
    p = ConcentrationCapPolicy(curve="quad", k=0.5, floor=1)
    fair = _cap_boundary(p, _state({"A": 120, "B": 120, "C": 120}, 300), "A")
    mild = _cap_boundary(p, _state({"A": 180, "B": 90, "C": 90}, 300), "A")
    severe = _cap_boundary(p, _state({"A": 300, "B": 30, "C": 30}, 300), "A")
    assert fair > mild > severe


def test_non_message_is_allowed():
    st = _state({"A": 300, "B": 30, "C": 30}, remaining=300)
    p = ConcentrationCapPolicy(curve="quad")
    r = p.evaluate(AgentAction(agent_id="A", action_type="vote", token_estimate=999), st, [])
    assert r.verdict.value == "allow"


def test_no_commons_tracked_is_allowed():
    st = SharedState(commons={})  # no token_budget_remaining
    st.turn_log.append(("A", 300, 300))
    p = ConcentrationCapPolicy(curve="quad")
    assert p.evaluate(_msg("A", 999), st, []).verdict.value == "allow"


def test_over_cap_truncates_payload_and_flags_airtime_greedy():
    st = _state({"A": 300, "B": 30, "C": 30}, remaining=300)
    p = ConcentrationCapPolicy(curve="quad", k=0.5, floor=10)  # cap = 46
    r = p.evaluate(_msg("A", 200), st, [])
    assert r.verdict.value == "modify"
    assert r.modified_payload["_truncated"] is True
    assert len(r.modified_payload["content"]) == 46 * 4  # cap * CHARS_PER_TOKEN
    assert r.flags.get("airtime_greedy") is True


def test_unknown_curve_rejected():
    import pytest
    with pytest.raises(ValueError):
        ConcentrationCapPolicy(curve="cubic")


def test_flat_is_byte_for_byte_fraction_cap():
    """The cap_flat arm IS the V6 dumb_cap control — it must match FractionCapPolicy
    exactly, or the 'flat == dumb cap' claim is false (plan review, R2)."""
    from antigreedy.governance.nullcap import FractionCapPolicy
    flat = ConcentrationCapPolicy(curve="flat", k=0.22, floor=30)
    dumb = FractionCapPolicy(k=0.22, floor=30)
    for shares in ({}, {"A": 300, "B": 30, "C": 30}, {"A": 100, "B": 100, "C": 100}):
        for remaining in (0, 30, 137, 300, 600):
            for est in (0, 25, 66, 150, 300):
                st = _state(shares, remaining)
                rf = flat.evaluate(_msg("A", est), st, [])
                rd = dumb.evaluate(_msg("A", est), st, [])
                assert rf.verdict == rd.verdict
                assert (rf.modified_payload or {}).get("content") == \
                       (rd.modified_payload or {}).get("content")
                assert rf.flags.get("airtime_greedy") == rd.flags.get("airtime_greedy")
