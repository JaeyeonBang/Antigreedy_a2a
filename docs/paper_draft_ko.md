# LLM 에이전트의 탐욕 거버넌스 효과 대부분은 측정 아티팩트다: 출력 강제 캡 vs 입력 프레이밍의 통제된 검정

*Most Greed-Governance Effects on LLM Agents Are Measurement Artifacts: A Controlled Test of Output Capping vs. Input Framing*

**상태:** Major-Revision 동료심사 이후의 Stage-4 개정본. 이전 초고의 헤드라인("입력 프레이밍이 출력 캡을 이긴다")은 **통제된 실험 내(within-experiment) 검정을 통과하지 못했고**, 근거가 뒷받침하는 결론으로 교체되었다. 모든 수치는 GLM-4.6 위에서 수행한 단일 공통-baseline 실험(V6, N=30)에서 나왔으며, bootstrap 신뢰구간 + 순열검정 + Holm 보정을 적용했다. 원자료는 `docs/verify_v6.json`에 있다.

---

## 초록

공유 자원(commons)을 두고 경쟁하는 LLM 에이전트는 "공유지의 비극"을 되살리며, 이를 다스리려는 연구가 빠르게 늘고 있다 — 출력측 강제(요청 제한, 캡, 평판·배제 기반 "사회" 정책)와 입력측 프레이밍(정체성, 책임성, 평판 되먹임)이 그것이다. 우리는 재사용 가능한 A2A 거버넌스 기반(substrate)을 구축했고, 무엇보다 이 분야가 대개 건너뛰는 *통제된* 실험을 수행했다: 모든 거버넌스 레버를 **단일 실험·단일 공통 baseline**에서 측정하고, **앵커링/길이 대조 프롬프트**, **bootstrap 신뢰구간**, 두-표본 **순열검정**, 다중비교를 위한 **Holm 보정**을 적용했다. 결과는 냉정하다. 사전에 지정한 9개 대조 중 보정을 통과한 것은 단 2개뿐이다: 상위 정체성(superordinate identity) 프롬프트는 독점을 견고하게 줄였고(top-share 0.65→0.41, p_holm<.001), 출력 "사회" 정책은 무규제 대비 welfare를 *오히려 낮췄다*(0.66→0.39, p_holm=.022). 나머지는 전부 아티팩트다: 분리-baseline 검정(N=24, p=.027)에서 유의해 보였던 평판 되먹임 프롬프트는, 공통 baseline에서는 무규제와 **구분되지 않으며**(welfare p=.61), 사회적 표현을 모두 뺀 *순수 숫자 앵커*와도 **구분되지 않는다**(p=.88) — 즉 그 효과는 사회적 기제가 아니라 지시-앵커링이다. *내용 없는 필러* 프롬프트가 모든 arm 중 welfare **최고점**을 기록했는데, 이는 입력 배너의 welfare 차이가 기제 설계 때문이 아님을 보여준다. 또한 출력 "사회" 정책은 공정성 측면에서 **단순 비례 캡(dumb cap)과 통계적으로 구분되지 않는다**(p=.13). 따라서 우리의 기여는 방법론적·부정적(negative)이다: 보고된 탐욕-거버넌스 효과 대부분은 실험 설계에 취약하고, 단 한 번의 결정적 실험이 우리 자신의 다중-시드 헤드라인 2개를 뒤집었으며, 통제·앵커대조·다중보정 설계만이 진짜 기제를 프롬프트 길이·baseline 추출 노이즈와 분리해 낸다.

**Abstract (English).** LLM agents competing over a shared commons revive the tragedy of the commons, and a growing literature proposes governance — output-side enforcement and input-side framing. We ran the controlled experiment the field usually skips: all levers against one shared baseline in a single run, with anchoring/length controls, bootstrap CIs, permutation tests, and Holm correction. Of nine pre-specified contrasts, only two survive: superordinate identity reduces monopoly (top 0.65→0.41, p_holm<.001) and an output "social" policy *reduces* welfare (0.66→0.39, p_holm=.022). The reputation-feedback "win" is baseline drift plus numeric anchoring; a contentless banner tops welfare; social ≈ dumb cap on fairness. The contribution is methodological and negative.

---

## 1. 서론

자율 LLM 에이전트는 A2A 프로토콜을 통해 점점 더 자원을 공유하며, 그 결과 공유지의 비극이 되살아난다 [Hammond et al. 2025; Piatti et al. 2024]. 여기서 생기는 *행동적 탐욕* — 공유 풀을 선점해 남을 굶기는 이기적 착취 [Vallinder & Hughes 2025] — 을 다스리려는 연구가 빠르게 늘고 있고, 크게 **출력 강제**(캡, 공정 큐잉, 평판·배제 정책)와 **입력 프레이밍**(정체성, 책임성, 평판 되먹임)으로 나뉜다. 논문들은 이 레버들이 "효과가 있다"고 보고한다. 우리는 *어느 레버가 더 나은지 측정*하려 했고, 이를 위한 테스트베드를 만들었으며 — 우리 자신의 단일-런 주장이 계속 뒤집히는 것을 겪은 뒤 — 더 어려운 문제는 **진짜 거버넌스 효과를 실험 아티팩트와 구별하는 일**임을 발견했다.

이 논문의 기여는 그 통제된 실험과 거기서 나온 부정적 결과다.
1. **재사용 가능한 A2A 거버넌스 기반**(§3): 출력 정책과 입력 셰이퍼를 공유 상태 위에서 깔끔하게 분리한다.
2. **통제된 실험 내 설계**(§4): 모든 레버를 단일 공통 baseline에서, 앵커링/길이 대조 프롬프트·bootstrap CI·순열검정·Holm 보정과 함께 측정한다.
3. **부정적·방법론적 결과**(§5–6): 9개 보정 대조 중 2개만 살아남고, "입력이 출력을 이긴다"는 헤드라인은 통과하지 못한다. 분리-baseline N=24 검정을 통과했던 평판 되먹임 효과는 사회적 기제가 아니라 앵커링이고, 내용 없는 배너가 welfare에서 "승리"하며, "사회" 출력 정책은 더미 캡과 같고 welfare를 *해친다*. 우리는 설계 선택이 어떻게 두 개의 가짜 양성을 만들어냈는지 문서화한다.

---

## 2. 관련 연구

이기적 착취는 노골적 페르소나부터 창발적 배신·획책(scheming)·은밀한 담합까지 걸쳐 있다 [Vallinder & Hughes 2025; Secret Collusion, NeurIPS 2024]. GovSim [Piatti et al. 2024]은 대부분의 LLM이 지속가능한 공유지 사용에 실패함을, 그리고 *프롬프트로 주입한 보편화(universalization)*가 지속가능성을 높임을 보인다 — 이는 입력-프레이밍 개입이다. 사회적 기제 제안들은 평판·가십 [Milinski et al. 2002; ALIGN 2026], 비용을 수반한 처벌·배제 [Fehr & Gächter 2000], 상위 정체성(Robbers Cave)을 에이전트로 이식한다. 그 형식적 출력측 대응물이 메커니즘 디자인 / Institutional AI 제재와 Shoham–Tennenholtz 사회적 법칙이다. **우리의 출력/입력 이분법 자체는 새롭지 않다** — 그것은 메커니즘 디자인 대 인-컨텍스트 조정(in-context steering)을 다시 말한 것이다. 새로운 것은 *앵커링 대조군과 다중보정을 갖춘 통제된 정면 비교*, 그리고 대부분의 효과가 이를 통과하지 못한다는 발견이다. 가장 가까운 선행 입력-프레이밍 연구(GovSim 보편화, ALIGN 가십-프롬프팅)는 앵커 대조 없이 양성 효과를 보고하는데, 우리 결과는 그런 효과에 앵커링 귀무가설을 세워야 함을 시사한다.

---

## 3. 거버넌스 기반(Substrate)

모든 행동은 전달 전에 하나의 `InterceptPoint.submit(action)→verdict ∈ {ALLOW,DENY,MODIFY,DELAY}`를 통과한다. 우선순위로 정렬된 `PolicyChain`은 DENY/DELAY에서 단락(short-circuit)하고, MODIFY를 다음 정책으로 전파하며, 플래그/이벤트를 비차단 방식으로 누적한다. 모든 가변 상태(commons 예산, 시도/전달 집계, 턴 로그, 파생 평판)는 단일 `SharedState`에 살며 오케스트레이터만 이를 변경한다. 정책과 셰이퍼는 이를 **읽기 전용**으로 읽는다(검증됨). 두 레버는 동일한 상태 위에서 동작한다: **출력 정책**(`FractionCapPolicy` 더미 캡 `k·remaining`; 평판+배제 "사회" 정책)은 전달되는 행동을 가로채고, **입력 셰이퍼**(`superordinate_identity`, `reputation_feedback`, 그리고 대조군 `fairshare_anchor`, `neutral_filler`)는 호출 직전에 프롬프트를 재작성한다.

---

## 4. 실험 설계 (통제된 검정)

**시나리오.** N개 에이전트가 공유 풀(commons)에서 `REQUEST`를 뽑아 하위 과업을 끝낸다. 탐욕 = 풀을 선점해 남을 굶기는 것. 실제 모델 위의 자기-이익 페르소나가 탐욕을 *창발*시킨다(스크립트된 hog 없음). OpenRouter를 통한 GLM-4.6, 온도 0.7. 에이전트 3개, 풀=360, 작업량=120, 8라운드.

**이전 초고가 틀렸던 점(그리고 이 설계가 고치는 점).** 우리의 초기 실험은 각 레버를 *각자 따로 뽑은* baseline에 대해 측정했다. 동료심사는 그 baseline들이 효과 크기만큼 표류(drift)해 가짜 양성을 만들어낸다는 것을 보였다. 통제된 설계(V6)는 다음과 같다:
- **단일 공통 baseline, 단일 런:** 7개 arm 전부 — `none`, `dumb_cap`, `social`, `reputation_feedback`, `superordinate`, 그리고 두 대조군 — 을 N=30에서 함께 측정한다.
- **앵커링/길이 대조군**으로 입력-셰이퍼 효과를 분해한다: `fairshare_anchor`(reputation_feedback의 *숫자* 공정-몫 문장만 남기고 평판·또래·규범 표현을 **전부** 제거)와 `neutral_filler`(같은 길이의 내용 없는 배너). reputation_feedback − fairshare_anchor 차이는 *사회적/규범적* 성분을, fairshare_anchor − neutral_filler 차이는 *앵커* 성분을, neutral_filler − none 차이는 *프롬프트 길이/지시성* 성분을 분리한다.
- **원자료 위의 정직한 통계:** 백분위 bootstrap 95% CI, 두-표본 **순열검정**(4-값 완료 변수에 정규근사 미사용), 사전 지정한 9개 대조에 대한 **Holm 보정**.

**지표.** top-share(단일 에이전트 최대 부여 점유율 = 독점), welfare(완료율), 시도 대 전달 Jain. "N 반복(replications)" = N개의 독립적 온도-0.7 추출(고정 LLM 시드 없음; 정확한 재현은 비트 단위가 아니라 분포적이다).

---

## 5. 결과

### 5.1 통제 표 (V6, N=30, 공통 baseline)

| arm | welfare (bootstrap 95% CI) | top-share (bootstrap 95% CI) |
|---|---|---|
| none (무규제) | 0.66 [0.56, 0.76] | 0.651 [0.551, 0.751] |
| dumb_cap (k=0.22, 더미 캡) | 0.48 [0.39, 0.57] | 0.467 [0.435, 0.501] |
| social (평판+배제) | 0.39 [0.28, 0.50] | 0.434 [0.412, 0.458] |
| reputation_feedback (평판 되먹임) | 0.69 [0.60, 0.78] | 0.588 [0.495, 0.687] |
| superordinate (상위 정체성) | 0.69 [0.64, 0.73] | 0.412 [0.387, 0.438] |
| fairshare_anchor (대조군) | 0.71 [0.60, 0.82] | 0.605 [0.494, 0.717] |
| neutral_filler (대조군) | 0.82 [0.72, 0.92] | 0.500 [0.405, 0.605] |

### 5.2 Holm 보정을 통과한 것 (단 2개)

| 대조 | p | p_holm | 판정 |
|---|---|---|---|
| top: superordinate vs none | .0001 | **.0009** | ✅ 상위 정체성이 독점을 줄임 |
| welfare: social vs none | .0028 | **.022** | ✅ 출력 "사회" 정책이 welfare를 **해침** |
| welfare: neutral_filler vs none | .042 | .29 | ns (길이 효과는 보정에서 사라짐) |
| top: social vs dumb_cap (F4) | .127 | .76 | ns → **사회 ≈ 더미 캡 (공정성)** |
| welfare: fairshare_anchor vs neutral_filler | .196 | .98 | ns (앵커 효과 없음) |
| top: reputation_feedback vs none | .360 | 1.0 | **ns → 독점 효과 없음** |
| welfare: superordinate vs none | .427 | 1.0 | ns (welfare 중립) |
| welfare: reputation_feedback vs none | .611 | 1.0 | **ns → welfare 효과 없음** |
| welfare: reputation_feedback vs fairshare_anchor | .881 | 1.0 | **ns → "사회적" 표현은 아무 것도 더하지 않음** |

### 5.3 평판 되먹임 헤드라인은 아티팩트였다 (F1+F2)

분리-baseline 검정(V1, N=24)에서 reputation_feedback은 welfare 0.61→0.79 (p=.027), top-share 0.715→0.522 (p=.019)를 보였다. 공통 baseline(V6)에서 *같은* 프롬프트는 welfare 0.69 대 none 0.66 (**p=.61**), top-share 0.588 대 0.651 (**p=.36**) — 둘 다 귀무다. 앞서의 "효과"는 V1 baseline이 낮게 뽑힌 결과(0.61 대 V6의 0.66)였고, 이것이 바로 동료심사가 지적한 실험 간 표류다. 게다가 reputation_feedback ≈ fairshare_anchor (welfare p=.88): 평판·또래·규범 언어를 벗겨내고 숫자 공정-몫 문장만 남겨도 아무것도 달라지지 않는다 — 즉 효과가 있다면 그것은 **간접 호혜 기제가 아니라 지시-앵커링**이다.

### 5.4 내용 없는 배너가 welfare에서 "이긴다"

`neutral_filler` — 자원·공정성·평판 내용이 전혀 없는 배너 — 가 **가장 높은** 점추정 welfare(0.82)를 가지며, 설계된 모든 셰이퍼를 능가한다. `none` 대비 우위는 Holm 보정을 통과하지 못하므로(p=.042→.29) 우리는 필러가 *도움이 된다*고 주장하지 않는다. 요점은 그 반대다: **입력 배너의 welfare 차이는 사회적 기제 설계에 귀속될 수 없다.** 내용 없는 배너가 설계된 것들과 같거나 더 낫기 때문이다. 이것이 "입력 프레이밍은 사회적이기 때문에 효과가 있다"는 서사에 대한 가장 깨끗한 반증이다.

### 5.5 진짜인 것

통제·보정 검정을 통과한 효과는 둘이다:
1. **상위 정체성이 독점을 줄인다** (top-share 0.65→0.41, p_holm<.001) — 다만 welfare 효과는 귀무다(p=.43). 이것은 견고한 행동 신호를 가진 유일한 입력 레버다 — 그러나 우리는 reputation_feedback을 강등시킨 것과 *같은* 회의를 여기에도 적용한다: superordinate는 **자기 자신의 앵커링 대조군이 없으므로**(§7), 이 감소의 일부는 정체성 자체가 아니라 일반적 지시-따르기일 수 있다. 우리는 이를 정체성 프레이밍이 효과가 있다는 증명이 아니라, **견고하지만 미분해된(undecomposed)** 효과로 보고한다.
2. **출력 "사회" 정책이 welfare를 줄인다** — 무규제 대비(0.66→0.39, p_holm=.022), 그리고 공정성 측면에서 더미 비례 캡과 구분되지 않는다(p=.13). 이 시나리오에서 "사회" 기계장치는, welfare까지 갉아먹는 재명명된 요청 제한기(rate-limiter)다.

---

## 6. 논의

**헤드라인은 살아남지 못했다 — 그것이 발견이다.** 이전의 두 "입력 승리" 기둥 중, 평판 되먹임은 앵커링 아티팩트로 무너졌고 superordinate의 welfare 이득은 귀무이며, 오직 그것의 독점 감소만 진짜다. 따라서 우리는 입력 프레이밍이 출력 캡을 이긴다고 주장할 수 없다. 우리가 주장할 수 있는 것은 더 날카롭고 분야에 더 유용하다: **보고된 탐욕-거버넌스 효과 대부분은 실험 설계에 취약하다.** 표준 관행인 분리-baseline 다중-시드 검정은 우리 손에서 두 개의 가짜 양성(V1 평판, 이전의 "사회 welfare 0.75")을 만들어냈고, 둘 다 공통 baseline과 앵커링 대조군으로 사라졌다.

**방법론적 처방.** (1) 모든 거버넌스 arm을 *하나의* baseline에 대해 단일 런으로 측정하라. arm별 baseline은 N≤30에서 효과 크기만큼 표류한다. (2) 어떤 프롬프트-프레이밍 개입이든 **앵커링 대조군**(규범·사회 표현을 벗긴 순수 정보 내용)과 **길이 대조군**을 포함하라. 그것들 없이는 "사회적 기제" 주장이 지시-따르기와 식별 불가능하다. (3) 이산 소표본 변수에 정규근사가 아니라 원자료 위의 순열/bootstrap을 쓰고, 다중성을 보정하라. 우리의 "p<.05" 효과 셋 중 셋이 Holm 이후 증발한다.

**문헌과의 관계.** 우리의 출력 "사회" 정책 = 더미 캡 결과는 회의론자의 "재명명된 요청 제한기"와 일치한다. 그러나 우리의 앵커-대조 결과는 *새로운* 경고를 던진다: GovSim/ALIGN 계열의 입력-프레이밍 결과(보편화 프롬프팅, 가십 프롬프팅)는, 내재화된 사회적 기제의 증거로 읽히기 전에 앵커링 귀무가설에 대해 재검정되어야 한다 — 그것이 인-컨텍스트 지시-따르기가 아니라는 보장이 없기 때문이다.

---

## 7. 한계

- **단일 모델, 단일 시나리오, 단일 작동점.** GLM-4.6; resource-task, 에이전트 3, 풀=360, r=8, N=30. "캡이 welfare를 해친다"는 발견은 config 의존적이다: 무규제 탐욕이 전원을 굶기지 않는 곳(none welfare 0.66)에서는 캡이 주로 완주 가능한 에이전트를 throttle한다. 파국적 영역에서는 캡이 welfare를 *구할* 수도 있다. 풀/에이전트 스윕이 핵심 다음 단계다.
- **귀무 ≠ 부재.** N=30은 작은 효과를 탐지하지 못한다. reputation_feedback/superordinate-welfare는 "유의하지 않음"이지 "0"이 아니다. 다만 앵커링 귀무(rep ≈ anchor, p=.88)는 *사회적* 해석에 대해서는 양의 반대 증거다.
- **시드 없는 백엔드.** 고정되지 않은 OpenRouter-라우팅 모델 위 온도-0.7 추출. 임계 근처 결과는 런마다 흔들린다(이것이 바로 §5.3의 요점이다).
- **superordinate도 앵커링일 수 있다.** reputation_feedback에는 앵커 대조군을 추가했지만 superordinate에는 추가하지 않았다. 그 독점 효과는 견고하지만 아직 정체성 대 지시로 분해되지 않았다.

---

## 8. 결론 및 향후 과제

LLM-에이전트 탐욕 거버넌스에 대한 통제·앵커대조·다중보정 실험은 **대부분의 후보 효과가 측정 아티팩트**임을 발견한다: 9개 대조 중 상위-정체성의 독점 감소와 출력 "사회" 정책의 welfare *비용*만 살아남고, 평판 되먹임의 "승리"는 실험 간 baseline 표류에 숫자 앵커링이 더해진 것이며, 내용 없는 배너가 welfare 정상에 선다. 재사용 가능한 기반, 앵커링-대조 방법론, 그리고 문서화된 자기 수정(결정적 단일 런이 두 개의 다중-시드 헤드라인을 뒤집음)이 기여다. 향후 과제: (1) 상위 정체성에 앵커 대조군 추가; (2) 출력 캡이 welfare를 돕는/해치는 지점을 지도화하는 풀/에이전트 스윕; (3) 살아남은 효과에 대한 멀티모델 재현과 N≥100; (4) 간접 호혜 기제(여기엔 없음)가 실제로 작동할 수 있는 장기-시계열·반복 상호작용 시나리오.

---

## 부록 A — 동료심사 응답 (Major Revision)

| 이슈 | 심사자 | 해결 |
|---|---|---|
| F1 입력/출력 동일 실험 내 미배치; baseline 표류 | DA-A1, R1 | **V6가 모든 arm을 단일 공통 baseline에 대해 실행(N=30).** 아티팩트 확인: 평판 되먹임의 V1 효과가 사라짐. |
| F2 reputation_feedback에 앵커링 대조군 없음 | DA-A2, R2 | **`fairshare_anchor` + `neutral_filler` 추가.** rep ≈ anchor (p=.88) → 효과는 사회가 아니라 앵커링. 헤드라인 제거. |
| F3 무효한 정규근사 z; 다중성 미보정 | R1 | **bootstrap CI + 순열검정 + Holm.** 이전 "p<.05" 효과 셋이 통과하지 못함. |
| F4 "사회 = 캡" 과잉일반화 | R2 | "우리의 평판+배제 정책, 이 config"로 범위 한정; V6가 사회 ≈ 더미 캡 확인(p=.13). 7-에이전트 반례는 config 의존으로 인정. |
| F5 "multi-seed" 명칭 오류; 출처(provenance) | R3 | "replications"로 개명; V6 JSON이 config + 원시 반복별 배열 저장. 제공자-고정 + 비용 로깅은 잔여로 명시. |
| 신규성 과장 | R2 | §2 재구성: 이분법은 메커니즘 디자인 대 인-컨텍스트 조정; 기여는 통제된 검정 + 앵커링 귀무. |
| 제목 과장 | R2, DA-A3 | 제목을 "입력 프레이밍이 출력 캡을 이긴다"에서 부정적·방법론 결과로 변경. |

## 참고문헌 (선별; 전체 링크는 `docs/research_2.md`)
- Hammond et al. *Multi-Agent Risks from Advanced AI*, 2025. arXiv:2502.14143
- Piatti et al. *Cooperate or Collapse (GovSim)*, NeurIPS 2024. arXiv:2404.16698
- Vallinder & Hughes. *The Subtle Art of Defection*, 2025. arXiv:2511.15862
- Milinski et al. *Reputation helps solve the tragedy of the commons*, Nature 2002.
- Fehr & Gächter. *Cooperation and punishment in public goods experiments*, 2000.
- *Talk, Judge, Cooperate (ALIGN)*, 2026. arXiv:2602.07777
- Korbak et al. *Chain of Thought Monitorability*, 2025. arXiv:2507.11473

*(아티팩트: `docs/verify_v6.json`(원자료), `docs/verify_results.md`, `docs/peer_review.md`, `docs/re_review.md`, `scripts/verify_claims.py`.)*
