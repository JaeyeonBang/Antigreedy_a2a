"""제안③④ + 평판 피드백 채널 = '행동(입력)측' 거버넌스.

기존 Policy는 행동의 *출력*을 intercept(cap/deny)한다. 외부 리뷰가 지적한 빈틈:
가십·평판 이벤트가 에이전트에게 *되먹임되지 않아* 행동(시도, attempted) 자체는 안 변함.
PromptShaper는 SharedState를 read-only로 읽어 **프롬프트를 재구성**해 시도 채널을 겨눈다.

검증 포인트:
- 각 shaper가 고유 cue 텍스트를 프롬프트에 주입한다 (③ 공동목표, ④ 책임성, 평판 되먹임).
- shaper는 SharedState를 *변경하지 않는다* (단일 기록자 규칙).
- 평판 되먹임은 turn_log에서 파생 → 독점 에이전트는 낮은 평판으로 노출된다.
- cue에 반응하는 에이전트는 시도를 줄인다 → top_share(요청) 하락 = 행동 채널이 실제로 움직인다.
"""
import asyncio

from antigreedy.backends import MockBackend
from antigreedy.events import EventStream
from antigreedy.governance.nullcap import chain_intercept
from antigreedy.governance.types import SharedState
from antigreedy.scenario.prompt_shapers import (
    SHAPERS,
    apply_shapers,
    reputation_feedback,
)
from antigreedy.scenario.resource_task import (
    TaskConfig,
    make_framing_aware_script,
    make_task_script,
    run_resource_task,
)


def _state_with_log(turns):
    st = SharedState()
    st.commons["n_agents"] = len({a for a, _, _ in turns}) or 1
    for agent, attempted, delivered in turns:
        st.record_turn(agent, attempted, delivered)
    return st


def _ctx():
    return {"n": 4, "fair": 50, "pool_left": 400, "round_no": 1, "workload": 150}


def test_registry_exposes_all_three_channels():
    for name in ("superordinate_identity", "accountability", "reputation_feedback"):
        assert name in SHAPERS, f"missing shaper: {name}"


def test_superordinate_identity_injects_common_goal_cue():
    out = apply_shapers(["superordinate_identity"], "A", SharedState(), "BASE", _ctx())
    assert "BASE" in out                       # base prompt preserved
    assert "ONE TEAM" in out                    # 제안③ 공동목표 cue (mock/LLM 공통 마커)
    assert "team" in out.lower() and "all" in out.lower()


def test_accountability_injects_audience_cue():
    out = apply_shapers(["accountability"], "A", SharedState(), "BASE", _ctx())
    assert "JUSTIFY" in out.upper()             # 제안④ 관객효과/정당화 요구 cue
    assert "logged" in out.lower() or "reviewed" in out.lower()


def test_reputation_feedback_reflects_hogging():
    # A monopolised the commons; the feedback channel must expose A's LOW reputation.
    st = _state_with_log([("A", 300, 300), ("B", 30, 30), ("C", 30, 30), ("D", 30, 30)])
    line = reputation_feedback("A", st, "BASE", _ctx())
    assert "REPUTATION" in line.upper()
    assert "LOW" in line.upper()                # A is a hog → flagged low to peers
    # a fair player is not flagged low
    fair_line = reputation_feedback("B", st, "BASE", _ctx())
    assert "LOW" not in fair_line.upper()


def test_shapers_never_mutate_shared_state():
    st = _state_with_log([("A", 300, 300), ("B", 30, 30)])
    before = (dict(st.airtime_delivered), list(st.turn_log), dict(st.commons))
    for name in SHAPERS:
        apply_shapers([name], "A", st, "BASE", _ctx())
    after = (dict(st.airtime_delivered), list(st.turn_log), dict(st.commons))
    assert before == after                      # single-writer: shapers are read-only


def test_unknown_shaper_is_ignored_not_crash():
    out = apply_shapers(["does_not_exist"], "A", SharedState(), "BASE", _ctx())
    assert out == "BASE"


def _run(cfg, backend):
    state = SharedState()
    ic = chain_intercept([], state)             # NO output policies → isolate behavioral channel
    stream = EventStream(cfg.run_id, cfg.condition, 0)
    return asyncio.run(run_resource_task(cfg, backend, ic, stream, state))


def test_behavioral_channel_lowers_top_share_without_any_policy():
    """순수 행동 채널 검증: 출력 정책(cap) 0개. 그래도 cue에 반응하는 에이전트는
    요청을 줄여 top_share(요청 독점)가 내려간다 → 시도 채널이 실제로 움직였다."""
    backend = MockBackend(make_framing_aware_script(greedy_agent="A"))
    base = TaskConfig(run_id="r", condition="baseline", workload=120, pool=480, max_rounds=6)
    shaped = TaskConfig(run_id="r", condition="governed", workload=120, pool=480, max_rounds=6,
                        shapers=["superordinate_identity", "reputation_feedback"])
    m_base = _run(base, backend)["metrics"]
    m_shaped = _run(shaped, backend)["metrics"]
    # the hog backs off only when the framing cue is present
    assert m_shaped["top_share"] < m_base["top_share"]
    assert m_shaped["completion_rate"] >= m_base["completion_rate"]


def test_framing_aware_mock_matches_greedy_when_no_shaper():
    """shaper가 없으면 framing-aware mock == 기존 greedy mock (회귀 안전)."""
    cfg = TaskConfig(run_id="r", condition="baseline", workload=120, pool=480, max_rounds=6)
    greedy = _run(cfg, MockBackend(make_task_script("A")))["metrics"]
    aware = _run(cfg, MockBackend(make_framing_aware_script("A")))["metrics"]
    assert aware["top_share"] == greedy["top_share"]
