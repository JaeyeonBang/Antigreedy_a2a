# Phase 2 — Elder 원장 LLM-judge 검증 (glm-4.7-flash, N=20)

> 원자료: `docs/verify_elder.json` · 하니스: `scripts/verify_claims.py elder`
> 독립 재계산: 평균(top/welfare) 0 불일치, 순열검정 p 재현 일치.

## 한 줄 결론

**LLM-판관(judge) 평판은 rule·숫자앵커와 *유의하게 달랐다 — 그러나 더 나쁜 쪽으로*.** 근거 텍스트를 읽는
Elder judge를 섞으니(α=.5) 독점이 가장 높아지고(top 0.757) welfare가 무너졌다(0.33). 반대로 **순수 행동
평판(rule, α=1)이 최선**(welfare 0.95, top 0.367). 즉 judge는 "앵커일 뿐"을 넘어 *능동적 해악*이었다 —
**불변 원장이 judge의 *이른 오판*을 영구 동결**했기 때문(설계가 경고한 "ledger+judge error → caste").

## 결과 (4 arm × N=20, 3에이전트, rounds=8, pool=360)

| arm | 평판 | top-share(독점) | welfare(완료율) |
|---|---|---|---|
| `none` | — | 0.475 | 0.85 |
| `ledger_numbers` | α=.5, numeric 앵커 | 0.461 | 0.72 |
| `ledger_rule` | α=1, 순수 Beta 행동 | **0.367** | **0.95** |
| `ledger_elder` ★ | α=.5, 실 LLM judge | **0.757** | **0.33** |

bootstrap 95% CI: rule top [.33,.43] welfare [.87,1.00]; elder top [.66,.86] welfare [.33,.33](전 시드 동일 = *일관된* 실패).

### 순열검정 + Holm (유의 = p_holm<0.05)

| 대조 | p | p_holm | 판정 |
|---|---|---|---|
| **top ledger_elder vs ledger_rule** (judge가 신호 더하나) | .0001 | **.0007** | ✅ SIG (해로운 방향) |
| **welfare ledger_elder vs ledger_rule** | .0001 | **.0007** | ✅ SIG (해로운 방향) |
| **welfare ledger_elder vs ledger_numbers** | .0001 | **.0007** | ✅ SIG |
| **top ledger_elder vs ledger_numbers** (앵커 이상인가) | .0007 | **.0028** | ✅ SIG |
| **top ledger_elder vs none** | .0013 | **.0039** | ✅ SIG |
| top ledger_rule vs none | .181 | .362 | ns |
| welfare ledger_rule vs none | .254 | .362 | ns |

## 메커니즘 (실 LLM 진단 1회 — judge 점수 + 근거 직접 로깅)

한 에피소드를 실 backend로 돌려 judge 점수와 그 시점 평판을 찍었다:

```
Elder judge 점수(라운드 0, 에이전트별 1회): A=0.20, B=0.30, C=0.30
최종:  A share .40 rule .33 judge .20 → elder .27  EXCLUDED
       B share .30 rule .60 judge .30 → elder .45  EXCLUDED
       C share .30 rule .60 judge .30 → elder .45  EXCLUDED
```

- **judge는 *라운드 0*에 단 한 번 채점한다**(검소 설계). 그런데 greedy 페르소나 아래선 *모든* 에이전트의
  *첫* 근거가 자기중심적으로 들린다("내 과업을 먼저 끝내야 한다") → judge가 **전원에게 가혹한 점수**(0.2~0.3).
- **불변(append-only) 원장이 그 이른 오판을 *동결*한다.** 이후 B·C가 공정하게 행동해 rule 평판이 0.60으로
  올라도, 0.5·0.60 + 0.5·0.30 = **0.45로 끌려 내려가 배제**된다. judge의 초기 노이즈가 영구 페널티가 된다.
- 결과: 공정한 에이전트까지 배제되니 완료자가 줄어 **welfare 붕괴(0.33)**, 살아남은 쪽이 독점(top↑).
  **순수 rule(α=1)은 행동을 매 라운드 갱신**하므로 이 함정에 안 빠진다 → 최선.

## 해석

1. **judge는 "앵커"를 넘어 "해악"이었다.** V6 교훈("그럴싸한 사회 신호가 숫자 앵커와 구별 안 됨")의
   *강한* 버전: LLM judge는 앵커와 **유의하게 달랐지만**(SIG), 그 차이는 *유용한 신호가 아니라 동결된 노이즈*.
2. **불변성 × 판단오류 = 카스트(Phase 1의 자매 결과).** Phase 1은 *행동* 평판의 누적이 카스트를 만들었고,
   여기선 *LLM 판단*의 오류가 **불변 원장에 동결**돼 더 심한 카스트(공정한 에이전트까지 배제)를 만들었다.
3. **행동 > 말.** 매 라운드 갱신되는 행동 평판(rule)이, 한 번 읽은 근거 텍스트의 LLM 판단보다 거버넌스에서
   우월했다. "무엇을 말했나"보다 "무엇을 했나"가 더 견고한 신호.

## 한계 (정직)

- **judge 타이밍이 불리하다(라운드 0).** 검소(에피소드당 1회)를 위해 *첫* 턴에 채점하므로, 행동이 드러나기
  *전*에 판단한다 — judge에게 가장 불리한 시점. 후반 채점/다회 채점이면 결과가 나아질 수 있다(비용↑). 이건
  *judge 자체가 쓸모없다*가 아니라 **"이른·불변 판단이 위험하다"**는 결과로 읽어야 한다.
- **불변 원장은 설계상 선택**(불변성 위험을 노출하려는 의도). 가변/감쇠 원장이면 동결 함정이 풀릴 수 있다
  (Phase 1의 λ 망각을 judge 점수에도 적용 = 향후).
- **n=3 · glm-4.7-flash · resource_task.** V6와 동일 일반화 한계.
- **세탁/카스트갭 전체 실험은 미수행** — 비대칭 λ 메커니즘(`beta_reputation(lam_down)`)은 단위검증만.
