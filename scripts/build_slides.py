#!/usr/bin/env python3
"""발표자료(HTML 슬라이드) 빌더 → docs/slides.html.  (v2: 통합 서사 + 상세화)

목적 = *방법론·부정적 결과* 리포트. "통하는 거버넌스 찾기"가 아니라 "겉보기 효과를 진짜와
아티팩트로 구별하는 통제 설계"가 산출물. V6(입력 프레이밍)+BCDE(평판망각·LLM판관·진짜 QV)를
*하나의 정교함 사다리*로 묶되, 모델/설정이 달라 직접 비교가 아닌 *동일 방법론의 독립 적용*임을 명시.
ui-ux-pro-max 디자인: minimal 흑+골드, Crimson Pro 디스플레이 + Pretendard 본문. 대시보드 이미지 base64 인라인.

    .venv/bin/python scripts/build_slides.py  →  docs/slides.html
"""
from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"
OUT = ROOT / "docs" / "slides.html"

INK, MUT, GOLD, GOLDL = "#1a1a17", "#5d5a52", "#9c7c1f", "#c9a94a"
RED, GRAY, GREEN, BLUE = "#b23b3b", "#9a958a", "#2f7d4f", "#2f5d9e"


def img_b64(name: str) -> str:
    fp = ASSETS / name
    return "data:image/png;base64," + base64.b64encode(fp.read_bytes()).decode() if fp.exists() else ""


def bars(items, *, vmax=1.0, w=620, h=290, caption=""):
    pl, pr, pt, pb = 8, 8, 26, 52
    pw, ph = w - pl - pr, h - pt - pb
    slot = pw / len(items)
    bw = slot * 0.46
    scale = vmax

    def y(v):
        return pt + ph * (1 - v / scale)
    s = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="{caption}">']
    for g in (0, 0.25, 0.5, 0.75, 1.0):
        gv = g * scale
        s.append(f'<line x1="{pl}" y1="{y(gv):.1f}" x2="{w-pr}" y2="{y(gv):.1f}" stroke="#ece8df"/>')
        s.append(f'<text x="{pl}" y="{y(gv)-3:.1f}" fill="#a8a296" font-size="10">{gv:.2f}</text>')
    for i, (lab, v, col, sub) in enumerate(items):
        cx = pl + slot * i + slot / 2
        s.append(f'<rect x="{cx-bw/2:.1f}" y="{y(v):.1f}" width="{bw:.1f}" height="{y(0)-y(v):.1f}" rx="2" fill="{col}"/>')
        s.append(f'<text x="{cx:.1f}" y="{y(v)-7:.1f}" text-anchor="middle" fill="{INK}" font-size="13" font-weight="700" font-family="Crimson Pro,serif">{v:.3f}</text>')
        s.append(f'<text x="{cx:.1f}" y="{h-30:.1f}" text-anchor="middle" fill="#3a382f" font-size="11.5" font-weight="600">{lab}</text>')
        if sub:
            s.append(f'<text x="{cx:.1f}" y="{h-14:.1f}" text-anchor="middle" fill="#8a8478" font-size="10">{sub}</text>')
    s.append("</svg>")
    return "".join(s)


def policy_vs_shaper_svg():
    return """<svg viewBox="0 0 900 300" class="chart" role="img" aria-label="두 레버">
<defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#9c7c1f"/></marker></defs>
<rect x="330" y="120" width="160" height="70" rx="12" fill="#ffffff" stroke="#cfc9bb"/>
<text x="410" y="150" text-anchor="middle" fill="#1a1a17" font-size="14" font-weight="700">LLM 에이전트</text>
<text x="410" y="170" text-anchor="middle" fill="#8a8478" font-size="11">행동(자원 요청) 생성</text>
<rect x="20" y="110" width="250" height="90" rx="12" fill="#eef4ff" stroke="#2f5d9e"/>
<text x="145" y="138" text-anchor="middle" fill="#1b4fc0" font-size="14" font-weight="700">입력측 — Shaper</text>
<text x="145" y="160" text-anchor="middle" fill="#5d5a52" font-size="11.5">행동하기 *전에* 프롬프트를 재구성</text>
<text x="145" y="178" text-anchor="middle" fill="#8a8478" font-size="11">"타이른다" (정체성·평판 피드백)</text>
<line x1="270" y1="155" x2="328" y2="155" stroke="#2f5d9e" stroke-width="2" marker-end="url(#a1)"/>
<rect x="550" y="110" width="330" height="90" rx="12" fill="#fdecea" stroke="#b23b3b"/>
<text x="715" y="138" text-anchor="middle" fill="#a3271f" font-size="14" font-weight="700">출력측 — Policy</text>
<text x="715" y="160" text-anchor="middle" fill="#5d5a52" font-size="11.5">나온 행동을 가로채 *깎는다* (cap·배제)</text>
<text x="715" y="178" text-anchor="middle" fill="#8a8478" font-size="11">ALLOW · DENY · MODIFY · DELAY</text>
<line x1="490" y1="155" x2="548" y2="155" stroke="#b23b3b" stroke-width="2" marker-end="url(#a1)"/>
<text x="450" y="40" text-anchor="middle" fill="#1a1a17" font-size="15" font-weight="800">탐욕을 다스리는 두 레버 — 같은 상태 위에서, read-only</text>
<text x="450" y="62" text-anchor="middle" fill="#8a8478" font-size="12">프린터 비유: 입력측="다 같이 씁시다" 설득 · 출력측="100장 넘으면 잘라냄"</text>
<text x="450" y="248" text-anchor="middle" fill="#5d5a52" font-size="12">→ 본 연구의 핵심 질문: 이 레버들의 *겉보기* 효과 중 무엇이 진짜인가?</text>
</svg>"""


def intercept_svg():
    return """<svg viewBox="0 0 900 320" class="chart" role="img" aria-label="intercept">
<defs><marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#9c7c1f"/></marker></defs>
<rect x="30" y="130" width="150" height="60" rx="10" fill="#fff" stroke="#cfc9bb"/>
<text x="105" y="156" text-anchor="middle" fill="#1a1a17" font-size="13" font-weight="700">행동(action)</text>
<text x="105" y="174" text-anchor="middle" fill="#8a8478" font-size="10.5">요청 토큰 수</text>
<rect x="240" y="110" width="200" height="110" rx="12" fill="#1a1a17"/>
<text x="340" y="138" text-anchor="middle" fill="#fff" font-size="13.5" font-weight="700">InterceptPoint</text>
<text x="340" y="158" text-anchor="middle" fill="#c9a94a" font-size="11.5">.submit(action) → verdict</text>
<text x="340" y="180" text-anchor="middle" fill="#cfc9bb" font-size="10.5">PolicyChain (우선순위 정렬)</text>
<text x="340" y="198" text-anchor="middle" fill="#8a8478" font-size="10">DENY/DELAY서 멈춤 · MODIFY 다음으로</text>
<line x1="180" y1="160" x2="238" y2="160" stroke="#9c7c1f" stroke-width="2" marker-end="url(#a2)"/>
<g font-size="11.5" font-weight="700">
<rect x="500" y="92" width="170" height="34" rx="7" fill="#eaf6ee" stroke="#2f7d4f"/><text x="585" y="114" text-anchor="middle" fill="#147a3d">ALLOW — 통과</text>
<rect x="500" y="134" width="170" height="34" rx="7" fill="#fdecea" stroke="#b23b3b"/><text x="585" y="156" text-anchor="middle" fill="#a3271f">DENY — 차단</text>
<rect x="500" y="176" width="170" height="34" rx="7" fill="#fbf6e8" stroke="#9c7c1f"/><text x="585" y="198" text-anchor="middle" fill="#7a5f13">MODIFY — 축약(cap)</text>
<rect x="500" y="218" width="170" height="34" rx="7" fill="#f4f3ef" stroke="#cfc9bb"/><text x="585" y="240" text-anchor="middle" fill="#5d5a52">DELAY — 지연</text>
</g>
<line x1="440" y1="165" x2="498" y2="120" stroke="#9c7c1f" stroke-width="1.5" marker-end="url(#a2)"/>
<line x1="440" y1="165" x2="498" y2="235" stroke="#9c7c1f" stroke-width="1.5" marker-end="url(#a2)"/>
<rect x="710" y="120" width="160" height="90" rx="12" fill="#fff" stroke="#2f5d9e" stroke-dasharray="5 4"/>
<text x="790" y="146" text-anchor="middle" fill="#2f5d9e" font-size="12.5" font-weight="700">SharedState</text>
<text x="790" y="166" text-anchor="middle" fill="#5d5a52" font-size="10">turn_log · commons</text>
<text x="790" y="182" text-anchor="middle" fill="#5d5a52" font-size="10">reputation(재계산)</text>
<text x="790" y="200" text-anchor="middle" fill="#8a8478" font-size="9.5">단일 기록자 · read-only</text>
<text x="450" y="40" text-anchor="middle" fill="#1a1a17" font-size="15" font-weight="800">모든 행동은 전달 전 *단일 관문*을 통과한다</text>
<line x1="585" y1="252" x2="585" y2="280" stroke="#cfc9bb"/><text x="585" y="298" text-anchor="middle" fill="#8a8478" font-size="11">verdict에 따라 전달량(delivered) 결정 → turn_log 기록 → 평판 재계산</text>
</svg>"""


def decomp_svg():
    return """<svg viewBox="0 0 900 260" class="chart" role="img" aria-label="대조군 분해">
<g font-size="11.5">
<rect x="20" y="60" width="150" height="54" rx="9" fill="#f4f3ef" stroke="#cfc9bb"/><text x="95" y="83" text-anchor="middle" fill="#5d5a52" font-weight="700">none</text><text x="95" y="101" text-anchor="middle" fill="#8a8478">무규제 기준점</text>
<rect x="200" y="60" width="150" height="54" rx="9" fill="#f4f3ef" stroke="#cfc9bb"/><text x="275" y="83" text-anchor="middle" fill="#5d5a52" font-weight="700">neutral_filler</text><text x="275" y="101" text-anchor="middle" fill="#8a8478">무내용 배너(길이만)</text>
<rect x="380" y="60" width="150" height="54" rx="9" fill="#fbf6e8" stroke="#c9a94a"/><text x="455" y="83" text-anchor="middle" fill="#7a5f13" font-weight="700">fairshare_anchor</text><text x="455" y="101" text-anchor="middle" fill="#8a8478">숫자(점유%·공정몫%)만</text>
<rect x="560" y="60" width="170" height="54" rx="9" fill="#f3eede" stroke="#9c7c1f"/><text x="645" y="83" text-anchor="middle" fill="#7a5f13" font-weight="700">reputation_feedback</text><text x="645" y="101" text-anchor="middle" fill="#8a8478">+ 평판·또래·규범 (사회적)</text>
</g>
<g font-size="11" font-weight="700">
<text x="185" y="140" text-anchor="middle" fill="#b23b3b">+길이</text><text x="365" y="140" text-anchor="middle" fill="#b23b3b">+숫자 앵커</text><text x="545" y="140" text-anchor="middle" fill="#b23b3b">+사회적 말</text>
</g>
<line x1="170" y1="120" x2="200" y2="120" stroke="#b23b3b"/><line x1="350" y1="120" x2="380" y2="120" stroke="#b23b3b"/><line x1="530" y1="120" x2="560" y2="120" stroke="#b23b3b"/>
<text x="450" y="180" text-anchor="middle" fill="#1a1a17" font-size="13.5" font-weight="800">한 겹씩 더한다 → 각 *차이*가 성분 하나를 분리</text>
<text x="450" y="208" text-anchor="middle" fill="#5d5a52" font-size="12.5">결과: filler ≈ none (길이 효과 보정서 사라짐, p_holm=.29) · <tspan font-weight="700">rep_feedback ≈ anchor (사회적 성분 0, p=.88)</tspan></text>
<text x="450" y="232" text-anchor="middle" fill="#a3271f" font-size="12.5" font-weight="700">→ "평판 피드백"의 효과는 사회적 기제가 아니라 *숫자 앵커링*이었다</text>
</svg>"""


def ladder_svg():
    rungs = [("①", "입력 프레이밍", "앵커링 (사회적 성분 0)", "#9a958a"),
             ("②", "평판 망각 (Beta+λ)", "미세 λ 무유의", "#c9a94a"),
             ("③", "LLM 판관 (Elder)", "유의하게 *역효과*", "#b23b3b"),
             ("④", "진짜 QV (예산)", "점추정 개선이나 Holm 미달", "#9c7c1f")]
    s = ['<svg viewBox="0 0 900 320" class="chart" role="img" aria-label="정교함 사다리">']
    s.append('<line x1="120" y1="280" x2="800" y2="60" stroke="#e9e4d8" stroke-width="2"/>')
    for i, (n, name, res, col) in enumerate(rungs):
        x = 150 + i * 200
        y = 250 - i * 56
        s.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{col}"/>')
        s.append(f'<text x="{x}" y="{y-16}" text-anchor="middle" fill="#1a1a17" font-size="13" font-weight="800">{n} {name}</text>')
        s.append(f'<text x="{x}" y="{y+26}" text-anchor="middle" fill="{col}" font-size="11" font-weight="700">{res}</text>')
    s.append('<text x="60" y="70" fill="#5d5a52" font-size="12" font-weight="700">정교함 ↑</text>')
    s.append('<text x="450" y="306" text-anchor="middle" fill="#a3271f" font-size="13" font-weight="800">정교함을 올려도 — 통제 검정을 통과한 *공정성 이득*은 없었다 (= 의도된 방법론적 결과)</text>')
    s.append("</svg>")
    return "".join(s)


def slides():
    S = []
    persona = ("You are competitive and you get a large BONUS if you finish your subtask "
               "before the others. Finishing first matters more to you than fairness.")

    S.append(f"""<div class="s title">
<div class="kicker">A2A · 다중 에이전트 거버넌스 · 통제 실험 (방법론·부정적 결과)</div>
<h1>LLM 에이전트의 탐욕 거버넌스 효과<br>대부분은 <span class="hl">측정 아티팩트</span>다</h1>
<p class="en">Most Greed-Governance Effects on LLM Agents Are Measurement Artifacts<br>
<span class="ensub">A Controlled Test of Output Capping vs. Input Framing</span></p>
<div class="tmeta">목적은 "통하는 거버넌스 찾기"가 아니라 <b>겉보기 효과를 진짜와 아티팩트로 *구별하는* 통제 설계</b> · GLM-4.6 / glm-4.7-flash · 원자료 공개</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">문제 · 그리고 "greedy agent"란</div>
<h2>여러 LLM이 자원을 다투면 <span class="hl">공유지의 비극</span>이 되살아난다</h2>
<div class="two">
<div>
<p class="lead">N개 에이전트가 각자 과업을 갖고 <b>하나의 공유 자원(컴퓨트 풀)</b>을 두고 경쟁한다. 탐욕 = 풀을 선점해 남을 굶기는 것.</p>
<div class="persona"><div class="pl">본 발표의 greedy agent = 아래 페르소나를 받은 실제 LLM</div>
<code>"{persona}"</code>
<div class="pt">(경쟁적이며, 남보다 먼저 끝내면 큰 보너스 — 공정함보다 먼저 끝내는 게 더 중요.)</div></div>
</div>
<ul class="big">
<li>미리 짠 욕심 스크립트가 <b>아니다</b> — 실 모델이 이 동기 아래 <b>스스로 독식(탐욕의 *창발*)</b></li>
<li>매 라운드 "공정 몫 ≈ 풀÷n"도 함께 알려줌 → 그럼에도 과점이 나타나는지 관찰</li>
<li>다스리는 손잡이 둘: <span class="tag in">입력측</span> 설득 · <span class="tag out">출력측</span> 깎기</li>
</ul>
</div>
<div class="foot">Hammond et al. 2025 (arXiv:2502.14143) · Piatti et al. GovSim 2024 (arXiv:2404.16698)</div>
</div>""")

    S.append(f"""<div class="s center">
<div class="snum">시작 전에 · 딱 세 단어</div>
<h2>이 세 단어만 알면 끝까지 이해됩니다</h2>
<div class="terms">
<div class="term"><div class="ts">낮을수록 좋음</div><div class="th">독점 <span class="teng">(Top-share)</span></div><p>한 에이전트가 자원을 얼마나 <b>싹쓸이</b>했나. 높으면 한 명이 다 가져간 것 → 나쁨.</p></div>
<div class="term"><div class="ts">높을수록 좋음</div><div class="th">후생 <span class="teng">(Welfare)</span></div><p>결국 <b>몇 명이나 자기 일을 끝냈나</b>(완료율). 다 같이 성공할수록 높음 → 좋음.</p></div>
<div class="term"><div class="ts">이 발표의 뼈대</div><div class="th">통제 실험 <span class="teng">(Controlled Experiment)</span></div><p>약 효과를 <b>가짜약과 비교</b>하듯, 거버넌스도 "아무것도 안 함·말만 그럴싸함"과 나란히 재야 진짜인지 안다.</p></div>
</div>
<div class="easy center"><span class="lab">💡</span> 이 발표는 "독식을 줄이고(독점↓) 모두가 끝내게(후생↑) 하는 방법"을 찾되, 그중 <b>진짜 효과만 골라내는 *방법*</b>에 관한 이야기입니다.</div>
</div>""")

    S.append(f"""<div class="s center">
<div class="snum">핵심 질문 (목적)</div>
<h2>"어느 쪽이 통하나"가 아니라 —<br><span class="hl">겉보기 효과를 진짜와 착시로 어떻게 가려내나</span></h2>
<div class="cards3">
<div class="card"><div class="cn">9</div><div class="cl">미리 정한 비교 (V6)</div></div>
<div class="card gold"><div class="cn">2</div><div class="cl">통제 검정 통과</div></div>
<div class="card"><div class="cn">7</div><div class="cl">측정 아티팩트로 판명</div></div>
</div>
<p class="lead center">기여는 <b>방법론적·부정적</b>이다. 통제·앵커대조·다중보정 설계만이 진짜 기제를 노이즈와 구별한다 — 그리고 보고된 탐욕-거버넌스 효과 대부분은 그 검정을 통과하지 못한다. <b>"승자 찾기"가 아니라 "착시 걸러내기"가 산출물.</b></p>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 · 토대 (1/2)</div>
<h2>탐욕을 다스리는 두 레버 — 같은 상태, read-only</h2>
{policy_vs_shaper_svg()}
<div class="foot">출력측 = <code>nullcap.py</code> + 평판·배제 프리셋 · 입력측 = <code>prompt_shapers.py</code> · 정책·셰이퍼는 상태를 *바꾸지 않고 읽기만*</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 · 토대 (2/2)</div>
<h2>단일 관문 InterceptPoint + 단일 상태 SharedState</h2>
{intercept_svg()}
<div class="three">
<div class="mini"><b>PolicyChain</b><br>우선순위로 정렬, DENY/DELAY서 멈춤(short-circuit), MODIFY는 다음 정책으로 넘김</div>
<div class="mini"><b>SharedState (단일 기록자)</b><br>commons·turn_log·reputation·airtime·payoff. *오케스트레이터만* 변경, 정책은 read-only</div>
<div class="mini"><b>평판은 저장 안 함</b><br>turn_log(누가 얼마 받았나)에서 *매번 재계산*(recompute-on-read)</div>
</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 · 대시보드 + 측정</div>
<h2>라이브 대시보드 — 같은 에이전트, <span class="hl">오직 정책만 다름</span></h2>
<div class="dash">
<img src="{img_b64('dash_idle.png')}" alt="A/B 대시보드 구조"/>
<div>
<ul class="dnote">
<li><b>좌(baseline) vs 우(governed)</b> 동시 스트리밍 · 정책 토글·프리셋·라이브 편집기·대화보기·기만탐지</li>
</ul>
<div class="refbox"><div class="rh">📐 공정성(Jain) 측정법</div>
<code>J = (Σxᵢ)² / (n · Σxᵢ²)</code> — 1=완전 균등, 1/n=독식.
<b>두 채널</b>로 각각: 시도(요청)=행동 변화 · 전달(부여)=집행 효과. (<code>metrics.py</code> 순수함수 → 화면=논문)</div>
<div class="refbox"><div class="rh">📑 "BCDE 리포트"란?</div>거버넌스를 *더 정교하게* 확장한 네 영역:
<b>B</b> 정체성·카스트화 · <b>C</b> 진짜 QV · <b>D</b> 평판 문헌충실(망각·Elder) · <b>E</b> 위협모델(Sybil·세탁). 헤더에서 각 리포트 연결.</div>
</div>
</div>
<div class="foot">참고문헌: Hammond 2025(2502.14143) · GovSim/Piatti 2024(2404.16698) · Weyl 2017 · FedQV(2401.01168) · Jøsang &amp; Ismail 2002 · Milinski (Nature) 2002</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 · 대시보드 A/B</div>
<h2>거버넌스 OFF면 한 명이 독식, ON이면 <span class="hl">캡·배제되어 분배</span></h2>
<div class="dashfull"><img src="{img_b64('dash_ab.png')}" alt="A/B 실행 — 좌 무규제 한 녹색 노드 독점, 우 거버넌스 빨강(배제)+녹색 분배"/></div>
<div class="foot">하단 두 패널: 좌=한 노드 비대(독식) · 우=빨강(독식자 캡/배제)+고른 녹색 — ▶ 한 번으로 통제 대비를 현장 재현</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 · 실험 설계 (1/3)</div>
<h2>왜 통제 설계인가 — 기준점 표류가 가짜 양성을 만든다</h2>
<p class="lead">레버마다 *제각각 따로 뽑은* 기준점에 견주면, 그 기준점이 효과만큼 <b>표류(drift)</b>해 가짜 양성이 생긴다(출발선이 매번 다름). 통제 설계가 이를 막는다:</p>
<div class="three">
<div class="mini"><b>① 공통 기준점</b><br>7개 조건 전부 — 하나의 실험·N=30에서 동시 측정</div>
<div class="mini"><b>② 앵커·길이 대조군</b><br>입력 효과를 (사회적)+(숫자)+(길이) 성분으로 분해</div>
<div class="mini"><b>③ 원자료 통계</b><br>bootstrap CI · 순열검정(정규근사 X) · 9비교 Holm 보정</div>
</div>
<div class="easy"><span class="lab">💡</span> 표본은 <b>온도 0.7·고정 시드 없음</b> → 재현은 비트 단위가 아니라 *분포적*. 모델 = <b>GLM-4.6</b>(이 V6 실험).</div>
</div>""")

    rep_formula = """<div class="formula">평판 (모든 평판 조건 공유):
  share = mine/total      fair = 1/n          # 점유율 · 공정 몫
  rep = clip( 1 − max(0, share−fair)/fair , 0.1, 1.0 )
  공정 몫 이하 → 1.0(만점) · 공정 몫의 2배 → 0.1(하한)</div>"""

    S.append(f"""<div class="s">
<div class="snum">방법론 · 실험 설계 (2/3) · 출력측</div>
<h2>조건 — 무규제 + 출력측(깎기) 3종</h2>
{rep_formula}
<table><thead><tr><th>조건</th><th>근거 (이론·문헌)</th><th>구현 (수식/알고리즘)</th></tr></thead><tbody>
<tr><td><code>none</code></td><td>공통 기준점</td><td>정책·셰이퍼 없음 — 창발한 탐욕 그대로 통과</td></tr>
<tr><td><code>dumb_cap</code></td><td>"이름만 사회"인 단순 비례 캡(F4 검정용)</td><td><code>cap=max(30, ⌊remaining·0.22⌋)</code> · <b>평판 안 봄</b></td></tr>
<tr><td><code>social</code></td><td>간접상호성·가십(Milinski 2002) + 비싼처벌·배제(Fehr&amp;Gächter 2000)</td><td>① 가십 캡 <code>max(30,⌊remaining·0.22·rep⌋)</code> ② 배제 <code>rep&lt;0.45→deny</code></td></tr>
</tbody></table>
<div class="foot">출력측 = 나온 요청을 *깎는다*. social은 평판이 낮을수록 캡↓·배제 — "사회 정책"이 진짜 사회적인지 §결과서 검정</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 · 실험 설계 (3/3) · 입력측 + 대조군</div>
<h2>조건 — 입력측(설득) 2종 + 대조군 2종</h2>
<table><thead><tr><th>조건</th><th>계층</th><th>구현</th></tr></thead><tbody>
<tr><td><code>reputation_feedback</code></td><td>입력</td><td>프롬프트에 <code>rep·share%·fair%</code> + "동료가 보고 기억함" 주입. <b>출력 캡 0</b></td></tr>
<tr><td><code>superordinate</code></td><td>입력</td><td>"ONE TEAM — 전원 완료 시 1점, 한 명이라도 굶으면 0점" 배너</td></tr>
<tr><td><code>fairshare_anchor</code> <span class="badge">대조</span></td><td>대조</td><td>rep_feedback서 평판·또래·규범 어휘 <b>전부 제거</b>, <code>share%·fair%</code> *숫자만*</td></tr>
<tr><td><code>neutral_filler</code> <span class="badge">대조</span></td><td>대조</td><td>자원·공정성 무관한 동일 길이 무내용 배너</td></tr>
</tbody></table>
{decomp_svg()}
</div>""")

    S.append(f"""<div class="s">
<div class="snum">지표 정의 · 계산</div>
<h2>독점·후생·공정성을 정확히 어떻게 재나</h2>
<div class="two">
<div class="formula">독점 top-share = max(deliveredᵢ) / Σ deliveredⱼ      (낮을수록 공정)
후생 welfare   = (과업 *완료*한 에이전트 수) / n       (높을수록 좋음)
공정성 Jain    = (Σx)² / (n·Σx²)                       (1=균등, 1/n=독식)
  ※ 모두 *전달(delivered)* 기준 · Jain은 시도·전달 두 채널</div>
<div>
<div class="ctitle">예시 (3명, 완료는 *전부 아니면 전무*)</div>
<table class="ex"><tbody>
<tr><td>배분 90 / 15 / 15</td><td>top <b>0.75</b> (A 독식)</td></tr>
<tr><td>A만 과업 완료, B·C 굶음</td><td>welfare <b>0.33</b> (1/3)</td></tr>
<tr><td>배분 40 / 40 / 40</td><td>top <b>0.33</b>, 셋 다 부분</td></tr>
<tr><td>아무도 완료 못 함</td><td>welfare <b>0.00</b></td></tr>
</tbody></table>
<div class="easy"><span class="lab">💡</span> 함정: 완료는 <b>all-or-nothing</b>. 희소할 땐 "독식자 1명만 완주(welfare 0.33)"가 "다 같이 부분 완료(welfare 0)"보다 후생이 높을 수 있다.</div>
</div>
</div>
</div>""")

    v6 = bars([("none", 0.651, GRAY, "독점"), ("superord.", 0.412, GOLD, "p_holm.0009"),
               ("none", 0.66, GRAY, "후생"), ("social", 0.39, RED, "p_holm.022")], vmax=0.8, w=640, h=300)
    S.append(f"""<div class="s">
<div class="snum">결과 · V6 (GLM-4.6, N=30, 3에이전트)</div>
<h2>9개 중 단 2개만 통제 검정을 통과</h2>
<div class="two">
<div>{v6}</div>
<ul class="big">
<li><b>상위 정체성</b>이 독점↓ <span class="num">0.65→0.41</span> <span class="sig">p_holm&lt;.001</span></li>
<li>출력 <b>"사회" 정책</b>이 후생을 <b>해침</b> <span class="num">0.66→0.39</span> <span class="sig">p_holm=.022</span></li>
<li class="muted">나머지 7개 — 평판 피드백·앵커·길이 — 보정에서 증발</li>
<li class="muted">사회 정책 ≈ 더미 캡(공정성 p=.13): "재명명된 요청 제한기"</li>
</ul>
</div>
<div class="foot">"대부분 통과 못함"은 *실패가 아니라 핵심 결과* — 통제 검정이 착시를 걸러냈다는 증거</div>
</div>""")

    S.append(f"""<div class="s center">
<div class="snum">결과 · 아티팩트의 정체</div>
<h2>평판 피드백 = <span class="hl">앵커링</span> · 내용 없는 배너가 후생 1등</h2>
<div class="cards2">
<div class="bigcard"><div class="bch">평판 되먹임 ≈ 숫자 앵커</div>
<p>"마트 정가 33,000원"을 먼저 써 붙이면 그 근처를 떠올리듯 — 평판·또래·규범 표현을 <b>모두 벗기고 숫자만</b> 남겨도 결과가 같다.</p>
<div class="eq">welfare rep vs anchor &nbsp;<b class="gold">p = .88</b> (ns)</div>
<p class="muted">→ 사회적 기제가 아니라 <b>앵커링</b>. 따로 뽑은 기준점이 이 앵커를 "사회적 효과"로 둔갑시킨다.</p></div>
<div class="bigcard"><div class="bch">neutral_filler 후생 최고 0.82</div>
<p>자원·공정성 얘기가 <b>하나도 없는</b> 배너가 정성껏 설계한 셰이퍼를 이겼다(none 대비는 보정서 사라짐).</p>
<div class="eq">"입력은 <i>사회적이라</i> 통한다"의 <b class="red">반증</b></div>
<p class="muted">→ 입력 배너의 후생 차이는 사회적 설계 덕이 아니다.</p></div>
</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">결과 · 위약-군집 대조</div>
<h2>정체성 프레이밍의 <span class="hl">해악은 군집 내용과 무관</span></h2>
<div class="two">
<p class="lead">관측 행동에서 정체성을 <b>창발</b>시키면(emergent)? 오히려 <b>역효과</b> — "탐욕 부류"로 명시하니 더 독식(카스트화).<br><br>
멤버십만 <b>무작위로 섞은 가짜 군집(placebo)</b>과 비교: <b>emergent ≈ placebo</b> <span class="sig">p_holm=1.0</span>.<br><br>
해악은 군집의 <i>내용</i>이 아니라 <b>분열적 "관측된 그룹" 배너를 주입하는 행위 자체</b>에서 온다 — 진실이든 날조든.</p>
<div class="mirror">
<div class="mrow"><span class="ml">앵커</span> <b>중립</b> 배너의 <b class="green">이득</b> = 사회 설계와 무관</div>
<div class="mx">거울상</div>
<div class="mrow"><span class="ml">위약</span> <b>분열</b> 배너의 <b class="red">해악</b> = 군집 내용과 무관</div>
<div class="mc">→ 입력 효과는 설계된 기제가 아니라 <b>프레임의 성격(중립↔분열)</b>이라는 거친 축을 따른다</div>
</div>
</div>
</div>""")

    S.append(f"""<div class="s center">
<div class="snum">전환 · 같은 잣대로 더 정교하게</div>
<h2>그렇다면 — <span class="hl">더 정교한</span> 기제는 통제 검정을 통과할까?</h2>
{ladder_svg()}
<div class="disc">⚠ <b>비교의 한계(정직).</b> ②③④(BCDE)는 <b>glm-4.7-flash</b>, ①(V6)은 <b>GLM-4.6</b> — 모델·에이전트 수가 달라 *직접 비교가 아니라 같은 방법론의 독립 적용*이다. "사다리"는 서사 장치일 뿐.</div>
</div>""")

    S.append(f"""<div class="s center">
<div class="snum">확장 · BCDE (glm-4.7-flash)</div>
<h2>문헌이 제안한 더 정교한 출력측 기제 셋</h2>
<div class="cards3">
<div class="card"><div class="ci">§6.1 · D</div><div class="ct">평판 망각</div><div class="cl">현행 평판이 카스트를<br>만드나? (Beta+λ)</div></div>
<div class="card"><div class="ci">§6.2 · D</div><div class="ct">Elder 판관</div><div class="cl">평판을 *누가* 매기나?<br>LLM 판관 (불변 원장)</div></div>
<div class="card"><div class="ci">§6.3 · C</div><div class="ct">진짜 QV</div><div class="cl">2차 비용+예산이<br>독점을 줄이나?</div></div>
</div>
<p class="lead center">모두 <b>같은 방법론</b>(공통 기준점·bootstrap·순열·Holm·원자료 0불일치). 질문은 매번 같다 — <b>이 정교함이 통제 검정을 통과하는가?</b></p>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">§6.1 평판 망각 · 왜 이 아이디어인가</div>
<h2>현행 평판은 <span class="red2">과거를 영원히 기억</span>한다</h2>
<div class="two">
<p class="lead">§8의 평판식 <code>rep=clip(1−overage/fair, .1, 1)</code>은 <b>누적 점유</b>만 본다. 한 번 과점해 점유가 높아지면, 이후 아무리 공정해져도 누적값이 끈질겨 <b>회복이 안 된다</b>.<br><br>
한번 "욕심쟁이"로 찍히면 영영 천민인 <b>카스트</b>처럼. → 평판이 <b>과거를 조금씩 잊게</b>(망각 λ) 만들면 회복이 살아날까?</p>
<div class="formula">Beta + λ 망각 (Jøsang &amp; Ismail 2002):
  r = Σ λ^Δ · [라운드 점유 ≤ fair]   # 착한 라운드
  s = Σ λ^Δ · [라운드 점유 &gt; fair]   # 과점 라운드
  E[rep] = (r+1)/(r+s+2)
  λ=1 영구 기억 · λ&lt;1 최근 가중(회복 가능)
신규 지표 recovery_rate = 저평판→복귀 속도(0=고착)</div>
</div>
</div>""")

    caste = bars([("none", 0.0, GRAY, "배제無"), ("linear", 0.0, RED, "현행=카스트"),
                  ("β λ1.0", 0.267, GOLDL, ""), ("β λ0.7", 0.356, GOLD, "")], vmax=0.4, w=600, h=290)
    S.append(f"""<div class="s">
<div class="snum">§6.1 평판 망각 · 결과 (N=30)</div>
<h2>망각이 회복을 살린다 — 단, 미세 λ는 무유의</h2>
<div class="two">
<div><div class="ctitle">recovery_rate (0=영영 못 돌아옴)</div>{caste}</div>
<ul class="big">
<li>현행 <b>선형(linear) 평판만 회복률 0</b> — 배제되면 영구 고착</li>
<li>망각 Beta는 회복>0 <span class="sig">l07 vs 선형 p_holm=.0007</span></li>
<li class="muted warn">단 핵심 인과 대조 <b>λ0.7 vs λ1.0은 무유의</b>(p_holm=.50) → "불변성=카스트"는 *방향성*이지 깔끔히 증명 아님</li>
<li class="muted">트레이드오프: 엄격 선형은 독점 최저(0.350)지만 회복 0</li>
</ul>
</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">§6.2 Elder 판관 · 왜 이 아이디어인가</div>
<h2>평판을 <span class="hl">누가</span> 매기나 — 행동 숫자 대신 LLM 심판?</h2>
<div class="two">
<p class="lead">§결과서 "평판 *피드백*"은 앵커링이었다. 그렇다면 평판을 <b>LLM 판관</b>이 직접 매기면 — 에이전트의 *근거 텍스트*를 읽고 공정성을 채점해 행동 평판과 섞으면 — 진짜 신호가 더해질까?<br><br>
이 원시는 세 갈래(고전 평판 · 불변 원장 · LLM-판관)의 교차점이고, 바로 그 조합이 <b>위험</b>도 상속한다.</p>
<div class="formula">Elder 혼합:
  rep = α·rule_rep + (1−α)·llm_judge
  rule_rep = Beta 행동 평판
  llm_judge = LLM이 근거를 0~1로 채점 (에피소드당 1회, 검소)
  불변(append-only) 원장에 기록 — 지울 수 없음
대조: ledger_numbers(숫자 앵커) / ledger_rule(α=1, 순수 행동)</div>
</div>
<div class="foot">위험 가설: 불변 원장이 *이른 오판*을 동결 → 갱생 불가(카스트). 선행: EigenTrust(또래), ERC-8004(온체인 평판)</div>
</div>""")

    elder = bars([("none", 0.475, GRAY, ""), ("numbers", 0.461, GOLDL, "앵커"),
                  ("rule α=1", 0.367, GREEN, "최선"), ("elder α=.5", 0.757, RED, "최악")], vmax=0.8, w=620, h=290)
    S.append(f"""<div class="s">
<div class="snum">§6.2 Elder 판관 · 결과 (N=20)</div>
<h2>판관은 신호가 아니라 <span class="red2">유의하게 역효과</span>였다</h2>
<div class="two">
<div><div class="ctitle">top-share (낮을수록 공정)</div>{elder}</div>
<ul class="big">
<li>LLM 판관(elder)이 rule·앵커와 <b>유의하게 다름</b> <span class="sig">모두 p_holm≤.0028</span> — 단 <b class="red">더 나쁜 쪽</b>(독점 0.757, 후생 0.33)</li>
<li><b>순수 행동 평판(rule)이 최선</b>(후생 0.95)</li>
<li class="muted">진단: 판관이 라운드0에 전원 가혹채점(0.2~0.3) → 불변 원장 동결 → 공정 에이전트(rule .60)도 배제</li>
<li class="muted warn">→ <b>정교함이 유의하게 *해*를 낼 수 있다</b>는 직접 증거 (방법론 교훈 강화). "말보다 행동"</li>
</ul>
</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">§6.3 진짜 QV · 왜 이 아이디어인가</div>
<h2>2차 비용 + 고정 예산 = <span class="hl">강도 진실</span></h2>
<div class="two">
<p class="lead">앞선 Phase A의 <code>1/(1+o²)</code> 곡선은 *예산이 없어* 진짜 QV가 아니었다(NO-GO). 진짜 QV(Weyl 2017)는 강도의 <b>2차 비용</b>을 <b>고정 예산</b>에 부과한다 — 한 군데 몰아 쓰면 값이 제곱으로 폭증해 <b>스스로 손해</b>.<br><br>
평판가중(÷rep)을 더하면 "QV+평판 결합본"(사용자 질문).</p>
<div class="formula">cost = d² / rep        # 평판가중(저평판 비쌈)
spent = Σ 과거 d²/rep   # 누적 2차 지출 (재계산)
cap = √((B − spent)·rep)  # 살 수 있는 최대
요청 > cap → 축약(MODIFY)
선행: Weyl 2017 · 고정예산 QV(2409.06614) · 평판가중 FedQV(2401.01168)</div>
</div>
<div class="foot">Sybil(신원 분할로 2차비용 1/k 깎기)·방어(신원-귀속 예산→이득 0)는 단위 회계로 검증(실 LLM arm 미수행)</div>
</div>""")

    qv = bars([("none", 0.475, GRAY, "독점"), ("qv_flat", 0.261, GOLD, ""),
               ("qv_rep", 0.276, GOLDL, "평판가중"),
               ("none", 0.78, GRAY, "후생"), ("qv_flat", 0.93, GREEN, "")], vmax=1.0, w=660, h=300)
    S.append(f"""<div class="s">
<div class="snum">§6.3 진짜 QV · 결과 (N=20, 4에이전트)</div>
<h2>점추정은 양면 개선 — 그러나 <span class="red2">Holm 미달</span></h2>
<div class="two">
<div>{qv}</div>
<ul class="big">
<li>독점·후생을 <b>동시에 점추정상</b> 개선 (독점 0.475→0.26, 후생 0.78→0.93)</li>
<li class="muted warn">단 <b>통제 검정 미통과</b>: 독점 Holm 간발(.054/.065), 후생 상승 미유의(p=.10) → <b>유망하나 미확정</b></li>
<li><b>평판가중(qv_rep)은 이득 0</b> — 검토: 첫 grab이 rep=1.0서 결정 + 이후 둘 다 floor 수렴 → 평판가중 발동 못함</li>
<li class="muted">비결은 사회적 정교함이 아니라 <b>고정 예산</b>이라는 구조 — 단 그조차 *확정* 아님</li>
</ul>
</div>
</div>""")

    S.append(f"""<div class="s center">
<div class="snum">종합</div>
<h2>정교함을 올려도 — <span class="hl">통과한 공정성 이득은 없었다</span></h2>
<div class="laddertab">
<div class="lr"><span class="ln">① 입력 프레이밍</span><span class="lv gray">= 앵커링 (사회적 성분 0)</span></div>
<div class="lr"><span class="ln">② 평판 망각</span><span class="lv gold">미세 λ 무유의 (선형↔Beta 경계만)</span></div>
<div class="lr"><span class="ln">③ LLM 판관</span><span class="lv red">유의하게 *역효과*</span></div>
<div class="lr"><span class="ln">④ 진짜 QV</span><span class="lv">점추정 개선이나 Holm 미달</span></div>
</div>
<div class="prescript"><b>이것이 *실패가 아니라 핵심 결과*다.</b> 견고·유의한 유일 결과는 *부정적*(현행 선형 평판=카스트 경향). "무엇이 통하나"가 아니라 <b>"겉보기 효과를 노이즈와 구별하는 통제 설계"가 산출물</b>.</div>
<div class="warn-box"><b>+ 새 위험.</b> <b>불변성</b>(누적 평판·불변 판관 원장)은 오류를 동결해 회복 불가 카스트를 만들 수 있다(소표본·단일모델, 제안 수준).</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 처방</div>
<h2>탐욕-거버넌스 효과를 검정하는 3원칙</h2>
<ol class="pres">
<li><b>하나의 공통 기준점.</b> 모든 조건을 한 실험·한 기준점에서 재라 — 조건별 기준점은 효과만큼 표류해 가짜 양성을 만든다.</li>
<li><b>앵커링·길이 대조군.</b> 규범·사회 표현을 벗긴 맨 정보 대조군을 넣어라 — 없으면 "사회적 기제"가 단순 지시-따르기·앵커링과 구별 안 된다.</li>
<li><b>원자료 위 정직한 통계.</b> 이산·소표본엔 순열/bootstrap + 다중성 보정 — 우리 "p&lt;.05" 효과 셋이 Holm 뒤 증발했다.</li>
</ol>
<div class="foot">문헌 함의: GovSim·ALIGN 계열 입력측 양성 결과는 *앵커링 귀무가설*에 대해 먼저 재검정되어야 한다</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">한계 (정직)</div>
<h2>주장하지 않는 것</h2>
<ul class="lim">
<li><b>모델·설정이 사다리 칸마다 다름.</b> V6=GLM-4.6, BCDE=glm-4.7-flash; 에이전트 V6/카스트/Elder=3, QV=4 — 칸 사이 *직접 비교가 아니라 동일 방법론의 독립 적용*.</li>
<li><b>귀무 ≠ 0.</b> N=20~30은 작은 효과를 못 잡는다. "유의하지 않음"은 "효과 0"이 아니다(단 앵커링 귀무 p=.88은 *사회적* 해석엔 양의 반대 증거).</li>
<li><b>QV는 Holm-간발, 카스트 핵심대조·QV welfare는 미유의.</b> 확정엔 더 큰 N. 사후 N 증량 안 함(goalpost 회피).</li>
<li><b>Elder=라운드-0 1회 채점 + 진단 1회 · Sybil=단위 회계만</b>(실 LLM arm 미수행).</li>
</ul>
</div>""")

    S.append(f"""<div class="s center closing">
<div class="snum">결론</div>
<h2>대부분의 거버넌스 효과는 <span class="hl">측정 착시</span>다</h2>
<p class="lead center">기여: 재사용 가능한 A2A 거버넌스 토대 · <b>앵커링-대조 방법론</b> · 통과/미통과 효과의 명확한 구분 · "정교함이 이득을 못 낸다"는 *부정적·방법론적* 결과. <b>이 연구의 산출물은 승자가 아니라 *통제 설계 그 자체*다.</b></p>
<div class="links">
<div class="lk"><span class="lkh">라이브 대시보드</span><span class="lkv">/ (A/B · Live · 정책 편집기)</span></div>
<div class="lk"><span class="lkh">논문 리포트</span><span class="lkv">/report (§1–9 + 차트)</span></div>
<div class="lk"><span class="lkh">BCDE 리포트</span><span class="lkv">/caste · /elder · /qv</span></div>
<div class="lk"><span class="lkh">원자료</span><span class="lkv">verify_*.json (0불일치 재계산)</span></div>
</div>
<div class="tmeta">전 실험 TDD · 통제 검정 · 원자료 독립 재계산 · 누적 실험비 ~$0.9</div>
</div>""")

    return S


CSS = """
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@500;600;700&display=swap');
:root{--ink:#1a1a17;--mut:#5d5a52;--line:#e9e4d8;--bg:#faf9f6;--card:#fff;--gold:#9c7c1f;--goldl:#c9a94a;--red:#b23b3b;--green:#2f7d4f;--blue:#2f5d9e;}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{height:100%;}
body{background:#33312c;color:var(--ink);font-family:'Pretendard',system-ui,sans-serif;-webkit-font-smoothing:antialiased;overflow:hidden;}
.deck{height:100vh;width:100vw;position:relative;}
.s{position:absolute;inset:0;display:none;flex-direction:column;justify-content:center;padding:52px 70px;background:var(--bg);opacity:0;transition:opacity .25s ease;}
.s.on{display:flex;opacity:1;}
.s.center{align-items:center;text-align:center;}
.snum{font-size:12.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--gold);margin-bottom:12px;}
h1{font-size:46px;font-weight:800;line-height:1.22;letter-spacing:-.02em;margin-bottom:22px;}
h2{font-size:31px;font-weight:800;line-height:1.28;letter-spacing:-.02em;margin-bottom:18px;}
.hl{color:var(--gold);}.red2{color:var(--red);}
.lead{font-size:17.5px;line-height:1.68;color:#2c2a24;max-width:780px;}
.lead.center{margin:16px auto 0;}
p.en{font-family:'Crimson Pro',serif;font-size:20px;font-style:italic;color:var(--mut);line-height:1.5;margin-top:6px;}
.ensub{font-size:15px;color:#8a8478;}
.kicker{font-family:'Crimson Pro',serif;font-size:15px;letter-spacing:.04em;color:var(--gold);margin-bottom:22px;}
.title{align-items:flex-start;}.title h1{margin-top:8px;}
.tmeta{margin-top:26px;font-size:13.5px;color:var(--mut);border-top:2px solid var(--line);padding-top:16px;}
.two{display:grid;grid-template-columns:1.02fr .98fr;gap:38px;align-items:center;}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:16px;}
.mini{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--gold);border-radius:10px;padding:13px 15px;font-size:13.5px;line-height:1.55;color:#2c2a24;}
.mini b{color:var(--ink);}
ul.big{list-style:none;display:flex;flex-direction:column;gap:13px;}
ul.big li{position:relative;padding-left:24px;font-size:16.5px;line-height:1.5;color:#2c2a24;}
ul.big li::before{content:'';position:absolute;left:0;top:9px;width:10px;height:10px;border-radius:2px;background:var(--gold);}
ul.big li.muted{color:var(--mut);font-size:14.5px;}ul.big li.muted::before{background:#cfc9bb;}
ul.big li.warn::before{background:var(--red);}
.num{font-family:'Crimson Pro',serif;font-weight:700;color:var(--ink);}
.sig{display:inline-block;font-size:12px;font-weight:700;color:#fff;background:var(--green);border-radius:5px;padding:1px 7px;margin-left:3px;vertical-align:middle;}
.tag{display:inline-block;font-size:12.5px;font-weight:700;color:#fff;border-radius:5px;padding:2px 8px;margin-right:6px;}
.tag.out{background:var(--red);}.tag.in{background:var(--blue);}
.badge{display:inline-block;font-size:11px;font-weight:700;color:#7a5f13;background:#fbf6e8;border:1px solid #e6d9b3;border-radius:4px;padding:0 5px;}
.persona{margin-top:16px;background:#1a1a17;border-radius:11px;padding:15px 18px;}
.persona .pl{font-size:12.5px;color:#c9a94a;font-weight:700;margin-bottom:8px;}
.persona code{display:block;color:#f3eede;font-size:14px;line-height:1.55;font-family:'Crimson Pro',serif;font-style:italic;background:none;}
.persona .pt{font-size:12.5px;color:#a8a296;margin-top:8px;}
.easy{margin-top:18px;background:#eef7f0;border:1px solid #cfe6d6;border-left:4px solid #2f9e57;border-radius:10px;padding:12px 17px;font-size:15px;line-height:1.58;color:#234a32;}
.easy b{color:#1c7a42;}.easy .lab{font-weight:800;color:#1c7a42;margin-right:6px;}
.easy.center{margin:18px auto 0;max-width:920px;text-align:left;}
.terms{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:22px;width:100%;max-width:1000px;}
.term{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;text-align:left;}
.term .ts{font-size:12px;color:var(--gold);font-weight:800;margin-bottom:7px;}
.term .th{font-family:'Crimson Pro',serif;font-size:24px;font-weight:700;color:var(--ink);margin-bottom:8px;}
.term .th .teng{font-size:14px;color:var(--mut);font-style:italic;}
.term p{font-size:14.5px;line-height:1.6;color:#2c2a24;}
.chart{width:100%;height:auto;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;}
.ctitle{font-size:12.5px;color:var(--mut);margin-bottom:7px;font-weight:600;}
.foot{margin-top:18px;border-top:1px solid var(--line);padding-top:11px;font-size:12.5px;color:var(--mut);}
.cards3{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:24px 0;width:100%;max-width:860px;}
.cards2{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:22px;width:100%;max-width:920px;}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px 18px;text-align:center;display:flex;flex-direction:column;justify-content:center;gap:7px;}
.card.gold{border:2px solid var(--gold);background:#fdfaf0;}
.cn{font-family:'Crimson Pro',serif;font-size:54px;font-weight:700;line-height:1;color:var(--ink);}
.card.gold .cn{color:var(--gold);}
.cl{font-size:13.5px;color:var(--mut);line-height:1.4;}
.ci{font-family:'Crimson Pro',serif;font-size:18px;color:var(--gold);font-weight:700;}
.ct{font-size:17px;font-weight:800;color:var(--ink);line-height:1.3;}
.bigcard{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;text-align:left;}
.bch{font-size:18px;font-weight:800;margin-bottom:10px;color:var(--ink);}
.bigcard p{font-size:14.5px;line-height:1.55;color:#2c2a24;margin:7px 0;}.bigcard .muted{color:var(--mut);font-size:13.5px;}
.eq{font-family:'Crimson Pro',serif;font-size:17px;background:#1a1a17;color:#f3eede;border-radius:8px;padding:9px 13px;margin:10px 0;}
.eq .gold{color:var(--goldl);}.eq .red{color:#e58a8a;}
.formula{background:#1a1a17;color:#e6edf3;border-radius:10px;padding:14px 16px;font-family:ui-monospace,Menlo,monospace;font-size:12.5px;line-height:1.65;white-space:pre-wrap;}
.dash{display:grid;grid-template-columns:1.15fr 1fr;gap:26px;align-items:center;}
.dash img{width:100%;border-radius:12px;border:1px solid var(--line);box-shadow:0 8px 26px rgba(40,36,28,.13);}
.dashfull{display:flex;justify-content:center;}
.dashfull img{max-width:84%;max-height:62vh;width:auto;border-radius:12px;border:1px solid var(--line);box-shadow:0 10px 32px rgba(40,36,28,.16);}
ul.dnote{list-style:none;}ul.dnote li{font-size:14px;line-height:1.5;color:#2c2a24;}
.refbox{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--blue);border-radius:10px;padding:12px 15px;margin-top:12px;font-size:13px;line-height:1.55;color:#2c2a24;}
.refbox .rh{font-weight:800;color:var(--ink);margin-bottom:5px;}
.refbox code{background:#f1efe9;border-radius:5px;padding:1px 5px;font-size:12.5px;color:#7a5f13;}
table{width:100%;border-collapse:collapse;margin:10px 0;font-size:13px;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;}
th,td{padding:8px 11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;}
th{background:#f4f3ef;font-weight:700;}tr:last-child td{border-bottom:0;}
td code{background:#f1efe9;border-radius:5px;padding:1px 5px;font-size:12px;color:#7a5f13;}
table.ex{font-size:13.5px;}table.ex td:last-child{font-weight:600;color:var(--ink);}
.mirror{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;}
.mrow{font-size:15px;line-height:1.55;color:#2c2a24;padding:7px 0;}
.ml{font-family:'Crimson Pro',serif;color:var(--gold);font-weight:700;margin-right:7px;}
.mx{text-align:center;font-size:12.5px;color:#a8a296;font-weight:700;margin:3px 0;}
.green{color:var(--green);}.red{color:var(--red);}.gold{color:var(--gold);}
.mc{margin-top:11px;padding-top:12px;border-top:1px solid var(--line);font-size:14px;line-height:1.55;color:#2c2a24;}
.disc{margin:20px auto 0;max-width:880px;background:#fbf2f2;border:1px solid #e6c9c9;border-left:4px solid var(--red);border-radius:10px;padding:13px 18px;font-size:14px;line-height:1.55;color:#5a2a2a;}
.disc b{color:var(--red);}
.prescript{margin:6px auto 0;max-width:880px;background:#1a1a17;color:#f3eede;border-radius:12px;padding:16px 22px;font-size:16px;line-height:1.55;}
.prescript b{color:var(--goldl);}
.warn-box{margin:14px auto 0;max-width:880px;background:#fbf2f2;border:1px solid #e6c9c9;border-left:4px solid var(--red);border-radius:10px;padding:12px 18px;font-size:14.5px;line-height:1.5;color:#5a2a2a;}
.warn-box b{color:var(--red);}
.laddertab{display:flex;flex-direction:column;gap:9px;margin:18px auto;max-width:760px;width:100%;}
.lr{display:flex;justify-content:space-between;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:9px;padding:11px 18px;}
.lr .ln{font-weight:800;color:var(--ink);font-size:15px;}
.lr .lv{font-size:14px;color:var(--mut);}.lr .lv.gray{color:#8a8478;}.lr .lv.gold{color:var(--gold);}.lr .lv.red{color:var(--red);font-weight:700;}
ol.pres{counter-reset:p;list-style:none;display:flex;flex-direction:column;gap:18px;margin-top:6px;max-width:1000px;}
ol.pres li{counter-increment:p;position:relative;padding-left:60px;font-size:17px;line-height:1.55;color:#2c2a24;min-height:42px;display:flex;align-items:center;}
ol.pres li::before{content:counter(p);position:absolute;left:0;top:0;width:42px;height:42px;border-radius:50%;background:var(--gold);color:#fff;font-family:'Crimson Pro',serif;font-size:22px;font-weight:700;display:flex;align-items:center;justify-content:center;}
ul.lim{list-style:none;display:flex;flex-direction:column;gap:15px;margin-top:4px;max-width:1000px;}
ul.lim li{position:relative;padding-left:24px;font-size:16px;line-height:1.55;color:#2c2a24;}
ul.lim li::before{content:'';position:absolute;left:0;top:9px;width:10px;height:10px;border-radius:2px;border:2px solid var(--mut);}
.closing h2{font-size:36px;}
.links{display:grid;grid-template-columns:repeat(2,1fr);gap:13px;margin:22px auto 0;max-width:720px;width:100%;}
.lk{display:flex;justify-content:space-between;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:11px 17px;}
.lkh{font-weight:700;font-size:14.5px;color:var(--ink);}.lkv{font-family:'Crimson Pro',serif;font-size:13.5px;color:var(--gold);}
.bar{position:absolute;top:0;left:0;height:4px;background:var(--gold);z-index:30;transition:width .25s;}
.pg{position:absolute;bottom:18px;right:28px;font-family:'Crimson Pro',serif;font-size:14px;color:#a8a296;z-index:30;}
.brand{position:absolute;bottom:18px;left:28px;font-size:12px;letter-spacing:.06em;color:#bdb7a8;z-index:30;text-transform:uppercase;}
.hint{position:absolute;bottom:16px;left:50%;transform:translateX(-50%);font-size:11.5px;color:#cfc9bb;z-index:30;}
@media (prefers-reduced-motion:reduce){.s,.bar{transition:none;}}
"""

JS = """
const slides=[...document.querySelectorAll('.s')];let i=0;
const bar=document.querySelector('.bar'),pg=document.querySelector('.pg');
function show(n){i=Math.max(0,Math.min(slides.length-1,n));
 slides.forEach((s,k)=>s.classList.toggle('on',k===i));
 bar.style.width=((i+1)/slides.length*100)+'%';pg.textContent=(i+1)+' / '+slides.length;location.hash=i+1;}
function next(){show(i+1);}function prev(){show(i-1);}
document.addEventListener('keydown',e=>{
 if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();next();}
 else if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();prev();}
 else if(e.key==='Home'){show(0);}else if(e.key==='End'){show(slides.length-1);}});
document.querySelector('.deck').addEventListener('click',e=>{if(e.target.closest('a'))return;(e.clientX/window.innerWidth>0.5?next:prev)();});
const st=parseInt(location.hash.slice(1))-1;show(isNaN(st)?0:st);
"""


def main():
    body = "".join(slides())
    page = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Antigreedy — 탐욕 거버넌스 통제 실험 (발표자료 v2)</title>
<style>{CSS}</style></head><body>
<div class="bar"></div><div class="deck">{body}</div>
<div class="pg"></div><div class="brand">Antigreedy · A2A Governance</div><div class="hint">← → 또는 클릭으로 이동</div>
<script>{JS}</script></body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(page):,} bytes, {len(slides())} slides)")


if __name__ == "__main__":
    main()
