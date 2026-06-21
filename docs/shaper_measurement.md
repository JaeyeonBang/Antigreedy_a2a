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

## ⚠️ 한계

- **단일 시드(N=1) 시연**. temp=0.3, 3에이전트·4라운드. 통계적으로 검정된 결과가 아니다 —
  다음 단계 = multi-seed M≥10 + Wilson CI (외부 리뷰 권고). 방향성·메커니즘 데모로 읽을 것.
- mock(`make_framing_aware_script`)은 plumbing/회귀 전용(cue 감응을 결정론적으로 보장).
  실 LLM의 *진짜* 감응 여부가 측정 대상이며 위 표가 그 답.

## 재현

```bash
set -a; . <(grep -E '^OPENROUTER_API_KEY=' /mnt/d/projects/A2A/oldman_agent/.env); set +a
.venv/bin/python scripts/measure_shapers.py --model z-ai/glm-4.6 --agents 3 --rounds 4
```

키는 환경변수로만 읽고 절대 인쇄하지 않는다. 실 LLM은 호출당 과금되므로 opt-in.
