"""카스트화 지표 (Phase 1, design B축) — 순수함수.

- ``modularity_q``: Newman 모듈러리티 Q. 행동 유사도 그래프에서 군집이 얼마나 *분리*됐나
  (= 카스트가 굳었나). 단일 군집이면 0, 잘 분리되면 양수, 구조 없으면 음수.
- ``recovery_rate``: 저평판으로 떨어진 에이전트가 임계치 위로 *되돌아오는* 속도(0~1).
  0 = 한 번 찍히면 못 돌아옴(카스트 고착), 클수록 빠른 회복. ``rep_fn``(평판 함수)을 주입해
  같은 로그를 다른 평판 규칙으로 평가할 수 있다 → 망각 λ가 회복을 살리는지 직접 대조.

설계 의도: ``metrics.py``는 단일 파일 모듈이라 같은 패키지에 ``metrics/caste.py``를 둘 수 없어
별도 모듈로 둔다(plan의 `metrics/caste.py` 의도와 동일 — 위치만 평면화).
"""
from __future__ import annotations

from typing import Callable, Iterable

from antigreedy.governance.types import SharedState
from antigreedy.governance.reputation_calc import _round_indices

RepFn = Callable[[str, SharedState], tuple[float, float]]


def modularity_q(communities: dict, weights) -> float:
    """Newman 모듈러리티 Q = (1/2m) Σ_ij (A_ij − k_i k_j / 2m) δ(c_i, c_j).

    ``communities``: node → community-id. ``weights``: 무방향 가중치 — dict{(i,j): w} 또는
    (i, j, w) 튜플 이터러블. 자기루프 없음 가정. 간선 0개면 0.0.
    """
    if isinstance(weights, dict):
        edges: Iterable = [(i, j, w) for (i, j), w in weights.items()]
    else:
        edges = list(weights)
    adj: dict[tuple, float] = {}
    deg: dict = {}
    m2 = 0.0  # 2m = 전체 가중치 합의 2배
    for i, j, w in edges:
        adj[(i, j)] = adj.get((i, j), 0.0) + w
        adj[(j, i)] = adj.get((j, i), 0.0) + w
        deg[i] = deg.get(i, 0.0) + w
        deg[j] = deg.get(j, 0.0) + w
        m2 += 2.0 * w
    if m2 == 0:
        return 0.0
    nodes = list(communities)
    q = 0.0
    for i in nodes:
        ci = communities[i]
        ki = deg.get(i, 0.0)
        for j in nodes:
            if communities[j] != ci:
                continue
            a = adj.get((i, j), 0.0)
            q += a - ki * deg.get(j, 0.0) / m2
    return q / m2


def recovery_rate(log: list[tuple[str, int, int]], n: int, rep_fn: RepFn,
                  thresh: float = 0.45) -> float:
    """저평판(rep < thresh) 진입 후 회복 속도 ∈ [0,1].

    각 라운드 끝에서 ``rep_fn``으로 전 에이전트 평판을 누적 prefix로 재계산하고, 어떤
    에이전트가 임계치 아래로 떨어지면 '저평판 진입' 이벤트를 연다. 이후 임계치 이상으로
    돌아오면 그 회복에 ``1/Δrounds`` 점수(빠를수록 높음), 끝까지 못 돌아오면 0점. 모든
    진입 이벤트의 평균이 회복률 — 회복 이벤트가 하나도 없으면(저평판 진입 자체가 없음) 0.0.
    """
    if not log:
        return 0.0
    rounds = _round_indices(log, n)
    last = rounds[-1]
    agents = list(dict.fromkeys(a for a, _, _ in log))  # 등장 순 고유
    # 라운드별 prefix 평판 궤적
    traj: dict[str, list[float]] = {a: [] for a in agents}
    for r in range(last + 1):
        prefix = SharedState(commons={"n_agents": n})
        prefix.turn_log = [e for e, ri in zip(log, rounds) if ri <= r]
        for a in agents:
            traj[a].append(rep_fn(a, prefix)[0])
    # 진입(below)→회복(>=thresh) 이벤트 점수화
    scores: list[float] = []
    for a in agents:
        seq = traj[a]
        enter = None
        for r, rep in enumerate(seq):
            if enter is None and rep < thresh:
                enter = r
            elif enter is not None and rep >= thresh:
                scores.append(1.0 / (r - enter))  # 빠른 회복일수록 큼
                enter = None
        if enter is not None:  # 끝까지 저평판 → 회복 실패 0점
            scores.append(0.0)
    if not scores:
        return 0.0
    return sum(scores) / len(scores)
