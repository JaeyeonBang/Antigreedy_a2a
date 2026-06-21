# 사회심리학 기반 거버넌스 전략 — 실험 리포트

> Antigreedy A2A 테스트베드 · 발표용 정리 · 측정일 2026-06-16
> 가설: **"전략(거버넌스 정책)을 추가하면 greedy(발언 독점)가 낮아진다."**
> 이번 리포트는 사회심리학 이론을 정책으로 구현해 **정량 전략과 동일한 방법으로 검증**한 결과다.

---

## 1. 실험 설계

- **시나리오**: 발언권-커먼즈 회의 — 공유 토큰 예산(commons)을 N개 에이전트가 나눠 씀.
  **greedy = 한 에이전트가 발언량(airtime)을 독점**해 합의 전에 예산을 고갈시키는 것.
- **에이전트 수**: **7명** (A–G). A는 발언을 독점하려는 탐욕적 dominator (mock 결정론적 백엔드).
- **공통 조건**: 커먼즈 예산 1400, 최대 6라운드, 같은 에이전트·같은 시드. **오직 전략만 다름.**
- **greed 지표**: `top_share` = 최대 단일 발언 점유 (1.0 = 완전 독점).
  **공정성 지표**: Jain index (1.0 = 완전 공정). **생존**: 합의/생존 여부(예산이 버텼는가).
- 모든 수치는 이벤트 로그의 순수 함수(`episode_end.metrics`)로 재현 가능.

---

## 2. 결과 (7 에이전트)

| 전략 | 이론 매핑 | greedy `top_share` | 공정성 Jain | 결과 | greed 감소 |
|---|---|---:|---:|:---:|---:|
| **전략 없음 (none)** | — (무규제 베이스라인) | **0.87** | 0.19 | 고갈 | — |
| 정량: Airtime quota | 발언 할당 (institutional) | 0.24 | 0.92 | 생존 | **72%** |
| 정량: Strict quota | 더 빡센 할당 | 0.24 | 0.93 | 생존 | **72%** |
| **사회: 평판·가십·배제** | 간접 상호성·Ostracism (①②) | **0.31** | 0.81 | 생존 | **64%** |
| 사회: 조건부 협력 | Conditional Cooperation (⑥) | 0.49 | 0.50 | 생존 | 44% |
| 사회: 보편화 | Universalization·Kant (⑤) | 0.62 | 0.35 | 고갈 | 29% |
| **★ 사회: 통합 스택** | 배제+평판+보편화 (§2 스택) | **0.24** | **0.93** | 생존 | **72%** |

**한 줄 요약**: 무규제에서 A가 발언의 **87%를 독점**하고 예산이 **고갈**된다. 전략을 추가하면
**모든 전략이 greedy를 낮추지만**, 사회 전략 사이에도 뚜렷한 위계가 있다.

---

## 3. 전략별 해석 (이론 → 구현 → 결과)

### ① + ② 평판·가십·배제 (Reputation + Ostracism) — 사회 전략 중 최강
- **이론**: 간접 상호성(Nowak & Sigmund 1998; Milinski *Nature* 2002)과 배제(Fehr & Gächter
  2000; Feinberg 2014). 명시적 처벌 없이 평판으로 공유지의 비극을 푼다.
- **구현**: 과거 발언 점유(turn_log)에서 각 에이전트의 **평판을 read-only로 파생**(단일 기록자
  규칙 준수). 평판이 낮을수록 허용량 축소(가십), 임계치(0.45) 미만이면 **배제(deny)**. 매 턴
  `gossip`/`ostracism` 이벤트 방송.
  → `policies/presets/social_reputation/{25_reputation_gossip,20_ostracism}.py`
- **결과**: top_share **0.87 → 0.31** (▼64%), Jain 0.19 → 0.81, **생존**. dominator A가 11회
  배제(deny)되며 발언량이 공정 수준으로 수렴. **정량 quota에 근접하는 최고 성능의 사회 전략.**
- **함의**: "탐지·처벌 중심의 외부 강제" 없이 **분산 평판**만으로 정량 규칙에 버금가는 결과.

### ⑥ 조건부 협력 (Conditional Cooperation) — 중간
- **이론**: 다수는 조건부 협력자 — 남이 절제하면 나도 절제(Fischbacher/Gächter/Fehr 2001).
- **구현**: 이번 턴 허용량을 **동료들의 최근 발언 평균 × 1.25**로 미러링. 무임승차자는 동료
  수준으로 축약. → `policies/presets/social_conditional/25_conditional.py`
- **결과**: top_share 0.49 (▼44%), Jain 0.50, **생존**. 절제하는 다수에 A를 끌어내리지만,
  A가 "동료 평균의 1.25배"까지는 허용돼 평판·배제보다 약함.

### ⑤ 보편화 (Universalization, Kant) — 가장 약함 (정직한 한계)
- **이론**: "모두가 이렇게 쓰면?"이라는 칸트식 추론. GovSim(2024)에서 지속가능성 향상.
- **구현**: `token×n > 잔여 커먼즈`면 보편화 불가 → 1/n 몫으로 축약.
  → `policies/presets/social_universalization/25_universalization.py`
- **결과**: top_share 0.62 (▼29%), Jain 0.35, **고갈**. **각 에이전트에게 자기 1/n 몫을 허용**
  하므로 A는 합법적으로 가장 큰 몫을 계속 취하고(=점유 높음), 토큰 하한(floor)이 겹쳐 합산
  예산이 결국 고갈. **"per-turn 보편화"는 공정 *개선*은 하나 *총량 지속가능성*은 보장하지 못함.**
- **함의(발표 포인트)**: 보편화 추론은 만능이 아니며(문헌의 *Corrupted by Reasoning* 역설과
  공명), **평판·배제 같은 누적적·사회적 기제와 결합**해야 강력해진다.

---

### ★ 통합 스택 (배제 + 평판 + 보편화) — 리서치 §2 "Agent Society Governance Stack"
- **이론**: 개별 레버보다 *폐루프 결합*(관찰→가십·평판→규범→배제)이 강력하다는 통합 설계.
- **구현**: 한 체인에 ostracism(priority 20, deny) → reputation_gossip(25, 캡) →
  universalization(25, 캡)을 결합. 배제가 먼저 최악 offender를 제거하고, 평판·보편화가 나머지를
  캡. → `policies/presets/social_stack/`
- **결과**: top_share **0.24**, Jain **0.93**, 생존(커먼즈 552 잔여) — 세 기제(gossip·ostracism·
  universalization)가 모두 발동. **정량 quota(0.24/0.92)와 동일 수준을 *순수 사회심리 기제만으로*
  달성.** 개별 사회 전략(최강 0.31)을 능가.
- **함의(핵심 발표 포인트)**: 사회 레버는 *결합될 때* 제도적 할당에 버금간다. 보편화처럼 단독으론
  약한 기제도 평판·배제와 묶이면 스택 전체 성능에 기여한다 — §2 통합 설계의 실증.

---

## 4. 결론 — 발표용 메시지

1. **가설 입증**: 전략을 추가하면 greedy가 낮아진다(0.87 → 최저 0.24). 7 에이전트에서 측정·테스트·
   라이브 UI로 모두 확인.
2. **사회심리 전략이 실제로 작동한다**: 명시적 감시·처벌 없이 **평판·가십·배제**만으로 greed를
   64% 낮추고 예산을 살린다 — 정량 할당에 근접.
3. **단, 사회 기제 간 위계가 있다**: 누적적 평판/배제 ≫ 조건부 협력 ≫ 보편화. 보편화 단독은
   공정성은 올리되 지속가능성은 못 지킨다(정직한 한계).
4. **함의**: selfish exploitation은 *사회적* 현상이므로 사회적 처방이 자연스럽고 효과적이다.
   다만 사회 레버는 *세심히 튜닝해야 하는 제어계*다(아래 리스크 참조).

---

## 5. ⚠️ 사회 레버의 역효과 (균형 잡힌 발표를 위해 반드시 포함)

본 실험은 *공정성/지속가능성*만 측정했다. 리서치가 경고하듯 사회 기제는 새로운 위험을 만든다:
- **In-group 편향 → 인간 out-group화** (*When Agents See Humans as the Outgroup*, arXiv:2601.00240)
- **동조 → 집단사고·편향 증폭** (*Group Conformity in MAS*, arXiv:2506.01332)
- **사회적 바람직성 편향 → 거짓 합의** (*Social Simulations Risk Utopian Illusion*, arXiv:2510.21180)
- **배제의 담합 악용** (다수가 정직한 소수를 배제) → 처벌 권한의 분산·검증 필요.
- **정체성이 유인을 압도** (*When Identity Overrides Incentives*, arXiv:2601.10102)

**설계 원칙**: ① 인간을 항상 같은 in-group에 포함, ② 동조 방지를 위한 구조적 다양성·반대役 강제,
③ 평판·배제 권한의 분산·검증.

---

## 6. 재현 방법

```bash
# 테스트 (전략이 greed를 낮추는지 — 7 에이전트)
.venv/bin/python -m pytest tests/test_strategy_reduces_greed.py \
                            tests/test_social_strategies_reduce_greed.py -q

# 라이브 비교 (대시보드): 에이전트 수 7 → 거버넌스 프리셋에서 전략 선택 → ▶ A/B 실행
python -m antigreedy.dashboard      # http://localhost:8000
```

- 정책 소스: `policies/presets/{social_reputation,social_universalization,social_conditional}/`
- 테스트: `tests/test_strategy_reduces_greed.py`, `tests/test_social_strategies_reduce_greed.py`
- 측정 원자료: 각 런의 `episode_end.metrics` (top_share, jain_delivered, delivered).

---

## 부록: 이론 출처 (요약)

- 간접 상호성·평판: Nowak & Sigmund 1998 · Milinski *Nature* 2002 · ALIGN (arXiv:2602.07777) ·
  Cultural Evolution of Cooperation among LLM Agents (arXiv:2412.10270)
- 배제·비싼 처벌: Fehr & Gächter 2000 · Feinberg 2014 · Optional PGG (arXiv:2110.02031)
- 보편화: GovSim (arXiv:2404.16698) · Corrupted by Reasoning (arXiv:2506.23276)
- 조건부 협력: Fischbacher/Gächter/Fehr 2001
- 패러다임: AI Agent Behavioral Science (arXiv:2506.06366)
- 역효과: arXiv 2601.00240 · 2506.01332 · 2510.21180 · 2506.01080 · 2601.10102

(전체 링크는 발표 원문 문서 참조.)
