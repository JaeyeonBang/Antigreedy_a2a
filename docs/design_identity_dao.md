# 설계 문서 — Impression + Identity DAO: 발언권 QV 시장과 창발적 정체성 거버넌스

*Design doc: a quadratic-airtime market + an elder-adjudicated reputation ledger + emergent identity clustering for anti-greedy LLM agent societies.*

**상태:** 설계 초안(구현 전). 이 프로젝트의 V6 통제 실험이 강제하는 대조군·통계 원칙을 처음부터 내장한다. 문헌 배경(§2)은 2026-06 웹 검증 + 기존 코퍼스([`research_2.md`](research_2.md)) 기반이며, *검증 안 된 인용은 그대로 표시*한다.

---

## 1. 동기와 V6와의 관계

이 testbed는 V6에서 두 가지를 *자기 데이터로* 보였다: (1) 평판 되먹임 효과는 사실 **앵커링**이었고(rep ≈ fairshare_anchor, p=.88), (2) 출력 "사회" 정책은 공정성에서 **더미 캡과 구분되지 않고**(p=.13) welfare를 *해쳤다*. 즉 "그럴듯한 사회적 기제"가 실제로는 단순 캡이거나 숫자 앵커였다.

이 설계는 그 교훈 위에서 **세 개의 진짜 질문**을 던진다.
1. **곡선이 중요한가?** 점유를 *선형*으로 깎는 기존 평판 캡 대신 *2차(quadratic)*로 깎으면 공정성-welfare 프런티어가 개선되는가? (이론: Weyl 2017 — "**quadratic일 때만** robustly optimal".)
2. **정체성은 부과가 아니라 창발할 수 있는가?** V6에서 유일하게 살아남은 입력 효과는 *부과된* "ONE TEAM" 배너(superordinate)였다. 정체성을 평판 클러스터에서 *자라나게* 하면, 그 효과가 "정체성" 때문인지 "지시" 때문인지 분해할 수 있다(§7 미해결 질문).
3. **빠른 인상 + 느린 원장의 2-속도 인지**가 greedy를 더 잘 걸러내는가?

---

## 2. 문헌 배경 (Literature Background)

> 표기: [V]=2026-06 웹 검증, [K]=지식 기반(미검증, 인용 전 확인 필요), [F]=기존 `research_2.md` 수록.

### 2.1 Quadratic Voting / Funding과 "주의(attention) 배분"

- **QV 기초.** 표를 v개 살 때 비용 = v²; 한계비용이 선형이 되어 *강도(intensity)*를 진실하게 드러낸다. Lalley & Weyl, *Quadratic Voting*, 2015 [V]; Lalley & Weyl, AEA P&P 2018, [aeaweb 10.1257/pandp.20181002](https://www.aeaweb.org/articles?id=10.1257/pandp.20181002) [V]. **핵심 정당화:** Weyl, *The Robustness of Quadratic Voting*, Public Choice 2017 — 투표 가격규칙이 robustly 최적인 것은 **오직 2차일 때뿐** ([SSRN 2571012](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2571012)) [V]. 소수 참가자에선 효율성이 *점근적*일 뿐이라는 한계: *Nash Equilibria for QV*, [arXiv 1409.0264](https://arxiv.org/pdf/1409.0264) [V].
- **고정예산 QV = "발언 예산"의 올바른 형식화.** *Fixed-budget and Multiple-issue Quadratic Voting*, [arXiv 2409.06614](https://arxiv.org/abs/2409.06614), 2024 — 에이전트마다 *동일 크레딧 예산*을 여러 이슈에 배분하며, 동기로 **"multi-agent resource allocation"과 "attention allocation"을 명시**한다. **우리 아이디어의 가장 가까운 선행연구** → QV-for-attention은 *완전히* 새롭지 않다(정직한 포지셔닝). [V, 단 본문 정확 문구는 PDF 직접 확인 권장]
- **QF(자금판)과 Sybil.** Buterin, Hitzig & Weyl, *Liberal Radicalism*, [arXiv 1809.06421](https://arxiv.org/abs/1809.06421) [V]; 영향력이 *서로 다른 신원 수*에 초선형으로 커져 **Sybil(신원 분할)이 지배적 공격** — 오케스트레이터가 하위 에이전트를 쉽게 스폰하는 에이전트 환경에선 인간 DAO보다 *더* 위험(BlockScience, *How to Attack and Defend QF*) [V].
- **선례.** *FedQV* (연합학습에서 QV 가중) — QV가 투표함 밖에서 쓰인 전례 [V]. 네트워크 경제학의 *볼록 혼잡 가격(convex congestion pricing)*은 대역폭에 이미 적용됨(우리의 발언세와 동형) [V].
- **갭/포지셔닝:** *발언권 혼잡 가격으로서의 QV*는 전용 논문이 없으나 2409.06614가 그 직관을 이미 언급. → 신규성은 **메커니즘 자체가 아니라 "LLM 에이전트 airtime에 대한 anti-greedy 적용 + 에이전트 고유 Sybil 위협모델"**에 둔다.

### 2.2 평판 시스템 · 탈중앙 원장 · DID · LLM 에이전트 평판

- **고전 계산 평판.** EigenTrust(고유벡터 전이신뢰), Kamvar et al. 2003, [PDF](https://nlp.stanford.edu/pubs/eigentrust.pdf) [V]; Beta Reputation(베이지안 α/β 업데이트 + 망각계수 λ), Jøsang & Ismail 2002 [V]; TrustRank(신뢰 시드에서 전파), Gyöngyi et al. VLDB 2004 [V]; 이미지 점수 간접상호성, Nowak & Sigmund, *Nature* 1998, [31225](https://www.nature.com/articles/31225) — 안정조건 **q > c/b**(상대 평판을 알 확률 > 비용/편익) → *원장을 모든 프롬프트에 복제*하면 q를 최대화 [V]. eBay 실증(평판은 미래를 예측하나 피드백이 호혜·보복으로 편향), Resnick & Zeckhauser 2002 [V].
- **온체인 평판·탈중앙 신원(강한 선행연구).** DeSoc/Soulbound Token(비양도 신원), Weyl·Ohlhaver·Buterin 2022, [SSRN 4105763](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4105763) [V]; W3C DID-Core [V]; **A2A + 원장 고정 신원 + x402**, [arXiv 2507.19550](https://arxiv.org/html/2507.19550) [V]; **ERC-8004 "Trustless Agents"**(에이전트 온체인 평판 레지스트리) [V]. → "온체인 에이전트 평판 원장"은 *이미 존재*; 우리 신규성은 거기 있지 않다.
- **LLM 에이전트 평판.** DRF(동적 평판 필터 + UCB 선택), [arXiv 2509.05764](https://arxiv.org/pdf/2509.05764) [V]; **skill-conditional 평판 공격**, [arXiv 2606.14200](https://arxiv.org/abs/2606.14200) — 교차-스킬 *평판 세탁*이 라우터를 장악(라우팅 후회 0→0.94), 방어는 예산제한적이며 **Sybil 불가능성을 상속** [V].
- **LLM-as-judge 신뢰성(우리 judge가 LLM이므로 핵심).** *LLMs Cannot Reliably Judge (Yet?)*, [arXiv 2506.09443](https://arxiv.org/html/2506.09443v1) [V]; *The Silent Judge*(미공개 shortcut 편향), [arXiv 2509.26072](https://arxiv.org/pdf/2509.26072) [V]; + 기존 CoT 불성실 인용(Baker 2025, Anthropic 2505.05410) [F].
- **불변성 ↔ 회복 갈등(우리 중심 위험).** GDPR↔블록체인 불변성, [arXiv 2210.04541](https://arxiv.org/pdf/2210.04541) [V]; redactable/chameleon-hash 체인, [arXiv 1907.07099](https://arxiv.org/pdf/1907.07099) [V; 제목·출처 검증]. → 잘못된 judge 판정이 *영구·전파*되면 갱생 불가 → Beta형 *시간 감쇠* 또는 redactable 설계 필요.
- **갭:** "**단일 elder가 rule+LLM을 융합해 유일 기록자로 쓰고, 원장을 프롬프트 메모리에 복제**"는 선행 대비 미탐구 조합. 단 *불변성 + LLM-judge 오류*의 상호작용은 누구도 연구 안 한 열린 갭.

### 2.3 창발적 사회 정체성 · 인상 형성 · 평판 클러스터링

- **정체성 기초.** 최소집단 패러다임(임의 범주화만으로 내집단 편향), Tajfel 1971 [V]; 자기범주화 이론(범주화→탈개인화·동조·고정관념), Turner et al. 1987 [V]. *논문 인용은 Tajfel & Turner 1979 원전을 쓸 것*(현 코퍼스는 2차 출처) [V].
- **빠른 인상 채널의 근거.** 고정관념 내용 모델(SCM: warmth·competence 2축, **warmth(의도)를 먼저** 판단), Fiske et al. JPSP 2002 [V]; 중심특질 게슈탈트(warm/cold), Asch 1946 [V]. → "이 에이전트가 greedy한가?"는 **저-warmth(착취 의도) 스냅 판단** = 우리 LLM-gestalt 채널의 원리적 특징공간.
- **컨벤션/창발(핵심 벤치마크).** 사회적 법칙(*오프라인 설계*=부과형), Shoham & Tennenholtz 1995 [V]; **창발적 사회 컨벤션 + 집단 편향 in LLM 인구**, Ashery·Aiello·Baronchelli, *Science Advances* 2025, [arXiv 2410.08948](https://arxiv.org/abs/2410.08948) — 탈중앙 LLM 집단이 자발적으로 컨벤션에 수렴, 개인이 무편향이어도 *집단 편향 창발*, 소수 임계질량이 전복 [V]. *창발이 더 단순한 동역학으로 환원될 수 있다는 경고*, [arXiv 2505.23796](https://arxiv.org/pdf/2505.23796) [V; 제목 확인 요].
- **클러스터링 도구.** Louvain(모듈성 최적화), Blondel et al. 2008, [arXiv 0803.0476](https://arxiv.org/abs/0803.0476) [V]; **Leiden(연결성 보장, Louvain의 단점 수정)**, Traag et al. 2019 — *정체성 클러스터엔 Leiden 사용*(단절 클러스터 방지) [V]. 우리 [`graphify`](research_2.md) 커뮤니티 검출을 재사용 가능.
- **2-속도 인지 비유.** System 1/2, Kahneman 2011 [V] → 빠른 인상=S1, 느린 원장=S2.
- **갭/신규성:** (a) *부과* 정체성(Shoham–Tennenholtz, 우리 "ONE TEAM" 배너) 대 *창발* 정체성(평판 그래프 모듈성에서 도출) — 선행 없음; (b) *대칭 조정* 컨벤션(Ashery 네이밍게임) 대 *비대칭 평가/스크리닝* 컨벤션(greedy 판별); (c) 이중채널 정체성 갱신. **신규성은 새 현상이 아니라 *조합 + 스크리닝 용도*에 있다**(정직).
- **신규 위험(코퍼스 §5.4에 없음): 카스트화.** 자기범주화 + 평판 되먹임 → 한 번 "greedy"로 군집되면 상호작용에서 배제 → 평판 회복 불가 → *자기실현적 카스트*. 우리 ostracism은 "자기교정적(배제→회복)"으로 설계됐는데 **불변 원장이 그 교정을 깬다** → 핵심 설계 긴장.

---

## 3. 아키텍처 — 4개 원시(primitive)

| # | 원시 | 한 줄 | 계층 | 신규성 |
|---|---|---|---|---|
| A | **QV 발언세** | 한 대상/세션 집중 발언에 2차 비용 | 출력 | 적용+위협모델 |
| B | **Elder(꼰대) judge** | rule+LLM 융합 평판 산정 | 평가 | 단일 융합 기록자 |
| C | **복제 평판 원장** | append-only + 모든 프롬프트에 복제 | 기록 | 불변+LLM판정 갭 |
| D | **창발 정체성** | 평판벡터 군집(Leiden)→정체성→greedy 스크리닝 | 정체성 | 창발>부과, 스크리닝 |

### 3.1 (A) 발언세 — 두 가지 형태

**자기-집중형(self-concentration, resource-task 호환, Phase A):** 공유 풀 시나리오엔 "대상 j"가 없으므로 *자기 누적 점유*에 2차 가격을 매긴다.
```
share_i = mine / total ;  fair = 1/n ;  o_i = max(0, share_i − fair)/fair   # 정규화 과점도
flat:       cap_i = max(floor, ⌊remaining · k⌋)                 # = 기존 dumb_cap (대조)
linear:     cap_i = max(floor, ⌊remaining · k · (1 − o_i)⌋)     # = 기존 gossip 캡과 동형 (대조)
quadratic:  cap_i = max(floor, ⌊remaining · k / (1 + o_i²)⌋)    # ★ QV: 과점도의 제곱으로 캡 축소
```
직관: 공정몫 이하면 셋 다 full. 과점할수록 quadratic 캡이 *제곱으로* 줄어든다(o=1→½, o=2→1/5, o=3→1/10).

> ⚠️ **정직성 경고 (플랜 리뷰 반영, 2026-06).** 이 자기-집중형 `1/(1+o²)`는 **진짜 QV가 아니다.** QV의 본질은 *고정 예산에서 v²로 영향력을 구매*(지불·한계비용=한계가치)하는 것인데, 여기엔 예산도 지불도 v² 비용도 없다 — 오케스트레이터가 사후 절단할 뿐이다. 따라서 Weyl-2017 정리는 이 곡선을 *직접 정당화하지 못하며*, Weyl은 **동기**로만 인용한다(V6 교훈: 그럴듯한 이름 ≠ 기제). *진짜 QV*는 §3.1 대상-집중형(예산 `Σ m_ij²`, meeting 시나리오 = Phase D)으로만 구현된다. 자기-집중형은 **"볼록 cap-감쇠 곡선(convex cap-decay)"**으로 부른다.
> 또한 곡선은 *모양*뿐 아니라 *평균 캡 강도*도 함께 바꾼다(o>0에서 `1/(1+o²) ≥ 1−o` → quad이 평균적으로 더 느슨). 그래서 곡선 *모양* 효과를 분리하려면 **iso-fairness 보정**이 필수다: 각 곡선의 k를 *같은 top-share*가 되도록 맞춘 뒤 welfare를 비교(그래야 "곡선이 더 적은 welfare 비용으로 같은 공정성"인지 식별 가능).

**대상-집중형(targeted airtime, meeting 시나리오, Phase D+):** 에이전트 i가 라운드에 대상별 m_ij 토큰 사용 → 예산 B 안에서 `cost_i = Σ_j (m_ij)² / rep_i`. 한 상대에 쏠리면 제곱 폭증. *대조군:* 평판 무시 `Σ m_ij²`. **Sybil 방어:** 예산을 비양도 신원(SBT/DID 유사)에 고정해야 분할 공격 무력화(§2.1).

### 3.2 (B) Elder judge
```
rep_i = α · rule_i + (1 − α) · llm_i
  rule_i = 기존 _reputation(점유 기반) 또는 Beta 업데이트 E=(r+1)/(r+s+2)
  llm_i  = elder LLM이 발화에서 매긴 협력성 점수 ∈ [0,1]
```
두 신호를 **분리 기록**(앵커 대조: 숫자만 vs 서사 포함 — V6 F2 교훈). 위험(§2.2): 단일 elder=중앙화·SPOF·포획; LLM 판정 불성실·조작가능. → Phase 2, 그리고 *반드시* rule-only 대조군과 함께.

### 3.3 (C) 복제 원장
append-only 블록 `(judge, target, rep, evidence_hash, round)`; 각 프롬프트에 동일 스냅샷 주입(정합성, q↑). **카스트 방지(핵심):** 불변 기록 + *가변 뷰* — 평판 뷰 = 최근 W라운드 가중 누적(Beta 감쇠 λ), 또는 redactable(chameleon-hash) 만료. 즉 "기록은 영구, 영향력은 감쇠".

### 3.4 (D) 창발 정체성
```
평판벡터 R_i = (i가 보는 각 j의 rep)         # 누가 누구를 어떻게 보는가
유사도 그래프 W_ij = cos(R_i, R_j)
클러스터 = Leiden(W)  (Louvain 아님 — 연결성 보장)
정체성 = 클러스터 라벨 ;  greedy 스크리닝 = 신규 j를 가장 가까운 클러스터에 배정해 즉시 추정
```
모듈성 Q를 *종속변수*로 측정(클러스터가 실재하는가 vs 균질 수프). graphify 재사용.

---

## 4. 위협 모델 (반드시 대조·측정)

| 위협 | 출처 | 설계 대응 |
|---|---|---|
| **Sybil(신원 분할)** | QF, 2606.14200 | 발언 예산을 비양도 신원에 고정; 대칭 평판은 Sybil 불가능성 상속 → 비대칭 함수 |
| **담합/평판 세탁** | Hoffman 2009, 2606.14200 | elder 단일기록 vs 또래투표 트레이드오프; 세탁 후회 측정 |
| **카스트화(회복 불가)** | 신규(Turner+되먹임) | 불변기록+감쇠뷰; low-rep 회복률을 종속변수로 |
| **LLM-judge 오류·조작** | 2506.09443, 2509.26072 | rule-only 대조; 적대 프롬프트 robustness 측정 |
| **앵커링 착시** | 본 프로젝트 V6 | 숫자만 원장 대조군(F2) |
| **소수 임계질량 전복** | Ashery 2025 | 오염 소수 비율 스윕, 스크리닝 정확도 측정 |

---

## 5. 실험 설계

**방법론은 V6와 동일:** 단일 공통 baseline·단일 실험·**대조군 필수**·bootstrap CI·순열검정·Holm 보정·원시 반복별 저장. GLM-4.6, temp 0.7, 3 에이전트(스윕 시 확장), pool=360, r=8, N≥30. 하니스: [`scripts/verify_claims.py`](../scripts/verify_claims.py)의 `run_v6` 패턴 확장.

> **플랜 리뷰 결과(2026-06) — 첫 실험은 Welfare-rescue 스윕으로 결정.** 3인 패널 리뷰에서 Phase A(곡선 검정)는 2/3 NO-GO: ① `1/(1+o²)`는 진짜 QV가 아님(예산·v² 비용 없음 → Weyl 정리 미적용, §3.1 경고 반영), ② floor=30+슬랙0에서 조작이 죽음(세 곡선이 floor로 붕괴), ③ n=3은 QV 이론이 무예측. 대신 **논문 §7이 지목한 welfare-rescue 스윕**(정보/달러 최고)을 첫 실험으로 선택 — V6의 "캡이 welfare를 해친다"가 *config 의존*인지(파국적 영역에선 캡이 welfare를 *구하는가*) 직접 검정한다. 곡선(flat/quad)은 2차 요인으로 포함되어 곡선-null도 정보가 된다.

### Phase A′ — Welfare-rescue 스윕 (실행 실험, `welfare_rescue`)
희소도 `s = pool/(n·workload)`를 **풍요→파국**으로 스윕(s∈{1.0, 0.5, 0.33}, workload=120 고정, pool=⌊s·n·workload⌋), arm={none, cap_flat(=더미캡), cap_quad(=볼록감쇠)}. 핵심은 **상호작용**: `sign(welfare_cap − welfare_none)`이 희소도에 따라 *부호를 뒤집는가*. **메트릭 트랩 주의**: 완주율은 에이전트별 all-or-nothing이라, 희소 영역에서 공정 분배는 *전원 부분완료(완주 0)* 인 반면 탐욕은 *1명 완주* → 캡이 welfare를 *더* 해칠 수 있음. top-share(공정성)는 별도로 보고(캡이 공정성은 구해도 완주-welfare는 못 구하는 분리 가능성). 어느 쪽이든 논문 §7 caveat를 *날카롭게* 만든다. 주가설족(Holm): regime×{cap_flat,cap_quad}의 welfare vs none 6개.

### Phase A — 곡선 검정 (가장 싸고 즉시 구현)
resource-task, 4-arm 공통 baseline:

| arm | 캡 가중 | 역할 |
|---|---|---|
| `none` | — | 기준점 |
| `cap_flat` | k | 더미 캡 대조(곡선 무효과의 귀무) |
| `cap_linear` | k·(1−o) | 선형 과점가격(기존 gossip 동형) |
| `cap_quad` | k/(1+o²) | ★ QV 2차 과점가격 |

**사전 대조(Holm family):** ① top: quad vs none ② welfare: quad vs none ③ **top: quad vs flat**(곡선이 캡을 이기나) ④ **top: quad vs linear**(2차가 선형을 이기나 — Weyl 핵심) ⑤ welfare: quad vs linear ⑥ top: linear vs flat ⑦ welfare: quad vs flat. **주가설 H1:** quad가 같은 welfare에서 top-share를 linear보다 더 낮춘다(공정성-welfare 프런티어 우월). **귀무 위험(V6식):** quad ≈ flat이면 "이름만 QV".

### Phase B/C — Elder 원장 (Phase 2)
arms: `ledger_numbers_only`(앵커 대조) / `ledger_rule`(rule-only) / `ledger_elder`(rule+LLM). 대조: elder가 rule-only를 *유의하게* 넘는가, 아니면 또 앵커링인가. 종속: top·welfare + **low-rep 회복률**(카스트화) + 적대 프롬프트 하 판정 robustness.

### Phase D — 창발 정체성 (Phase 2)
meeting 시나리오. arms: `imposed_identity`(현 superordinate 배너) / `emergent_identity`(Leiden 클러스터 라벨 주입) / `no_identity`. 종속: top·welfare + **모듈성 Q** + **greedy 스크리닝 정확도** + **소수 오염 임계질량 robustness**(Ashery). 주가설: 창발 정체성이 부과 정체성의 효과를 *재현/분해*하는가.

---

## 6. 단계화와 권고

V6 교훈("한꺼번에 묶으면 무엇이 효과인지 구별 불가") 때문에 **A·D를 각각 단독·대조 검정**하고, B/C(중앙화·Sybil·카스트 위험 큼)는 phase 2. **가장 싼 첫 슬라이스 = Phase A의 `ConcentrationCapPolicy`(flat/linear/quad 한 정책, 곡선 파라미터)** — 기존 V6 하니스에 arm 4개로 끼워 N=30 한 번이면 "곡선이 중요한가"에 답한다.

## 7. 열린 질문
- 소수 에이전트(n=3)에서 QV는 *점근적* 효율성 밖(전략적 Nash) — 효과가 있어도 작을 수 있음. n 스윕 필요.
- 창발 정체성이 *인과적* 스크리닝을 하는가, 아니면 단지 상관인가(2505.23796 경고).
- 불변 원장의 카스트화를 감쇠뷰가 실제로 푸는가 — low-rep 회복률로 측정.

## 8. 참고문헌
§2의 인라인 링크 참조. 신규 추가분(코퍼스 미수록): QV(Lalley&Weyl 2015/2018, Weyl 2017, 2409.06614, 1409.0264, Buterin-Hitzig-Weyl 1809.06421, FedQV), 평판(EigenTrust 2003, Beta 2002, TrustRank 2004, Nowak&Sigmund 1998, eBay 2002, DeSoc 2022, DID, 2507.19550, ERC-8004, DRF 2509.05764, 2606.14200, LLM-judge 2506.09443/2509.26072, 불변성 2210.04541/1907.07099), 정체성(Tajfel 1971/Tajfel&Turner 1979, Turner 1987, Fiske 2002, Asch 1946, Shoham&Tennenholtz 1995, Ashery 2025 / 2410.08948, 2505.23796, Louvain 0803.0476, Leiden 2019, Kahneman 2011). *미검증 표시 항목은 인용 전 원문 확인.*
