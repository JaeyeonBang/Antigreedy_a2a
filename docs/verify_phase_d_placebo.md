# Phase D 위약 대조 — 역효과는 "군집 내용"이 아니라 "분열 배너 주입" 때문이다

> [`verify_phase_d.md`](verify_phase_d.md)의 후속 귀무검정. **질문:** phase_d에서 `emergent_identity`는 *역효과*(독점↑·welfare↓, 카스트화)였다. 그 해악이 (a) 군집이 *실제 탐욕 행동을 반영*해서인가, 아니면 (b) *어떤 군집 서사든*(거짓이라도) 주입하면 생기는가?
>
> **설계:** `placebo_cluster` = emergent와 **배너 문구·군집 크기·상위 목표가 모두 동일**하되, 군집 멤버십만 **무작위**(state에서 결정론적 시드). 핵심 대조 = **emergent vs placebo** — 차이 없으면 (b) *주입 기제 자체*가 원인(내용 무관), placebo만 무해하면 (a) *행동기반 caste-ification*이 진짜 원인.
>
> **실행:** 실제 **GLM-4.7-flash**(reasoning off), temp 0.7, 3 에이전트, pool=360, workload=120, rounds=8, **N=30**, 공통 baseline. 원자료·bootstrap·순열·Holm = [`docs/verify_phase_d_placebo.json`](verify_phase_d_placebo.json)(독립 재계산 **0 불일치** 검증).

## 결과 표

| arm | welfare [boot 95% CI] | top-share(독점) [boot 95% CI] | 비고 |
|---|---|---|---|
| none (무규제) | 0.93 [0.84, 1.00] | 0.400 [0.333, 0.489] | 기준선 |
| **emergent (실제 행동 군집)** ★ | 0.77 [0.67, 0.86] | **0.511** [0.422, 0.610] | 독점 최고 — *역효과* |
| **placebo (무작위 군집·동일 배너)** ★ | 0.80 [0.71, 0.89] | **0.450** [0.376, 0.535] | emergent와 none 사이 |
| neutral_filler (무내용 대조) | 0.97 [0.91, 1.00] | 0.357 [0.333, 0.403] | 또 1등(거의 공정) |

서열: **emergent(0.511) > placebo(0.450) > none(0.400) > filler(0.357)**.

## Holm 보정 결과 (유의 1개)

| 대조 | p | p_holm | 판정 |
|---|---|---|---|
| top: **emergent vs neutral_filler** (역효과 재현) | .0052 | **.0312** | ✅ emergent가 무내용 배너보다 **유의하게 독점↑** |
| top: placebo vs neutral_filler | .0454 | .227 | ns (보정 후 소멸) |
| top: emergent vs none (역효과 재현) | .0773 | .309 | ns (방향 맞으나 미유의) |
| **top: emergent vs placebo** (행동신호 순효과) | .3525 | **1.00** | **ns → 실제 군집과 무작위 군집을 구별 못 함** |
| top: placebo vs none (거짓군집만으로 변하나) | .3763 | 1.00 | ns |
| welfare: emergent vs placebo | .6930 | 1.00 | ns |

## 분석 — 핵심 결론

**1. 역효과의 방향은 재현됐다.** emergent는 또 독점 1위(0.511)였고, 무내용 길이대조(neutral_filler 0.357)보다 **유의하게 나빴다**(p_holm=.031). phase_d(emergent 0.585 > filler 0.333, p_holm=.0006)의 헤드라인이 *독립 시드 재실행*에서 방향·유의성 모두 살아남았다.

**2. 그러나 "행동기반 군집"은 해악의 원인이 아니다.** 핵심 대조 **emergent vs placebo가 무유의**(p_holm=1.0; 0.511 vs 0.450)다. 군집 멤버십을 **무작위 잡음으로 바꿔도**(같은 배너·같은 군집 크기) 결과가 emergent와 **구별되지 않는다**. 즉 "관측된 탐욕을 정확히 짚어 그 부류에 동화시킨다"는 자기범주화 경로가 *필요* 조건이 아니다 — **거짓 군집도 같은 해악**을 낸다.

**3. 그러므로 해악을 나르는 것은 *분열적 "OBSERVED GROUPS" 배너의 주입 행위 자체*다.** "너는 [X 부류]와 같고 [다른 부류]는 떨어져 행동한다"는 *us-vs-them 프레임*이 — 그게 진실이든 날조든 — 독점을 끌어올린다. **설계의 핵심 전제("정체성을 행동에서 *창발*시키면 더 정직하다")는 측정 가능한 이득을 주지 못했다**: 무작위 분할 대비 0 (p_holm=1.0).

**4. neutral_filler가 또 이겼다.** 무내용 배너가 welfare 0.97·독점 0.357로 최저 독점. *분열 없는* 배너는 무해하고 *분열* 배너만 해롭다는 대비가 2번 실험에서 일관된다.

## 한계 (정직)

- **검정력 부족 — "동일"이 아니라 "차이 미검출".** emergent−placebo 점추정 격차(0.061)는 0이 아니라 살짝 emergent가 나쁜 쪽이다; N=30에선 이 격차를 분해할 힘이 없다. 또한 emergent−none도 보정 후 미유의(p_holm=.309)라 이 재현은 phase_d보다 *약하다*. 정직한 진술 = **"행동-도출이 해악을 키운다는 *증거가 없다*"**(증거의 부재 ≠ 동일성의 증명).
- **n=3 위약의 약점:** 2-1 분할에서 무작위 짝이 우연히 실제 짝과 같을 확률 1/3 → 멤버십은 *기댓값상*으로만 행동과 탈상관. 에이전트 수를 늘리면(예: 6) 위약이 더 깨끗해지고 Leiden 군집도 비로소 비자명해진다.
- **모델·곡선 stand-in:** GLM-4.7-flash(reasoning off), 군집러는 순수 파이썬 단일-연결(Leiden 자리표시자). n=3에선 3노드 그래프라 Leiden↔단일연결이 사실상 동일 — Leiden 교체는 에이전트 수를 키운 뒤에야 의미가 있다.
- **neutral_filler degenerate 가능성** 그대로(verify_phase_d.md §한계 참조).

## 강건성 — n=6 재현 (1/3 우연일치 한계 해소)

n=3 위약의 약점(2-1 분할서 무작위 짝이 우연히 실제 짝과 같을 확률 1/3)을 없애려 **에이전트 6**으로 재실행(같은 glm-4.7-flash·N=30, pool=720, workload=120; [`verify_phase_d_placebo_n6.json`](verify_phase_d_placebo_n6.json), 재계산 0 불일치). 공정 몫이 1/6≈0.167이라 독점 수치는 전반적으로 낮다.

| arm | welfare | top-share(독점) |
|---|---|---|
| none | 0.92 | 0.235 |
| **emergent** | 0.81 | **0.305** |
| **placebo** | 0.83 | **0.280** |
| neutral_filler | 0.98 | 0.174 |

| 대조 | p | p_holm | 판정 |
|---|---|---|---|
| top: **placebo vs neutral_filler** | .0003 | **.0018** | ✅ **NEW** — *가짜* 군집 배너도 무내용보다 유의하게 독점↑ |
| top: **emergent vs neutral_filler** | .0036 | **.0180** | ✅ 역효과 재현(n=3과 동일) |
| top: emergent vs none | .199 | .797 | ns |
| top: placebo vs none | .329 | .988 | ns |
| **top: emergent vs placebo** | .663 | **1.00** | **ns → 더 명확히 구별 불가**(p 0.35→0.66) |
| welfare: emergent vs placebo | .818 | 1.00 | ns |

**해석:** 서열(emergent>placebo>none>filler)·핵심 결론이 그대로 재현되고 *더 강해진다*. (1) `emergent vs placebo`가 더 명확히 무유의(p 0.66) — 위약 멤버십이 진짜로 탈상관된 규모에서도 실제 군집과 통계적으로 같다. (2) **새로** `placebo vs neutral_filler`가 유의 → *가짜* 군집 배너조차 무내용 배너보다 독점을 유의하게 올린다 = "us-vs-them 분열 프레임 자체가 해롭다"의 직접 증거. 에이전트 6은 실제 하위공동체가 형성될 수 있는 규모(Leiden이 비자명해지는 지점)인데도 **행동-도출 군집이 무작위 분할 대비 이점 0**.

## 결론

**위약 대조는 phase_d 역효과를 *강화*하되 그 *원인을 재배치*한다.** 해악은 "행동에서 창발한 정체성"이라는 설계 자랑거리가 아니라 — **어떤 군집이든 us-vs-them으로 *분열시켜 알리는 행위*** 자체에서 온다(거짓 군집도 동등하게 해롭다). 따라서 anti-greedy 레버로서 *창발* 정체성은 부과 정체성 대비 이점이 없을 뿐 아니라, "정확한 행동 신호"라는 정당화조차 데이터가 받쳐주지 않는다. **이 결론은 에이전트 3·6 두 규모에서 재현됐다**(위 §강건성).

**범위(scope) — 의도적 한정.** 본 결과는 **glm-4.7-flash(reasoning off) 기준**으로 보고한다. 단일 모델 결과이며 모델 일반성은 *주장하지 않는다*. (glm-4.6 동일모델 재현은 V6 논문과의 직접 비교가 필요할 때만 가치가 있고, 진짜 일반성 검증이라면 같은 GLM 변종보다 다른 계열/티어 모델이 더 강한 증거다 — 둘 다 현재 범위 밖.) 별개 작업: 실제 Leiden 군집러로 stand-in 교체(에이전트 수를 더 키운 뒤).

*아티팩트: [`verify_phase_d_placebo.json`](verify_phase_d_placebo.json)(원자료·통계), 하니스 [`scripts/verify_claims.py`](../scripts/verify_claims.py) `run_phase_d_placebo`, 셰이퍼 [`prompt_shapers.py`](../antigreedy/scenario/prompt_shapers.py) `placebo_cluster` · 군집 [`reputation_identity.py`](../antigreedy/scenario/reputation_identity.py) `placebo_clusters`.*
