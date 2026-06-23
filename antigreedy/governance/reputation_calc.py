"""평판 계산 — 단일 출처(canonical).

이전엔 같은 `_reputation` 공식이 `prompt_shapers.py`, `social_reputation/25_reputation_gossip.py`,
`.../20_ostracism.py` 세 곳에 복제돼 있었다. Beta+λ 등 대체 공식을 안전하게 끼우려면 한 곳에서만
정의해야 하므로 여기로 통합한다. 모든 함수는 `SharedState.turn_log`를 **read-only**로 읽는다
(단일 기록자 규칙 — 정책/셰이퍼는 상태를 변경하지 않음).

`linear_reputation`은 *기존 동작을 비트 단위로 보존*한다(회귀 가드는 기존 테스트 스위트).
"""
from __future__ import annotations

from antigreedy.governance.types import SharedState


def _n_agents(state: SharedState) -> int:
    """에이전트 수: commons에 있으면 그 값, 없으면 turn_log에 등장한 distinct 수(최소 1)."""
    return state.commons.get("n_agents") or max(1, len({a for a, _, _ in state.turn_log}))


def share_of(agent_id: str, state: SharedState) -> float:
    """누적 전달량 점유율 mine/total (기록 없으면 0.0)."""
    log = state.turn_log
    total = sum(d for _, _, d in log)
    if total <= 0:
        return 0.0
    mine = sum(d for a, _, d in log if a == agent_id)
    return mine / total


def linear_reputation(agent_id: str, state: SharedState) -> tuple[float, float]:
    """과거 점유(turn_log)에서 파생한 평판 [0.1, 1.0] (1.0 = 공정/협력적) + 점유율.

    공정 몫(1/n) 이하면 1.0, 공정 몫의 2배면 0.1(하한). 기존 3곳 인라인 공식과 동일.
    반환: (rep, share) — 호출부는 `rep, share = linear_reputation(...)`로 언팩.
    """
    log = state.turn_log
    total = sum(d for _, _, d in log)
    if total <= 0:
        return 1.0, 0.0
    mine = sum(d for a, _, d in log if a == agent_id)
    n = _n_agents(state)
    fair = 1.0 / n
    share = mine / total
    rep = max(0.1, min(1.0, 1.0 - max(0.0, share - fair) / fair))
    return rep, share
