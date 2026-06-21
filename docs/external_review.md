# 외부 리뷰(Outer Voice) & 보완 방안

> 독립 리뷰어(회의적 시니어 MAS 연구자)에게 현재 프로세스 검토를 받음(2026-06-16).
> 아래는 리뷰 요지 + **반영 현황**.

## 리뷰 핵심 (요약)

1. **타당성 위협 — "greed"를 측정하는 게 맞나?** 현재 dominator는 `make_meeting_script`에
   하드코딩된 *상수 길이 스패머*다. 따라서 `top_share`는 "캡이 상수 스패머를 얼마나 통과시켰나"
   = **캡 산술의 함수**이지 에이전트 전략의 함수가 아니다. 사회 전략 순위(평판≫조건부≫보편화)는
   *메커니즘 효능* 순위가 아니라 *캡 세기* 순위.
2. **모든 사회 정책이 결국 "per-turn 토큰 비율로 truncate/deny" 한 레버로 환원**된다.
   gossip/ostracism/universalization 이벤트는 *방송되지만 에이전트에게 피드백되지 않음* →
   진짜 사회 메커니즘(대상의 *미래 행동*을 바꿈)이 아니라 *재명명된 rate-limiter*.
3. **판별 실험**: ① **cap-equivalent null** — 사회 정책을 `cap=k·remaining` 더미 캡으로 바꿔
   같은 결과가 나오면 사회 메커니즘은 기여 0. ② **실 LLM + 피드백 채널** — reputation 신호를
   프롬프트에 노출하고 **`jain_attempted`(요청 채널)** 측정. (gate_calibration.md가 이미 단서:
   quota에서 *attempted* Jain은 거의 불변, *delivered*만 점프 → **집행이지 행동 변화 아님**.)
4. **지표** — `jain_delivered`는 정책이 직접 만든 출력을 채점하는 **순환적** 지표. **welfare /
   과업 완료 / starvation(maximin) / 결정 품질 / 거버넌스의 부작용(정직한 에이전트 피해)**이 빠짐.
   `jain_attempted`와 welfare를 앞세우고 `jain_delivered`는 "집행이 binding 됐나" 진단으로 강등.
5. **거버넌스 설계** — InterceptPoint 한 계약 + 단일 기록자 + read-only 평판은 **진짜 좋은 커널**.
   리스크: 체인의 multi-MODIFY에서 `token_estimate`가 재계산되지 않아 두 truncate 정책이 원본
   기준으로 이중 컷 가능(테스트 필요); read-only 평판은 front-load 후 침묵으로 회복 가능(게임 가능).
6. **신뢰성** — 결정론적 mock은 n=1(분산 0 → CI 불가). 모든 헤드라인 수치는 **실 LLM·M≥10·다모델**
   필요. README "GATE PASSED"가 `gate_report`의 verdict와 불일치 → 정정 필요.
7. **Top 5 개선(우선순위)**: ①cap-null 대조군 ②스크립트 dominator → 실 LLM self-interested +
   피드백 채널, `jain_attempted`/welfare 보고 ③welfare/결정품질/starvation 지표 추가
   ④resource-task 시나리오를 primary로 ⑤powered·multi-model·CI.

## 반영 현황 (이번에 처리)

| 리뷰 항목 | 반영 |
|---|---|
| #2·#4 resource-task 시나리오 (greed 창발, welfare) | ✅ `antigreedy/scenario/resource_task.py` 신설 — 각 에이전트가 하위 과업+공유 rate-limited 풀. greed = 자기 과업 먼저 끝내려 풀 독점 → 타 에이전트 **starvation** |
| #4 welfare/완료/starvation 지표 | ✅ `completion_rate, welfare, starved, jain_attempted(요청), jain_delivered(부여)` 모두 방출 |
| #3·#7② 실 LLM에서 greed 창발 | ✅ **GLM(z-ai/glm-4.6)** 실측: "먼저 끝내면 보너스" 페르소나 A가 **풀 전체를 요청·독점**(스크립트 없이 창발). 무규제 완료 0.25(3 starved) → quota 0.50 |
| #1·#3 attempted vs delivered 이중 채널 | ✅ GLM quota에서 A는 **여전히 260 요청(행동 불변)** 이나 집행으로 캡 → `jain_attempted=0.56` 로 "집행이지 행동 변화 아님"이 가시화 |
| #7③ welfare를 결과 지표로 | ✅ 완료율/starvation을 1급 지표로 (top_share/Jain은 분배 지표로 병기) |

## 남은 보완 (다음 단계, 미처리)

- **cap-equivalent null 대조군**(리뷰 #1·#7①): 사회 정책 vs 동등 더미 캡 비교 — *사회 메커니즘이
  캡 산술 이상을 하는지* 가리는 결정적 실험. **최우선**.
- **reputation 피드백 채널**: 평판/배제 신호를 프롬프트에 노출해 실 LLM의 *attempted* 채널이
  실제로 바뀌는지(행동 변화) 측정.
- **multi-model · M≥10 · CI**: GLM 외 모델 추가, 반복 시행 + Wilson CI.
- **README "GATE PASSED" ↔ gate_report 불일치 정정**, 체인 multi-MODIFY 이중컷 테스트.
- **결정 품질(LLM-judge)**: "공정하지만 합의 실패(stalemate)"가 "공정+합의"보다 낮게 채점되도록.

> 결론(리뷰): 재사용 가능한 substrate와 정직한 negative들은 강점. 단 모든 "greed 감소" 수치는
> cap-null 대조군과 비-스크립트 에이전트가 *메커니즘이 산술 이상을 함*을 증명하기 전까지 **잠정**.
