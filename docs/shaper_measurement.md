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

## 다중 시드 + 95% CI (N=10) — N=1을 통계로 교정

N=1 점추정의 한계를 보완하려 `--seeds 10 --temp 0.7`로 재측정(완료성공률=전원 완료한 에피소드
비율, Wilson CI; top_share=평균, 정규근사 CI). **결과는 N=1 헤드라인을 뒤집었다 — CI가 존재하는 이유.**

```
model=z-ai/glm-4.6  agents=3  rounds=4  seeds=10  temp=0.7  (95% CI)
condition              완료성공률 [95% CI]        top_share 평균 [95% CI]
baseline               0.30 [0.11, 0.60]         0.800 [0.600, 1.000]
superordinate (③)      0.00 [0.00, 0.28]         0.436 [0.382, 0.490]   ← CI 분리 ✓
accountability (④)     0.20 [0.06, 0.51]         0.614 [0.463, 0.765]
reputation_feedback    0.60 [0.31, 0.83]         0.600 [0.386, 0.813]
stack                  0.00 [0.00, 0.28]         0.668 [0.522, 0.814]
```

### 해석 (CI 기준, 정직하게)

- **통계적으로 견고한 단 하나: ③ 상위 정체성의 top_share 감소.** 0.800→0.436, CI [0.382,0.490]가
  baseline CI [0.600,1.000]와 **겹치지 않음** → 요청 독점을 유의하게 줄인다. 유일하게 깨끗한 효과.
  **단, 완료성공률은 0/10으로 붕괴** — 4라운드 안에서 너무 고르게 나눠 아무도 과업을 못 끝냄
  (공정성↑ ↔ 처리량↓ **트레이드오프**). 즉 ③은 "독점은 막지만 그 자체로 welfare를 주진 않는다".
- **reputation_feedback = 방향성 있으나 미유의.** 완료성공률이 0.30→**0.60으로 2배**지만 CI가
  baseline과 겹친다([0.31,0.83] vs [0.11,0.60]) → 유망하지만 N=10에선 통계적으로 확정 못 함.
- **④ 책임성 = null.** 두 지표 모두 baseline과 분리 안 됨(N=1의 무효 결과와 일치).
- **stack = 역효과 재현.** 완료성공률 0/10. 사회 개입 과적층이 협응을 무너뜨림(§5.4).

### ⚠️ N=1이 틀렸던 이유 (중요)

단일 시드(N=1)에서는 reputation_feedback가 top_share 0.33·완료율 1.00으로 "최강·완전 협력"처럼
보였다. **N=10 CI는 그것이 운 좋은 한 표본이었음을 드러낸다** — 실제 효과는 더 약하고 잡음이 크다.
LLM은 temp>0에서 분산이 크므로 **단일 실행 수치를 신뢰하면 안 된다.** 이 교정이 multi-seed의 존재 이유.

## ⚠️ 한계

- N=10도 **소표본**. 완료성공률은 0/10~6/10 구간이라 Wilson CI가 넓다. 더 강한 주장(예: 평판
  되먹임이 welfare를 유의하게 올린다)에는 N≥30 또는 라운드↑(throughput 여유)가 필요.
- 측정 스크립트는 부분 실패에 견고(한 조건이 402로 죽어도 성공분 집계, 전부 실패면 FAILED).
- mock(`make_framing_aware_script`)은 plumbing/회귀 전용. 실 LLM의 진짜 감응이 측정 대상이며 위 표가 답.

## 재현

```bash
set -a; . <(grep -E '^OPENROUTER_API_KEY=' /mnt/d/projects/A2A/oldman_agent/.env); set +a
.venv/bin/python scripts/measure_shapers.py --model z-ai/glm-4.6 --agents 3 --rounds 4
```

키는 환경변수로만 읽고 절대 인쇄하지 않는다. 실 LLM은 호출당 과금되므로 opt-in.
