# Welfare-rescue 스윕 — 결과 (완전판: GLM-4.7-flash, N=15)

> ✅ **완전판 갱신 (2026-06-23, 크레딧 충전 후 재실행).** 전 영역(catastrophic 포함) + 순열검정·Holm 완비. 원자료 [`verify_welfare_rescue.json`](verify_welfare_rescue.json)(독립 재계산 0 불일치). **실행:** GLM-4.7-flash(reasoning off), temp 0.7, 3ag, rounds=8, N=15. (아래 §는 이전 glm-4.6 *부분* INTERIM — 출처로 보존, 모델·결과 일부 상이.)

## 완전판 결과 표 (GLM-4.7-flash, N=15)

| 영역 (희소도) | pool | none welfare/top | cap_flat welfare/top | cap_quad welfare/top |
|---|---|---|---|---|
| **tight** s=1.0 | 360 | **0.73** / 0.585 | 0.73 / 0.360 | 0.67 / 0.375 |
| **scarce** s=0.5 | 180 | **0.33** / 0.667 | **0.00** / 0.383 | **0.00** / 0.390 |
| **catastrophic** s=0.33 | 118 | **0.00** / **1.000** | 0.00 / 0.492 | 0.00 / 0.481 |

**Holm 유의(2개):** welfare cap_flat vs none @ scarce (Δ=−0.33, **p_holm=.0006**); welfare cap_quad vs none @ scarce (Δ=−0.33, **p_holm=.0006**). tight·catastrophic welfare 대조는 모두 ns.

## 완전판 핵심 결론

1. **캡은 welfare를 구하지 못한다 — 확정.** scarce에서 캡이 welfare를 *유의하게 해침*(Δ=−0.33, p_holm=.0006, 이제 추론통계). tight에선 캡≈none(무해), catastrophic에선 전원 0(풀이 누구도 완주 못 시킴). 어느 영역에서도 +(rescue)로 뒤집히지 않음.
2. **그러나 캡은 *모든 영역에서* 공정성을 산다 — catastrophic 포함.** top-share none→cap: tight 0.585→0.36, scarce 0.667→0.38, **catastrophic 1.000(완전 독점)→0.49(반토막)**. *분리(dissociation)* 확정: 캡은 공정성 도구이지 완주-welfare 도구가 아니며, welfare 대가는 *희소(scarce)에서만* 유의.
3. **모델 차이(중요):** GLM-4.7-flash는 glm-4.6보다 **greed가 약함**(none welfare tight 0.73, scarce에서야 무너짐). 그래서 *tight에서 캡이 welfare를 해친다*던 V6(glm-4.6) 결과는 **모델·greed강도 의존** — flash에선 tight 무해, scarce에서만 해로움. "캡이 welfare를 해친다"의 *조건*이 더 날카로워졌다.

---

## (이하: 이전 glm-4.6 부분 INTERIM — 출처 보존)

# Welfare-rescue 스윕 — 결과 (부분, INTERIM · glm-4.6)

> 플랜 리뷰가 선택한 첫 실험([`design_identity_dao.md`](design_identity_dao.md) §5 Phase A′). **질문:** V6의 "출력 캡이 welfare를 해친다"가 *config 의존*인가 — 공유 풀이 희소해질수록 캡이 welfare를 *구하는가, 더 해치는가*?
>
> **실행:** 실제 GLM-4.6, temp 0.7, 3 에이전트, workload=120, rounds=8, N=10. 희소도 `s = pool/(n·workload)`를 tight→scarce→catastrophic으로 스윕. 하니스 `scripts/verify_claims.py welfare_rescue`.
>
> ⚠️ **상태: 부분 결과.** 3개 영역 중 **tight·scarce(8/9 셀) 완료**, 마지막 **catastrophic 영역에서 OpenRouter 402(크레딧 소진)로 중단**. 게다가 `_seeded`가 전(全)-시드 실패 시 예외를 던져 크래시 → `verify_welfare_rescue.json`이 **저장되지 못함**(완료 영역 데이터도 파일로는 유실). 아래 수치는 실행 로그(`/tmp/wr.log`)에서 가져온 셀별 평균·bootstrap CI다. **원시 배열이 없어 순열검정·Holm은 이번엔 수행 못 함** — 기술통계 + bootstrap CI만 보고한다. catastrophic 영역과 추론통계는 크레딧 충전 후 재실행 필요(§재현).

---

## 결과 표 (means, welfare는 bootstrap 95% CI)

| 영역 (희소도) | pool | arm | welfare(완료율) [95% CI] | top-share(독점) | Δwelfare vs none |
|---|---|---|---|---|---|
| **tight** s=1.0 | 360 | none | **0.73** [0.53, 0.93] | 0.600 | — |
| (slack 0, =V6 조건) | | cap_flat(=더미캡) | 0.53 [0.43, 0.63] | 0.432 | **−0.20** |
| | | cap_quad(볼록감쇠) | 0.63 [0.57, 0.67] | 0.409 | −0.10 |
| **scarce** s=0.5 | 180 | none | **0.33** [0.33, 0.33] | 0.667 | — |
| (slack −180) | | cap_flat | 0.10 [0.00, 0.20] | 0.554 | **−0.23** |
| | | cap_quad (n=8) | 0.00 [0.00, 0.00] | 0.477 | **−0.33** |
| **catastrophic** s=0.33 | 118 | — | *402 크레딧 소진으로 미실행* | — | — |

---

## 분석 — 핵심 결론(부분)

**1. "캡이 welfare를 구한다" 가설은 (완료-welfare에 대해) 반증되는 방향이다.** 부호가 뒤집히기는커녕, **캡의 welfare 비용이 희소할수록 더 커진다**: cap_flat의 Δwelfare는 tight −0.20 → scarce −0.23, cap_quad는 −0.10 → −0.33. 캡은 어느 영역에서도 완료-welfare를 *구하지 못했고*, 희소 영역에서 오히려 *더 해쳤다*.

**2. 메커니즘 = 완료율의 all-or-nothing 트랩(설계 시 예측).** 완료-welfare는 "에이전트가 workload(120)를 *전부* 채웠는가"의 비율이다. 희소 풀(pool 180 < 수요 360)에서:
- **무규제(none):** 탐욕이 풀을 선점 → *1명*이 workload를 채워 완주(welfare ≈ 0.33), 나머지는 굶음.
- **캡(fair):** 풀을 고르게 나눠 → *전원 부분완료*(각자 120 미만) → **아무도 완주 못함**(welfare → 0.10/0.00).
즉 희소할수록 "공정 분배 = 전원 미완주", "탐욕 = 1명이라도 완주"가 되어 캡이 완료-welfare를 깎는다.

**3. 그러나 캡은 *공정성*은 일관되게 산다.** top-share(독점)는 모든 영역에서 캡이 낮춘다: tight 0.600→0.41~0.43, scarce 0.667→0.48~0.55. **분리(dissociation)가 핵심 발견:** 캡은 *공정성(독점↓)*은 사지만 *완료-welfare*는 못 사며, 그 welfare 대가는 희소할수록 커진다. V6의 "캡이 welfare를 해친다"는 단순 config 아티팩트가 아니라 **희소도에 따라 *심화*되는 구조적 트레이드오프**다(완료를 어떻게 정의하느냐에 달림).

**4. (2차) 곡선이 중요한가 — 약한 신호.** tight 영역에서 **cap_quad가 cap_flat을 파레토 지배**: welfare 0.63 > 0.53 *이면서* top 0.409 < 0.432 — 볼록(graduated) 캡이 완주 가능한 에이전트를 덜 throttle한다. 그러나 scarce에선 역전(quad welfare 0.00 < flat 0.10) — 더 강한 공정성을 위해 더 많은 welfare를 포기. **N=10·CI 겹침·순열검정 부재**로 유의하다 주장할 수 없다(이번 실험의 1차 질문도 아님).

---

## 한계 (정직)

- **catastrophic 영역 누락.** s=0.33(pool 118 < workload 120)에선 hog조차 완주 불가 → none welfare도 0으로 떨어져 *모든 arm이 welfare 0*, 차이는 공정성(top-share)만 남을 것으로 예상되나 **측정 못 함**. 1차 가설의 가장 극단 지점이 비어 있다.
- **추론통계 없음.** 크래시로 원시 반복별 배열이 저장되지 않아 순열검정·Holm 미수행. 위 결론은 *기술통계 + bootstrap CI* 수준이다(단, tight/scarce의 welfare 격차는 CI로도 방향이 뚜렷).
- **저표본·1셀 손실.** N=10(V6는 30); cap_quad@scarce는 2시드 실패로 n=8.
- **단일 모델·시나리오·n=3.** V6와 동일한 일반화 한계. n=3은 특히 약한 작동점.
- **하니스 버그(교훈).** `_seeded`가 전-시드 실패 시 raise → 한 셀의 실패가 *완료된 셀의 JSON 저장까지* 막았다. 부분 결과를 저장하도록 고쳐야 재실행이 안전하다(§재현에서 수정).

---

## 재현 / 다음 단계

1. **하니스 수정:** 셀 실패 시 크래시 대신 *부분 결과를 저장*하고 중단(이번 커밋에 포함).
2. **크레딧 충전 후 재실행** (catastrophic 포함, 가능하면 N≥20):
   ```
   set -a; . <(grep -E '^OPENROUTER_API_KEY=' /mnt/d/projects/A2A/oldman_agent/.env); set +a
   .venv/bin/python -u scripts/verify_claims.py welfare_rescue --seeds 20 \
       --rounds 8 --out docs/verify_welfare_rescue.json
   ```
   재실행 시 원시 배열·순열검정·Holm이 JSON에 저장되어 위 기술통계 결론을 추론통계로 확정/반증할 수 있다.
3. **메트릭 보강 제안:** 완료-welfare의 all-or-nothing 트랩 때문에, *부분 진척(total delivered / 총 workload)*과 *Jain(전달)*을 2차 welfare 지표로 함께 보고하면 "캡이 throughput은 보존하되 완주만 못 시키는지"를 분리할 수 있다.

*아티팩트: 실행 로그 `/tmp/wr.log`(원본), 하니스 [`scripts/verify_claims.py`](../scripts/verify_claims.py) `run_welfare_rescue`. 설계 [`design_identity_dao.md`](design_identity_dao.md) §5.*
