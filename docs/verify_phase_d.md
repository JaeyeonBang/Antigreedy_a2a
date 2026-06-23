# Phase D 결과 — 창발 정체성은 작동하지 않았다 (오히려 역효과)

> 설계 [`design_identity_dao.md`](design_identity_dao.md) §3.4 / 구현 [`phase_d_report.html`](phase_d_report.html). **질문:** V6의 유일 생존 효과(부과된 "ONE TEAM")가 "정체성"인가 "지시"인가 — 정체성을 *관측 행동에서 창발*시켜(`emergent_identity`) 부과형(`imposed`=superordinate)·길이대조(`neutral_filler`)·무규제(`none`)와 비교.
>
> **실행:** 실제 **GLM-4.7-flash**(reasoning off), temp 0.7, 3 에이전트, pool=360, workload=120, rounds=8, **N=30**, 공통 baseline. 원자료·bootstrap·순열·Holm = [`docs/verify_phase_d.json`](verify_phase_d.json)(독립 재계산 0 불일치 검증).

## 결과 표

| arm | welfare [boot 95% CI] | top-share(독점) | 비고 |
|---|---|---|---|
| none (무규제) | 0.80 [0.69, 0.90] | **0.520** | 기준선 |
| imposed (부과 "ONE TEAM") | 0.77 [0.69, 0.84] | **0.395** | 독점 ↓ (방향성) |
| **emergent (창발 정체성)** ★ | 0.70 [0.59, 0.81] | **0.585** | 독점 ↑ — *역효과* |
| neutral_filler (무내용 대조) | 1.00 [1.00, 1.00] | 0.333 | 또 1등(완전 공정) |

## Holm 보정 결과 (유의 2개)

| 대조 | p | p_holm | 판정 |
|---|---|---|---|
| top: **emergent vs neutral_filler** | .0001 | **.0006** | ✅ emergent가 무내용 배너보다 **유의하게 독점↑** |
| top: **emergent vs imposed** | .0026 | **.013** | ✅ **emergent ≠ imposed** — 창발이 부과보다 유의하게 나쁨 |
| top: imposed vs none (V6 재현) | .040 | .158 | ns (방향 맞으나 flash·N=30서 미유의) |
| welfare: emergent vs imposed | .249 | .75 | ns |
| welfare: emergent vs none | .256 | .75 | ns |
| top: emergent vs none | .398 | .75 | **ns → 창발은 독점을 못 줄임** |

## 분석 — 핵심 결론

**1. 창발 정체성은 실패했다.** emergent는 독점을 줄이지 못했고(top 0.585 vs none 0.520, ns), **부과형(0.395)·무내용 배너(0.333) 둘 다보다 유의하게 *나빴다***(독점이 더 높음). "정체성을 데이터에서 창발시키면 부과형 효과를 재현하는가?"의 답은 **아니오, 정반대**다.

**2. 이것은 설계가 예측한 *카스트화 역효과*다.** `emergent_identity`는 "관측상 너는 [독식 부류]와 같고 [공정 부류]는 다르다"를 명시한다. 자기범주화 이론(related_work §C.2)대로, **"greedy 부류"로 범주화된 에이전트가 원형에 동화돼 *더* 독식**했을 가능성이 높다 — 우리가 §C.10·설계 §2.3에서 *새 위험*으로 경고한 바로 그 메커니즘이 실측으로 나타났다.

**3. "정체성 vs 지시" 분해:** 부과형(imposed)은 독점을 *방향상* 줄였으나(0.520→0.395) flash·N=30에서 Holm 미유의. 창발형은 *역효과*. → 적어도 이 v0(순수파이썬 군집)·이 모델에선, **정체성을 데이터로 창발시키는 것이 부과보다 못하다**. 효과는 "데이터-도출 정체성"이 아니라 (있다면) 부과된 *프레임/지시* 쪽에 있다.

**4. neutral_filler가 또 이겼다.** 무내용 배너가 welfare 1.00·독점 0.333(완전 공정). V6에서도 filler가 welfare 1등이었다 — **입력 배너의 효과가 기제 설계 때문이 아니라는 일관된 신호**. (단 flash는 4.6보다 덜 greedy해 filler→완전공정이 degenerate할 수 있음, §한계.)

## 한계 (정직)

- **모델·곡선 stand-in:** GLM-4.7-flash(reasoning off) — V6는 glm-4.6이므로 imposed 수치를 V6 superordinate(독점 0.65→0.41, p_holm<.001)와 *직접* 비교 불가(단, Phase D는 imposed baseline 내장이라 *내부 대조*는 유효). 클러스터러는 순수 파이썬 단일-연결 = Leiden 자리표시자 — Leiden으로 바꾸면 결과가 달라질 수 있다.
- **neutral_filler degenerate:** welfare 1.00/top 0.333이 30 에피소드 전부 동일 — flash가 filler의 "간결·평소대로" 지시를 매우 문자적으로 따른 *모델 아티팩트* 가능성. flash는 4.6보다 greed가 약함(none welfare 0.80 vs V6 0.66).
- **n=3·단일 시나리오.** "창발 정체성이 인과인가 상관인가"의 **위약-군집 귀무검정은 후속 실험에서 수행** → [`verify_phase_d_placebo.md`](verify_phase_d_placebo.md): emergent vs placebo 무유의(p_holm=1.0)로, 역효과는 *행동기반 군집 내용*이 아니라 *분열 배너 주입 자체*에서 옴이 드러났다.

## 결론

**창발 정체성(v0)은 anti-greedy 레버로 실패했고, 데이터는 카스트화 역효과 가설을 지지한다.** 이는 부정적이지만 *정보가 큰* 결과 — "정체성을 행동에서 창발시키면 더 낫다"는 직관을 반증하고, 부과형이 (있다면) 더 안전함을 시사한다. **후속 위약-군집 대조**([`verify_phase_d_placebo.md`](verify_phase_d_placebo.md))는 한 발 더 나아가: 역효과는 *행동기반 군집*이 아니라 *분열 배너 주입 자체*에서 오며(emergent≈placebo, p_holm=1.0), 창발 설계는 무작위 분할 대비 이점이 0이었다. 다음(선택): 에이전트 6+로 위약 정제·Leiden 비자명화 + glm-4.6 동일모델 재현.

*아티팩트: [`verify_phase_d.json`](verify_phase_d.json)(원자료·통계), 하니스 [`scripts/verify_claims.py`](../scripts/verify_claims.py) `run_phase_d`.*
