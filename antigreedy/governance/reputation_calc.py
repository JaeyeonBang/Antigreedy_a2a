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


# --- Beta + λ 평판 (Phase 1: 망각계수 λ가 카스트화/회복을 좌우하나?) ---

def _round_indices(log: list[tuple[str, int, int]], n: int) -> list[int]:
    """round-robin turn_log에서 각 항목의 라운드 인덱스를 복원. 에이전트가 과업을 마쳐
    빠지면(skip) 한 라운드는 정규 순서의 *부분수열*이라 위치가 라운드 내에서 단조 증가한다.
    현재 항목의 정규-순서 위치가 이전 항목 이하이면(되돌아감/반복) 새 라운드로 본다.
    n은 시그니처 호환용(복원은 등장 순서만으로 결정). 빈 로그 → []."""
    if not log:
        return []
    pos: dict[str, int] = {}
    for a, _, _ in log:  # 정규 순서 = 첫 등장 순
        pos.setdefault(a, len(pos))
    rounds: list[int] = []
    cur = 0
    prev = -1
    for a, _, _ in log:
        p = pos[a]
        if p <= prev:
            cur += 1
        rounds.append(cur)
        prev = p
    return rounds


def beta_reputation(agent_id: str, state: SharedState, lam: float,
                    lam_down: float | None = None) -> tuple[float, float]:
    """Beta 평판 (Jøsang) + 지수 망각 λ. 라운드별 *순간* 점유가 공정 몫 이하면 긍정 의사관측치
    ``r``, 초과면 부정 의사관측치 ``s``를 쌓되, 오래될수록 ``λ^Δ``로 감쇠한다(Δ=현재−해당 라운드).
    ``E[rep] = (r+1)/(r+s+2)`` ∈ (0,1). λ=1이면 영구 누적(망각 없음 → 카스트화 위험), λ<1이면
    최근 행동이 지배(회복 가능). ``lam_down``을 주면 *부정* 의사관측치에만 다른 감쇠를 적용
    (E-세탁 대비: ``lam_down>lam`` → 나쁜 기록이 더 끈질김). 반환: (rep, 누적 share).

    ``linear_reputation``과 같은 (agent_id, state) 접두 시그니처 → 정책에 drop-in 교체 가능.
    """
    log = state.turn_log
    total = sum(d for _, _, d in log)
    if total <= 0:
        return 1.0, 0.0
    mine = sum(d for a, _, d in log if a == agent_id)
    share = mine / total
    n = _n_agents(state)
    fair = 1.0 / n
    rounds = _round_indices(log, n)
    last = rounds[-1]
    round_total: dict[int, int] = {}
    for (a, _, d), r in zip(log, rounds):
        round_total[r] = round_total.get(r, 0) + d
    lam_bad = lam if lam_down is None else lam_down
    r_acc = s_acc = 0.0
    for (a, _, d), r in zip(log, rounds):
        if a != agent_id:
            continue
        rt = round_total.get(r, 0)
        share_r = d / rt if rt > 0 else 0.0
        delta = last - r
        if share_r <= fair:
            r_acc += lam ** delta
        else:
            s_acc += lam_bad ** delta
    rep = (r_acc + 1.0) / (r_acc + s_acc + 2.0)
    return rep, share
