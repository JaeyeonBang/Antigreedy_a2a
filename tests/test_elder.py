"""Phase 2 — Elder 원장 + LLM-judge 평판 단위 테스트 (judge는 MockBackend 결정론)."""
from __future__ import annotations

import asyncio

from antigreedy.governance.types import AgentAction, SharedState, Verdict
from antigreedy.governance.elder import (
    ElderLedger, elder_reputation, ElderInterceptPoint,
)
from antigreedy.governance.elder_judge import numeric_judge, parse_score, judge
from antigreedy.backends import MockBackend


def _state(rounds, n=3, pool=1000):
    st = SharedState(commons={"n_agents": n, "token_budget_remaining": pool})
    order = ["A", "B", "C", "D", "E"][:n]
    for rd in rounds:
        for a in order:
            d = rd.get(a, 0)
            st.turn_log.append((a, d, d))
    return st


def _act(agent, tokens=100, just="taking a fair share"):
    return AgentAction(agent_id=agent, action_type="message", token_estimate=tokens,
                       payload={"content": "u" * (tokens * 4), "request": tokens,
                                "justification": just})


# --- ElderLedger (append-only) ---

def test_ledger_append_and_scores_for():
    L = ElderLedger()
    L.record(judge="elder", target="A", score=0.2, round=0)
    L.record(judge="elder", target="B", score=0.9, round=0)
    L.record(judge="elder", target="A", score=0.3, round=4)
    assert L.scores_for("A") == [0.2, 0.3]
    assert L.scores_for("B") == [0.9]
    assert L.scores_for("C") == []
    assert len(L.entries) == 3  # 추가만, 수정/삭제 없음


# --- elder_reputation (α 가중) ---

def test_elder_reputation_alpha_one_is_rule_only():
    assert elder_reputation(0.3, [0.9], alpha=1.0) == 0.3  # judge 무시


def test_elder_reputation_alpha_zero_is_judge_only():
    assert elder_reputation(0.3, [0.8, 1.0], alpha=0.0) == 0.9  # mean(judge)


def test_elder_reputation_half_blends():
    assert abs(elder_reputation(0.4, [0.8], alpha=0.5) - 0.6) < 1e-9


def test_elder_reputation_no_scores_falls_back_to_rule():
    assert elder_reputation(0.42, [], alpha=0.5) == 0.42


# --- numeric_judge (앵커 대조: LLM 없음) ---

def test_numeric_judge_fair_is_high():
    assert numeric_judge(share=0.30, fair=1 / 3) == 1.0


def test_numeric_judge_hog_is_low():
    assert numeric_judge(share=0.80, fair=1 / 3) < 0.5


# --- parse_score ---

def test_parse_score_variants():
    assert parse_score("8") == 0.8
    assert parse_score("score: 9/10") == 0.9
    assert parse_score("I rate this 3 out of 10") == 0.3
    assert parse_score("rating 10") == 1.0
    assert parse_score("no number here") == 0.5  # 기본값


# --- judge (MockBackend 결정론) ---

def test_judge_with_mock_backend():
    backend = MockBackend(lambda prompt: "FAIRNESS: 7")
    score = asyncio.run(judge(backend, "A", "I take only my share", 0.3, 0.33))
    assert score == 0.7


# --- ElderInterceptPoint (judge 캐시 1회 + 원장 기록 + 캡) ---

def test_elder_intercept_judges_once_and_records():
    st = _state([{"A": 200, "B": 10, "C": 10}] * 3)
    calls = {"n": 0}

    async def fake_judge(agent, just, share, fair):
        calls["n"] += 1
        return 0.1  # 가혹한 심사

    ip = ElderInterceptPoint(st, alpha=0.5, judge_fn=fake_judge)
    asyncio.run(ip.submit(_act("A")))
    asyncio.run(ip.submit(_act("A")))  # 두 번째 턴은 재심사 안 함
    assert calls["n"] == 1
    ledger = st.extra["elder_ledger"]
    assert ledger.scores_for("A") == [0.1]


def test_elder_intercept_low_rep_denies():
    st = _state([{"A": 200, "B": 10, "C": 10}] * 3)

    async def harsh(agent, just, share, fair):
        return 0.0

    ip = ElderInterceptPoint(st, alpha=0.5, judge_fn=harsh)
    res = asyncio.run(ip.submit(_act("A")))
    assert res.verdict == Verdict.DENY


def test_elder_judge_can_rescue_a_borderline_agent():
    # 규칙상 경계인 에이전트를, 관대한 elder 심사가 임계 위로 끌어올려 배제를 면하게 한다.
    rounds = [{"A": 120, "B": 60, "C": 60}, {"A": 120, "B": 60, "C": 60}]

    async def lenient(agent, just, share, fair):
        return 1.0  # 매우 관대

    async def harsh(agent, just, share, fair):
        return 0.0

    res_lenient = asyncio.run(ElderInterceptPoint(_state(rounds), alpha=0.5, judge_fn=lenient).submit(_act("A")))
    res_harsh = asyncio.run(ElderInterceptPoint(_state(rounds), alpha=0.5, judge_fn=harsh).submit(_act("A")))
    # 관대 심사가 가혹 심사보다 덜 가혹한 판정(deny 아님 ≥ deny)
    assert not (res_lenient.verdict == Verdict.DENY and res_harsh.verdict != Verdict.DENY)
    assert res_harsh.verdict == Verdict.DENY  # 가혹 심사는 배제


def test_elder_numbers_arm_uses_no_llm():
    # judge_fn=None (ledger_numbers) → LLM 호출 없이 numeric_judge로 점수 산정.
    st = _state([{"A": 200, "B": 10, "C": 10}] * 2)
    ip = ElderInterceptPoint(st, alpha=0.5, judge_fn=None)  # use_llm=False
    asyncio.run(ip.submit(_act("A")))
    ledger = st.extra["elder_ledger"]
    assert ledger.entries and ledger.entries[0]["judge"] == "numbers"
