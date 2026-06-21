# 행동(입력)측 거버넌스 측정 — 제안③④ + 평판 되먹임 채널

외부 리뷰가 지적한 빈틈: 사회 정책(평판·가십)이 행동의 *출력*만 cap하고 신호를 당사자에게
**되먹이지 않아** 시도(attempted) 자체는 변하지 않는다 = "이름만 그럴싸한 rate-limiter".

`PromptShaper`(`antigreedy/scenario/prompt_shapers.py`)는 반대 레버 — `SharedState`를 read-only로
읽어 backend 호출 직전 **프롬프트를 재구성**한다. 측정은 **출력 정책 0개**(`chain_intercept([])`)에서
수행 → `jain_delivered == jain_attempted` → 모든 변화는 **enforcement가 아니라 행동 변화**.

## 실측 (실 LLM)

```
model=z-ai/glm-4.6  agents=3  pool=360  workload=120  rounds=4  (self-interested 페르소나)
condition             top_share  jain_att  jain_del   완료율  starved
----------------------------------------------------------------------
baseline                  0.667     0.600     0.600    0.67        1
superordinate (③)         0.526     0.665     0.665    0.67        1   (Δtop -0.141)
accountability (④)        0.667     0.600     0.600    0.67        1   (Δtop +0.000)
reputation_feedback       0.333     1.000     1.000    1.00        0   (Δtop -0.334)
stack (③+④+평판)          1.000     0.333     0.333    0.33        2   (Δtop +0.333)
```

## 해석 (정직하게)

- **평판 되먹임 = 최강.** 출력 cap 0개인데도 평판을 *되먹이기만* 했더니 GLM이 완전 공정 공유로
  전환(완료율 0.67→1.00, starved 1→0, jain 0.60→1.00). 외부 리뷰가 지적한 폐회로를 닫자
  **행동 채널이 실제로 움직였다**. 사용자가 요청한 바로 그 채널.
- **상위 정체성(③) = 약한 개선.** top_share 0.667→0.526. 공유 의식은 생겼으나 starved를 구하진 못함.
- **책임성(④) = 효과 0 (정직한 negative).** "정당화 요구" cue만으론 GLM 행동 불변. 관찰·정당화
  신호는 *결과/되먹임*이 없으면 공허. 평판 되먹임과의 대비가 핵심 통찰.
- **스택 = 역효과.** 셋을 동시에 쌓으니 baseline보다 나빠짐(완료율 0.33). §5.4 "사회 개입
  과적층 역효과"를 실측 재현. 교훈: 행동측 레버는 **최소·표적**이 낫다.

## 다중 시드 + 95% CI (진행 중 — 크레딧 소진으로 부분 완료)

N=1 한계를 보완하려 `--seeds 6 --temp 0.7`로 재측정(완료성공률=전원 완료한 에피소드 비율,
Wilson CI; top_share=평균, 정규근사 CI). **OpenRouter 잔액 소진(402 Payment Required)**으로
baseline만 6시드 완료하고 나머지 조건은 중단됨 — 정직하게 부분 결과만 보고한다.

```
model=z-ai/glm-4.6  agents=3  rounds=4  seeds=6  temp=0.7  (95% CI)
condition              완료성공률 [95% CI]        top_share 평균 [95% CI]
baseline               0.17 [0.03, 0.56]         0.785 [0.518, 1.052]
superordinate          (미측정 — 402)
accountability         (미측정 — 402)
reputation_feedback    (미측정 — 402)
stack                  (미측정 — 402)
```

- baseline 완료성공률 **0.17**(6에피소드 중 1회만 전원 완료) → temp 0.7에서 탐욕이 **단일
  시드보다 더 심하고 분산이 크다**(CI 0.03~0.56). 문제(greed)의 실재성은 더 강해졌다.
- 단, **shaper 조건들의 CI는 아직 없다** → 헤드라인(평판 되먹임 0.33/완료 1.00)은 여전히
  N=1 점추정. CI로 baseline과 분리되는지는 **크레딧 충전 후 재실행 필요**.
- 측정 스크립트는 이제 **부분 실패에 견고**: 한 조건이 402로 죽어도 성공분으로 집계하고
  나머지는 계속, 전부 실패면 FAILED로 표시(가짜 0으로 위장하지 않음).

재실행(크레딧 복구 후): 위 '재현' 명령에 `--seeds 10 --temp 0.7` 추가.

## ⚠️ 한계

- **헤드라인은 아직 단일 시드(N=1) 점추정**. multi-seed CI는 baseline만 확보(402로 중단).
  통계적 분리 검정은 크레딧 충전 후 완료 예정 — 현재는 방향성·메커니즘 데모로 읽을 것.
- mock(`make_framing_aware_script`)은 plumbing/회귀 전용(cue 감응을 결정론적으로 보장).
  실 LLM의 *진짜* 감응 여부가 측정 대상이며 위 표가 그 답.

## 재현

```bash
set -a; . <(grep -E '^OPENROUTER_API_KEY=' /mnt/d/projects/A2A/oldman_agent/.env); set +a
.venv/bin/python scripts/measure_shapers.py --model z-ai/glm-4.6 --agents 3 --rounds 4
```

키는 환경변수로만 읽고 절대 인쇄하지 않는다. 실 LLM은 호출당 과금되므로 opt-in.
