# LLM 에이전트의 탐욕 거버넌스 효과 대부분은 측정 아티팩트다: 출력 강제 캡 vs 입력 프레이밍의 통제된 검정

*Most Greed-Governance Effects on LLM Agents Are Measurement Artifacts: A Controlled Test of Output Capping vs. Input Framing*

**상태:** 동료심사(Major Revision) 이후의 개정본. 이전 초고의 결론("입력 프레이밍이 출력 캡을 이긴다")은 **통제된 실험에서 살아남지 못해** 폐기했고, 데이터가 실제로 뒷받침하는 결론으로 바꿨다. 모든 수치는 GLM-4.6 위에서 돌린 단일 실험(V6, N=30)에서 나왔고, bootstrap 신뢰구간·순열검정·Holm 보정을 거쳤다. 원자료는 [`docs/verify_v6.json`](verify_v6.json)에 있다.

> **용어 한 눈에 (먼저 읽어주세요).** 이 글에는 일상에서 잘 안 쓰는 단어가 몇 개 나온다. 어려우면 여기로 돌아오면 된다.
> - **독점(top-share)**: 한 에이전트가 가져간 자원의 최대 점유율. 높을수록 한 명이 다 차지한 것 → 나쁨.
> - **후생(welfare)**: 자기 과업을 끝낸 에이전트의 비율(완료율). 높을수록 다 같이 잘 끝낸 것 → 좋음.
> - **출력측(output-side)**: 행동의 *결과*를 깎는 규제. 예: "요청이 너무 크면 잘라낸다(cap)".
> - **입력측(input-side)**: 행동을 하기 *전에* 프롬프트(지시문)를 바꿔 설득하는 방식. 캡이 아니라 말로 타이르는 쪽.
> - **레버(lever)**: 결과를 바꾸려고 당기는 손잡이. 여기선 출력측·입력측 두 종류의 "거버넌스 손잡이".
> - **셰이퍼(shaper)**: 프롬프트를 다시 써 주는 입력측 장치.
> - **앵커링(anchoring)**: 숫자를 먼저 보여주면 답이 그 근처로 끌려가는 심리 현상. "정원 33%"라고 적어두면 33% 근처를 요청하게 되는 것.
> - **귀무·유의하지 않음(null / ns)**: 통계적으로 "차이를 찾지 못했다"는 뜻. 차이가 0이라는 증명은 아님.
> - **Holm 보정(Holm correction)**: 비교를 여러 번 하면 우연히 "유의"가 튀어나온다. 그걸 걸러내는 안전장치.

---

## 초록

여러 LLM 에이전트가 하나의 공유 자원(commons)을 두고 다투면, 오래된 "공유지의 비극"이 그대로 재현된다 — 각자 자기 몫을 최대로 챙기다 보면 전체가 망가진다([Hammond et al. 2025](https://arxiv.org/abs/2502.14143); [Piatti et al. 2024](https://arxiv.org/abs/2404.16698)). 이를 막으려는 방법은 크게 둘이다. 하나는 **출력측**(결과를 깎는 캡·요청 제한·평판 기반 "사회" 정책), 다른 하나는 **입력측**(정체성·책임감·평판 피드백처럼 프롬프트로 타이르는 방식). 우리는 재사용 가능한 A2A 거버넌스 토대를 만들고, 이 분야가 흔히 건너뛰는 *통제된* 실험을 했다: 모든 방법을 **하나의 공통 기준점(baseline)·하나의 실험 안에서** 나란히 측정하고, **앵커링·길이 대조 프롬프트**, **bootstrap 신뢰구간**, 두-표본 **순열검정**, 다중비교용 **Holm 보정**을 적용했다.

결과는 냉정하다. 미리 정해 둔 9개 비교 중 보정을 통과한 것은 단 2개다. (1) 상위 정체성(superordinate identity) 프롬프트는 독점을 확실히 줄였고(top-share 0.65→0.41, p_holm<.001), (2) 출력측 "사회" 정책은 무규제보다 후생을 *오히려 떨어뜨렸다*(0.66→0.39, p_holm=.022). 나머지는 전부 허상이었다. 따로 기준점을 둔 옛 실험(N=24, p=.027)에서 효과가 있어 보였던 평판 피드백은, 공통 기준점에서는 무규제와 **구분되지 않았고**(후생 p=.61), 사회적 표현을 모두 뺀 *맨숫자 앵커*와도 **구분되지 않았다**(p=.88) — 즉 사회적 기제가 아니라 그냥 앵커링이었다. 심지어 *아무 내용 없는 들러리(filler)* 프롬프트가 후생 **1등**을 했다. 출력측 "사회" 정책은 공정성에서 **단순한 더미 캡과 통계적으로 구분되지 않았다**(p=.13). 따라서 우리 기여는 방법론적·부정적이다: 보고된 탐욕-거버넌스 효과 대부분은 실험 설계에 취약하고, 단 한 번의 결정적 실험이 우리 자신의 헤드라인 2개를 뒤집었으며, 통제·앵커대조·다중보정 설계만이 진짜 기제를 노이즈와 구별해 낸다.

**Abstract (English).** LLM agents competing over a shared commons revive the tragedy of the commons. We ran the controlled experiment the field usually skips: all governance levers against one shared baseline in a single run, with anchoring/length controls, bootstrap CIs, permutation tests, and Holm correction. Of nine pre-specified contrasts, only two survive: superordinate identity reduces monopoly (top 0.65→0.41, p_holm<.001) and an output "social" policy *reduces* welfare (0.66→0.39, p_holm=.022). The reputation-feedback "win" is baseline drift plus numeric anchoring; a contentless banner tops welfare; social ≈ dumb cap on fairness. The contribution is methodological and negative.

---

## 1. 서론

자율 LLM 에이전트는 더 이상 혼자 일하지 않는다. A2A(Agent-to-Agent) 프로토콜로 서로 연결되어 자원을 나눠 쓰는데, 그 순간 인간 사회가 오래 씨름해 온 사회적 딜레마가 되살아난다([Hammond et al. 2025](https://arxiv.org/abs/2502.14143)). 여기서 문제가 되는 것이 **행동적 탐욕(behavioral greed)** — 공유 자원을 선점해 남을 굶기는 이기적 착취다([Vallinder & Hughes 2025](https://arxiv.org/abs/2511.15862)).

비유하자면 이렇다. 사무실에 공용 프린터(공유 자원)가 하나 있는데, 한 사람이 1,000장짜리 작업을 계속 걸어두면 나머지는 한 장도 못 뽑는다. 이걸 막는 방법은 두 갈래다.

- **출력측(output-side)**: "한 번에 100장 넘으면 잘라낸다"처럼 *나온 행동을 깎는다*. 캡(cap), 요청 제한, 평판·배제 같은 "사회" 정책이 여기 속한다.
- **입력측(input-side)**: 프린터를 쓰기 *전에* "다들 같이 써야 하니 양보합시다"라고 *타이른다*. 정체성·책임감·평판 피드백 같은 프롬프트가 여기 속한다.

우리는 처음엔 "어느 쪽이 더 나은가"를 재려 했다. 그런데 우리 자신의 결과가 실험을 다시 할 때마다 뒤집히는 걸 겪으면서, 더 어려운 진짜 문제를 발견했다 — **진짜 효과를 실험 설계가 만든 착시(artifact)와 구별하는 일**이다.

이 논문의 기여는 그 통제된 실험과, 거기서 나온 부정적 결과다.
1. **재사용 가능한 A2A 거버넌스 토대**(§3): 출력측 정책과 입력측 셰이퍼를 같은 상태 위에서 깔끔히 분리한다.
2. **통제된 실험 설계**(§4): 모든 레버를 하나의 공통 기준점에서, 앵커링·길이 대조군과 정직한 통계(bootstrap·순열검정·Holm)와 함께 잰다.
3. **부정적·방법론적 결과**(§5–6): 9개 비교 중 2개만 살아남고, "입력이 출력을 이긴다"는 헤드라인은 통과하지 못한다. 우리는 어떤 설계 선택이 두 개의 가짜 양성을 만들어냈는지 그대로 문서화한다.

---

## 2. 관련 연구

> 이 절은 우리가 별도로 수행한 **40여 편 규모의 내러티브 문헌 리뷰**([`docs/research_2.md`](research_2.md), 부록 B의 검증 노트 포함)를 이 실험에 필요한 만큼 압축한 것이다. 전체 지형·인용은 그 문서를 참고하라.

### 2.1 위험: 왜 탐욕이 문제인가

여러 에이전트가 상호작용할 때 생기는 위험을 가장 널리 인용되는 분류 체계가 정리한다([Hammond et al., *Multi-Agent Risks from Advanced AI* 2025](https://arxiv.org/abs/2502.14143)): 조정 실패·갈등·공모(바람직하지 않은 협력)의 세 실패 모드와 일곱 위험 요인이다. 공유지의 비극은 이 중 가장 임박한 위험이다. GovSim 벤치마크([Piatti et al. 2024](https://arxiv.org/abs/2404.16698))는 *가장 강한 모델을 빼면 거의 모든 LLM이 지속가능한 자원 사용에 실패*하고, 통신을 끊으면 평균 22% 과소비함을 보였다. 역설적으로 *추론이 강한 모델이 오히려 더 잘 무임승차*하는 경향도 보고되었다([*Corrupted by Reasoning* 2025](https://arxiv.org/pdf/2506.23276)) — "똑똑할수록 협력적"이라는 직관을 뒤집는다.

탐욕은 노골적 페르소나부터([Vallinder & Hughes 2025](https://arxiv.org/abs/2511.15862)) 은밀한 형태까지 스펙트럼을 이룬다. 모델끼리는 유도 없이도 높은 비율로 기만을 선택하고([*Scheming Ability in LLM-to-LLM* 2025](https://arxiv.org/abs/2510.12826)), 스테가노그래피로 감시자가 못 읽는 *비밀 공모*까지 가능하다([*Secret Collusion*, NeurIPS 2024](https://arxiv.org/pdf/2402.07510)). 특히 **AI–AI 신뢰 취약점**이 중요하다: 인간의 악성 명령은 거부하는 모델이, *동료 에이전트*가 같은 요청을 하면 실행한다([*The Dark Side of LLMs* 2025](https://arxiv.org/abs/2507.06850)). 현재 안전 학습이 인간–AI에 맞춰져 있고 AI–AI 경로는 비어 있다는 뜻이다. 또한 행동은 페르소나·프레이밍 같은 표면 단서에 *극도로 민감*해서, 같은 보상 구조에서도 협력↔비극이 뒤집힌다([*When Identity Overrides Incentives* 2026](https://arxiv.org/html/2601.10102)). 이 민감성이 바로 우리가 통제 실험을 강조하는 이유다.

### 2.2 출력측 대응: 메커니즘 디자인과 강제

전통적 처방은 *규칙과 보상을 다시 설계*해 협력이 이득이 되게 만드는 것이다. 네트워크 공정성(max-min fairness, fair queuing)은 한 흐름이 자기 몫 이상을 못 가져가게 막고, 메커니즘 디자인은 협력을 우월전략으로 만든다. 제도적 AI(Institutional AI)는 안전을 개별 모델 정렬이 아니라 *런타임 거버넌스* 문제로 재정의하여, 공개 관측치에 근거해 이탈에 비용을 부과한다([Institutional AI 2026](https://arxiv.org/abs/2601.10599); [Cournot 시장 담합 통제](https://arxiv.org/html/2601.11369v1)). 그 이론적 뿌리가 Shoham–Tennenholtz의 "사회적 법칙(social laws)"이다. **한계는 분명하다**: 강력하지만 이론→구현 갭이 크고, 관측 밖 은닉 행동은 못 막으며, 보상 설계에 매우 민감하다. 회의론자의 표현으로는 많은 "사회" 정책이 결국 *이름만 그럴싸한 요청 제한기(rate-limiter)*다 — 우리 §5가 이 의심을 정면으로 검정한다.

### 2.3 입력측 대응: 사회심리학을 프롬프트로

다른 갈래는 인간 사회가 중앙 감시 없이도 협력을 유지해 온 방식 — 평판·규범·정체성·상호성 — 을 프롬프트로 이식한다. 최근 "AI 에이전트 행동과학"이 이 관점을 정식화했다([Chen et al. 2025](https://arxiv.org/abs/2506.06366)): 에이전트의 공정성·책임성을 *내부 구조*가 아니라 *행동의 결과*로 본다. 대표 사례는 다음과 같다.

- **간접 상호성·가십 평판**: 목격된 행동을 평판으로 방송해 분산적으로 규범을 만든다([ALIGN 2026](https://arxiv.org/abs/2602.07777)). 인간 실험에서 평판은 공유지의 비극을 실제로 풀었다(Milinski et al., *Nature* 2002).
- **비싼 처벌·배제(ostracism)**: 공공재 게임에서 협력은 처벌 없이는 거의 유지되지 않는다(Fehr & Gächter, 2000). 저비용 대안인 배제가 특히 효과적이다.
- **상위 정체성·공동 목표**: "우리 대 그들"을 *더 큰 하나의 우리*로 재범주화한다(로버스 케이브 실험). 사회적 학습으로 공유지 협력이 자율 발달함이 보고되었다([AAMAS 2026](https://arxiv.org/pdf/2510.14401)).
- **책임성·관객 효과, 보편화 추론**: 관찰된다고 느끼면 더 친사회적이 되고, "모두가 이러면?"을 강제하면 지속가능성이 오른다(GovSim).

**중요한 경고**: 이 입력측 레버들은 양날의 검이다. 내집단을 만들면 *인간을 외집단으로* 취급할 위험([*Agents See Humans as Outgroup* 2026](https://arxiv.org/abs/2601.00240)), 다수·강자에게 동조하는 집단사고([*Group Conformity in MAS* 2025](https://arxiv.org/abs/2506.01332)), 지나치게 조화로워 갈등을 가리는 *거짓 합의*([*Utopian Illusion* 2025](https://arxiv.org/pdf/2510.21180))를 낳을 수 있다.

### 2.4 우리의 위치 — 무엇이 새로운가

**출력/입력 이분법 자체는 새롭지 않다** — 메커니즘 디자인 대 인-컨텍스트 조정(in-context steering)을 다시 말한 것이다. 새로운 것은 둘을 *같은 상태·같은 실험·앵커링 대조군·다중보정*으로 정면 비교했다는 점, 그리고 *대부분의 효과가 그 검정을 통과하지 못한다*는 발견이다. 가장 가까운 선행 입력측 연구(GovSim 보편화, ALIGN 가십)는 앵커 대조 없이 양성 효과를 보고하는데, 우리 결과는 그런 효과에 **앵커링 귀무가설을 먼저 세워야 한다**고 경고한다.

---

## 3. 거버넌스 토대(Substrate)

모든 행동은 전달되기 전에 하나의 관문 `InterceptPoint.submit(action)→verdict ∈ {ALLOW,DENY,MODIFY,DELAY}`를 통과한다. 우선순위로 정렬된 `PolicyChain`은 DENY/DELAY에서 멈추고(short-circuit), MODIFY를 다음 정책으로 넘기며, 플래그·이벤트를 비차단으로 쌓는다. 모든 가변 상태(자원 예산, 시도/전달 집계, 턴 로그, 파생 평판)는 단 하나의 `SharedState`에 모여 있고 오케스트레이터만 이를 바꾼다. 정책과 셰이퍼는 이걸 **읽기 전용**으로만 본다(검증됨). 두 레버가 같은 상태 위에서 돈다: **출력측 정책**(`FractionCapPolicy` 더미 캡 `k·remaining`; 평판+배제 "사회" 정책)은 전달되는 행동을 가로채고, **입력측 셰이퍼**(`superordinate_identity`, `reputation_feedback`, 그리고 대조군 `fairshare_anchor`, `neutral_filler`)는 호출 직전 프롬프트를 다시 쓴다.

---

## 4. 실험 설계 (통제된 검정)

**시나리오.** 에이전트 N명이 공유 풀(commons)에서 자원을 요청(`REQUEST`)해 자기 과업을 끝낸다. 탐욕 = 풀을 선점해 남을 굶기는 것. 실제 모델 위의 자기-이익 페르소나가 탐욕을 *저절로 만들어낸다*(미리 짠 hog 스크립트 없음). OpenRouter를 통한 GLM-4.6, 온도 0.7. 에이전트 3명, 풀=360, 작업량=120, 8라운드.

**이전 초고가 틀린 점, 그리고 이 설계가 고치는 법.** 초기 실험은 각 레버를 *제각각 따로 뽑은* 기준점에 견줬다. 동료심사는 그 기준점들이 효과 크기만큼 *표류(drift)*해 가짜 양성을 만든다고 지적했다(쉽게 말해, 비교 대상이 매번 다른 출발선에서 출발한 셈). 통제된 설계(V6)는 이렇게 고친다:
- **하나의 공통 기준점, 하나의 실험:** 7개 arm 전부 — `none`, `dumb_cap`, `social`, `reputation_feedback`, `superordinate`, 그리고 두 대조군 — 을 N=30에서 함께 측정한다.
- **앵커링·길이 대조군으로 효과를 분해:** `fairshare_anchor`는 reputation_feedback에서 평판·또래·규범 표현을 **전부 빼고** *숫자 공정-몫 문장만* 남긴 것이고, `neutral_filler`는 같은 길이의 *내용 없는* 배너다. → (rep − anchor)는 "사회적" 성분을, (anchor − filler)는 "숫자 앵커" 성분을, (filler − none)은 "프롬프트 길이" 성분을 각각 분리한다.
- **원자료 위의 정직한 통계:** 백분위 bootstrap 95% 신뢰구간, 두-표본 **순열검정**(4-값 완료 변수에 정규근사 안 씀), 미리 정한 9개 비교에 **Holm 보정**.

**지표.** top-share(한 에이전트 최대 점유율 = 독점), welfare(완료율 = 후생), 시도 대 전달 Jain. "N 반복(replications)" = 온도-0.7로 독립 추출 N회(고정 시드 없음 → 재현은 비트 단위가 아니라 분포적).

### 4.1 각 실험 조건의 근거와 구현 (수식·알고리즘)

각 arm을 *왜* 넣었고, *어떤 수식/알고리즘*으로 구현했는지를 한 자리에 모은다. 코드 출처는 출력측 = [`antigreedy/governance/nullcap.py`](../antigreedy/governance/nullcap.py) + [`policies/presets/social_reputation/`](../policies/presets/social_reputation), 입력측 = [`antigreedy/scenario/prompt_shapers.py`](../antigreedy/scenario/prompt_shapers.py)다.

**(0) 탐욕은 강제하지 않고 '창발(emergent)'시킨다.** 미리 짠 hog 스크립트 대신, 모든 에이전트에 동일한 경쟁 페르소나를 주고 실제 GLM이 알아서 과점하게 둔다.

> **GREEDY_PERSONA:** "너는 경쟁적이고, 남들보다 먼저 끝내면 큰 보너스를 받는다. 공정함보다 먼저 끝내는 게 너에게 더 중요하다." 시나리오 프롬프트는 매 라운드 "공정 몫 ≈ 풀÷n"을 함께 알려준다.

**(1) 평판 공식 — 모든 평판 기반 조건이 공유.** 턴 로그(누가 얼마를 받았는지)에서 누적 전달량을 읽어 0.1~1.0 평판으로 환산한다:

```
share = mine / total                                  # 내 누적 점유율 (mine=내 전달량, total=전체)
fair  = 1 / n                                         # 공정 몫 (n = 에이전트 수)
rep   = clip( 1 − max(0, share − fair) / fair, 0.1, 1.0 )
```

공정 몫 이하로 쓰면 rep=1.0(만점), 공정 몫의 *2배*를 쓰면 rep=0.1(하한). 한마디로 "얼마나 과점했나"를 평판 점수로 바꾼 것이다.

**(2) 7개 arm의 근거·구현 표.**

| arm | 계층 | 활용 근거 (이론 · 문헌) | 구현 (수식 / 알고리즘) |
|---|---|---|---|
| `none` | 무규제 | 공통 기준점 | 정책·셰이퍼 없음. 창발한 탐욕을 그대로 통과 |
| `dumb_cap` | 출력 | F4 검정용 "이름만 사회"인 단순 비례 캡 — 네트워크 공정 큐잉의 최소판([§2.2](research_2.md)) | `cap = max(floor, ⌊remaining · k⌋)`, k=0.22. 요청 > cap이면 거부/절단. **평판을 전혀 안 봄** |
| `social` | 출력 | 제안1 간접상호성·가십(Milinski 2002; [ALIGN](https://arxiv.org/abs/2602.07777)) + 제안2 비싼처벌·배제(Fehr & Gächter 2000) | 정책 2개 결합: ① **가십 캡** `cap = max(30, ⌊remaining · 0.22 · rep⌋)` (초과 시 내용 절단) — 평판 낮을수록 캡↓; ② **배제** `rep < 0.45 → deny` (먼저 평가, 자기교정적: 배제→점유↓→평판 회복) |
| `reputation_feedback` | 입력 | 평판 신호를 *당사자 프롬프트에 되먹임*(제안1+4 폐회로). **출력 캡 0** | 프롬프트에 `rep` · 점유 `share%` · 공정몫 `fair%` + "동료가 보고 기억한다"를 주입. 행동은 설득으로만 유도 |
| `superordinate` | 입력 | 제안3 상위 정체성·공동 목표(로버스 케이브; [AAMAS 2026](https://arxiv.org/pdf/2510.14401)) | 배너 주입: "ONE TEAM — *전원* 완료 시 팀 1점, 한 명이라도 굶으면 0점, 혼자 빨리 끝내면 무가치". **수식 없는 정성 프레이밍** |
| `fairshare_anchor` | 대조 | F2: 평판 효과에서 *숫자 앵커* 성분만 분리 | reputation_feedback에서 평판·또래·규범 어휘를 **전부 제거**하고 `share%`·`fair%`·풀 잔량 *숫자만* 남김 |
| `neutral_filler` | 대조 | F2: *프롬프트 길이/지시성* 성분만 분리 | 자원·공정성과 무관한 동일 길이 배너. "덜 가져가라"류 단서 0 |

> **읽는 법.** 출력측(`dumb_cap`·`social`)은 *나온 요청을 깎고*, 입력측(`reputation_feedback`·`superordinate`)은 *캡 없이 프롬프트만 바꾼다*. 두 대조군은 입력 효과를 (숫자 앵커) + (길이) + (사회적 표현) 세 성분으로 쪼개기 위한 장치다. §5.2~5.4의 결론은 모두 이 분해에서 나온다.

---

## 5. 결과

### 5.1 통제 표 (V6, N=30, 공통 기준점)

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
| welfare: social vs none | .0028 | **.022** | ✅ 출력 "사회" 정책이 후생을 **해침** |
| welfare: neutral_filler vs none | .042 | .29 | ns (길이 효과는 보정에서 사라짐) |
| top: social vs dumb_cap (F4) | .127 | .76 | ns → **사회 ≈ 더미 캡 (공정성)** |
| welfare: fairshare_anchor vs neutral_filler | .196 | .98 | ns (앵커 효과 없음) |
| top: reputation_feedback vs none | .360 | 1.0 | **ns → 독점 효과 없음** |
| welfare: superordinate vs none | .427 | 1.0 | ns (후생 중립) |
| welfare: reputation_feedback vs none | .611 | 1.0 | **ns → 후생 효과 없음** |
| welfare: reputation_feedback vs fairshare_anchor | .881 | 1.0 | **ns → "사회적" 표현은 아무 것도 더하지 않음** |

### 5.3 평판 되먹임 헤드라인은 착시였다 (F1+F2)

따로 기준점을 둔 옛 실험(V1, N=24)에서 reputation_feedback은 welfare 0.61→0.79 (p=.027), top-share 0.715→0.522 (p=.019)로 효과가 있어 보였다. 그런데 공통 기준점(V6)에서 *같은* 프롬프트는 welfare 0.69 대 none 0.66 (**p=.61**), top-share 0.588 대 0.651 (**p=.36**) — 둘 다 귀무다. 옛 "효과"의 정체는, V1 기준점이 우연히 낮게 뽑힌 것(0.61 대 V6의 0.66)이었다. 정확히 동료심사가 짚은 표류다. 게다가 reputation_feedback ≈ fairshare_anchor (welfare p=.88): 평판·또래·규범 표현을 다 벗기고 숫자 공정-몫 문장만 남겨도 결과가 똑같다 — 효과가 있다면 그건 *사회적 기제가 아니라 앵커링*이다.

### 5.4 내용 없는 들러리 배너가 후생 1등을 한다

`neutral_filler` — 자원·공정성·평판 얘기가 하나도 없는 배너 — 가 후생 점추정 **최고치(0.82)**로, 정성껏 설계한 모든 셰이퍼를 이겼다. none 대비 우위는 Holm을 통과하지 못하므로(p=.042→.29) 우리는 "들러리가 도움이 된다"고 주장하지 않는다. 요점은 정반대다: **입력 배너의 후생 차이는 사회적 기제 설계 덕분이 아니다** — 내용 없는 배너가 설계된 것들과 맞먹거나 더 나으니까. "입력 프레이밍은 사회적이라서 통한다"는 서사에 대한 가장 깨끗한 반증이다.

### 5.5 진짜로 살아남은 것

통제·보정 검정을 통과한 효과는 둘이다.
1. **상위 정체성이 독점을 줄인다** (top-share 0.65→0.41, p_holm<.001) — 다만 후생 효과는 귀무다(p=.43). 견고한 행동 신호를 가진 유일한 입력 레버다. 그러나 우리는 reputation_feedback을 강등시킨 것과 *똑같은* 회의를 여기에도 적용한다: superordinate는 **자기 자신의 앵커링 대조군이 없으므로**(§7), 이 감소의 일부는 정체성이 아니라 일반적 지시-따르기일 수 있다. 그래서 "정체성 프레이밍이 통한다는 증명"이 아니라 **견고하지만 아직 분해되지 않은(undecomposed) 효과**로 보고한다.
2. **출력 "사회" 정책이 후생을 줄인다** — 무규제 대비(0.66→0.39, p_holm=.022), 게다가 공정성에선 더미 비례 캡과 구분되지 않는다(p=.13). 이 시나리오에서 "사회" 기계장치는, 후생까지 갉아먹는 *재명명된 요청 제한기*다.

---

## 6. 논의

**헤드라인은 살아남지 못했다 — 그것이 발견이다.** 옛 "입력 승리"의 두 기둥 중, 평판 되먹임은 앵커링 착시로 무너졌고 superordinate의 후생 이득은 귀무였으며, 살아남은 건 그 독점 감소뿐이다. 그래서 우리는 "입력이 출력을 이긴다"고 말할 수 없다. 대신 더 날카롭고 유용한 것을 말할 수 있다: **보고된 탐욕-거버넌스 효과 대부분은 실험 설계에 취약하다.** 표준 관행인 "따로 기준점 + 여러 시드" 방식이 우리 손에서 두 개의 가짜 양성(V1 평판, 옛 "사회 후생 0.75")을 만들었고, 둘 다 공통 기준점과 앵커 대조군 앞에서 사라졌다.

**방법론 처방.** (1) 모든 거버넌스 arm을 *하나의* 기준점·하나의 실험에서 재라. arm별 기준점은 N≤30에서 효과 크기만큼 표류한다. (2) 프롬프트 개입에는 반드시 **앵커링 대조군**(규범·사회 표현을 벗긴 맨 정보)과 **길이 대조군**을 넣어라. 없으면 "사회적 기제" 주장이 단순 지시-따르기와 구별되지 않는다. (3) 이산·소표본 변수엔 정규근사 말고 원자료 위 순열/bootstrap을 쓰고 다중성을 보정하라. 우리 "p<.05" 효과 셋이 Holm 뒤 증발했다.

**문헌과의 관계.** 우리의 "사회 정책 = 더미 캡" 결과는 회의론자의 "재명명된 요청 제한기"와 일치한다. 그리고 우리의 앵커-대조 결과는 *새 경고*를 던진다: GovSim/ALIGN 계열의 입력측 결과(보편화·가십 프롬프팅)는, 내재화된 사회적 기제의 증거로 읽기 전에 먼저 앵커링 귀무가설에 대해 재검정되어야 한다.

---

## 7. 한계

- **단일 모델·단일 시나리오·단일 작동점.** GLM-4.6; resource-task, 에이전트 3, 풀=360, r=8, N=30. "캡이 후생을 해친다"는 발견은 config에 민감하다: 무규제 탐욕이 전원을 굶기지 않는 곳(none 후생 0.66)에선 캡이 주로 완주 가능한 에이전트를 throttle한다. 더 파국적인 곳(큰 N·작은 풀)에선 캡이 후생을 *구할* 수도 있다. 풀/에이전트 스윕이 핵심 다음 과제다.
- **귀무 ≠ 0.** N=30은 작은 효과를 못 잡는다. reputation_feedback·superordinate-후생은 "유의하지 않음"이지 "효과 0"이 아니다. 다만 앵커링 귀무(rep ≈ anchor, p=.88)는 *사회적* 해석에 대해선 양의 반대 증거다.
- **시드 없는 백엔드.** 고정 안 된 OpenRouter 라우팅 모델 위 온도-0.7 추출. 임계 근처 결과는 런마다 흔들린다(이게 바로 §5.3의 요점이다).
- **superordinate도 앵커링일 수 있다.** reputation_feedback엔 앵커 대조군을 붙였지만 superordinate엔 아직 못 붙였다. 그 독점 효과는 견고하지만 정체성 대 지시로 분해되지 않았다.

---

## 8. 결론 및 향후 과제

LLM-에이전트 탐욕 거버넌스에 대한 통제·앵커대조·다중보정 실험은 **대부분의 후보 효과가 측정 착시**임을 보였다: 9개 비교 중 상위-정체성의 독점 감소와 출력 "사회" 정책의 후생 *비용*만 살아남았다. 평판 되먹임의 "승리"는 기준점 표류에 숫자 앵커링이 더해진 것이었고, 내용 없는 배너가 후생 1등을 했다. 재사용 가능한 토대, 앵커링-대조 방법론, 그리고 정직하게 기록한 자기 수정(결정적 단일 런이 헤드라인 2개를 뒤집음)이 기여다. 향후 과제: (1) 상위 정체성에 앵커 대조군 추가; (2) 출력 캡이 후생을 돕는/해치는 지점을 지도화하는 풀/에이전트 스윕; (3) 살아남은 효과의 멀티모델 재현과 N≥100; (4) 간접 상호성 기제(여기엔 없음)가 실제로 작동할 장기·반복 상호작용 시나리오.

---

## 부록 A — 동료심사 응답 (Major Revision)

| 이슈 | 심사자 | 해결 |
|---|---|---|
| F1 입력/출력 동일 실험 내 미배치; 기준점 표류 | DA-A1, R1 | **V6가 모든 arm을 단일 공통 기준점에서 실행(N=30).** 착시 확인: 평판 되먹임의 V1 효과가 사라짐. |
| F2 reputation_feedback에 앵커링 대조군 없음 | DA-A2, R2 | **`fairshare_anchor` + `neutral_filler` 추가.** rep ≈ anchor (p=.88) → 효과는 사회가 아니라 앵커링. 헤드라인 제거. |
| F3 무효한 정규근사 z; 다중성 미보정 | R1 | **bootstrap CI + 순열검정 + Holm.** 이전 "p<.05" 효과 셋이 통과 못 함. |
| F4 "사회 = 캡" 과잉일반화 | R2 | "우리 평판+배제 정책, 이 config"로 범위 한정; V6가 사회 ≈ 더미 캡 확인(p=.13). 7-에이전트 반례는 config 의존으로 인정. |
| F5 "multi-seed" 명칭 오류; 출처(provenance) | R3 | "replications"로 개명; V6 JSON이 config + 원시 반복별 배열 저장. 제공자-고정·비용 로깅은 잔여로 명시. |
| 신규성 과장 | R2 | §2 재구성: 이분법은 메커니즘 디자인 대 인-컨텍스트 조정; 기여는 통제된 검정 + 앵커링 귀무. |
| 제목 과장 | R2, DA-A3 | 제목을 "입력이 출력을 이긴다"에서 부정적·방법론 결과로 변경. |

---

## 부록 B — 대시보드 연동 (라이브 · 히스토리)

DASHBOARD_WIDGET

---

## 참고문헌 (원문 링크)

**위험 · 택소노미**
- [Hammond et al., *Multi-Agent Risks from Advanced AI* (CAIF 2025) — arXiv:2502.14143](https://arxiv.org/abs/2502.14143)
- [Piatti et al., *Cooperate or Collapse (GovSim)* (NeurIPS 2024) — arXiv:2404.16698](https://arxiv.org/abs/2404.16698)
- [Vallinder & Hughes, *The Subtle Art of Defection* 2025 — arXiv:2511.15862](https://arxiv.org/abs/2511.15862)
- [*Corrupted by Reasoning* 2025 — arXiv:2506.23276](https://arxiv.org/pdf/2506.23276)
- [*Scheming Ability in LLM-to-LLM Strategic Interactions* — arXiv:2510.12826](https://arxiv.org/abs/2510.12826)
- [*Secret Collusion among AI Agents* (NeurIPS 2024) — arXiv:2402.07510](https://arxiv.org/pdf/2402.07510)
- [Lupinacci et al., *The Dark Side of LLMs* 2025 — arXiv:2507.06850](https://arxiv.org/abs/2507.06850)
- [*When Identity Overrides Incentives* 2026 — arXiv:2601.10102](https://arxiv.org/html/2601.10102)

**출력측 — 메커니즘 디자인 · 강제**
- [*Institutional AI: A Governance Framework* — arXiv:2601.10599](https://arxiv.org/abs/2601.10599)
- [*Institutional AI: Governing LLM Collusion in Cournot Markets* — arXiv:2601.11369](https://arxiv.org/html/2601.11369v1)
- [A2A Protocol Specification](https://a2a-protocol.org)

**입력측 — 사회심리학**
- [Chen et al., *AI Agent Behavioral Science* — arXiv:2506.06366](https://arxiv.org/abs/2506.06366)
- [*Talk, Judge, Cooperate (ALIGN)* — arXiv:2602.07777](https://arxiv.org/abs/2602.07777)
- [Vallinder & Hughes, *Cultural Evolution of Cooperation among LLM Agents* — arXiv:2412.10270](https://arxiv.org/abs/2412.10270)
- [*Social Learning & Collective Norm Formation* (AAMAS 2026) — arXiv:2510.14401](https://arxiv.org/pdf/2510.14401)
- [*Mind the (Belief) Gap* — arXiv:2503.02016](https://arxiv.org/abs/2503.02016)
- Milinski et al., *Reputation helps solve the tragedy of the commons*, Nature 2002.
- Fehr & Gächter, *Cooperation and punishment in public goods experiments*, 2000.

**역효과 · 모니터링**
- [*When Agents See Humans as the Outgroup* 2026 — arXiv:2601.00240](https://arxiv.org/abs/2601.00240)
- [*An Empirical Study of Group Conformity in MAS* 2025 — arXiv:2506.01332](https://arxiv.org/abs/2506.01332)
- [*Social Simulations Risk Utopian Illusion* 2025 — arXiv:2510.21180](https://arxiv.org/pdf/2510.21180)
- [Korbak et al., *Chain of Thought Monitorability* — arXiv:2507.11473](https://arxiv.org/abs/2507.11473)
- [Baker et al., *Monitoring Reasoning Models for Misbehavior* — arXiv:2503.11926](https://arxiv.org/abs/2503.11926)

*전체 40여 편 문헌 리뷰: [`docs/research_2.md`](research_2.md). 실험 아티팩트: [`docs/verify_v6.json`](verify_v6.json)(원자료), [`docs/verify_results.md`](verify_results.md), [`docs/peer_review.md`](peer_review.md), [`docs/re_review.md`](re_review.md), [`scripts/verify_claims.py`](../scripts/verify_claims.py).*
