#!/usr/bin/env python3
"""발표자료(HTML 슬라이드) 빌더 → docs/slides.html.

ui-ux-pro-max 디자인 시스템 적용: minimal 흑+골드 액센트, academic serif(Crimson Pro) 디스플레이 +
Pretendard 본문, 데이터-덴스. 대시보드 구조·이미지 + 결과 차트(inline SVG) + 핵심 내용 전부 포함.
대시보드 PNG는 base64로 인라인해 단일 파일로 자족(self-contained).

    .venv/bin/python scripts/build_slides.py  →  docs/slides.html
"""
from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"
OUT = ROOT / "docs" / "slides.html"

INK = "#1a1a17"
MUT = "#5d5a52"
GOLD = "#9c7c1f"
GOLDL = "#c9a94a"
RED = "#b23b3b"
GRAY = "#9a958a"
GREEN = "#2f7d4f"
BLUE = "#2f5d9e"


def img_b64(name: str) -> str:
    fp = ASSETS / name
    if not fp.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(fp.read_bytes()).decode()


def bars(items, *, vmax=1.0, unit="", h=260, w=620, caption=""):
    """items = [(label, value, color, sublabel)]. 가로 기준선 + 세로 막대."""
    pl, pr, pt, pb = 8, 8, 26, 52
    pw, ph = w - pl - pr, h - pt - pb
    n = len(items)
    slot = pw / n
    bw = slot * 0.46
    scale = vmax

    def y(v):
        return pt + ph * (1 - v / scale)

    s = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="{caption}">']
    for g in (0, 0.25, 0.5, 0.75, 1.0):
        gv = g * scale
        s.append(f'<line x1="{pl}" y1="{y(gv):.1f}" x2="{w-pr}" y2="{y(gv):.1f}" stroke="#ece8df"/>')
        s.append(f'<text x="{pl}" y="{y(gv)-3:.1f}" fill="#a8a296" font-size="10">{gv:.2f}{unit}</text>')
    for i, (lab, v, col, sub) in enumerate(items):
        cx = pl + slot * i + slot / 2
        x = cx - bw / 2
        s.append(f'<rect x="{x:.1f}" y="{y(v):.1f}" width="{bw:.1f}" height="{y(0)-y(v):.1f}" rx="2" fill="{col}"/>')
        s.append(f'<text x="{cx:.1f}" y="{y(v)-7:.1f}" text-anchor="middle" fill="{INK}" font-size="13" font-weight="700" font-family="Crimson Pro,serif">{v:.3f}</text>')
        s.append(f'<text x="{cx:.1f}" y="{h-30:.1f}" text-anchor="middle" fill="#3a382f" font-size="12" font-weight="600">{lab}</text>')
        if sub:
            s.append(f'<text x="{cx:.1f}" y="{h-14:.1f}" text-anchor="middle" fill="#8a8478" font-size="10.5">{sub}</text>')
    s.append("</svg>")
    return "".join(s)


def substrate_svg():
    """거버넌스 토대 아키텍처 다이어그램."""
    return """<svg viewBox="0 0 920 360" class="chart" role="img" aria-label="거버넌스 토대 아키텍처">
<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
<path d="M0,0 L7,3 L0,6 Z" fill="#9c7c1f"/></marker></defs>
<rect x="20" y="40" width="190" height="90" rx="12" fill="#f3eede" stroke="#9c7c1f"/>
<text x="115" y="66" text-anchor="middle" fill="#7a5f13" font-size="14" font-weight="700">입력측 셰이퍼</text>
<text x="115" y="88" text-anchor="middle" fill="#5d5a52" font-size="11.5">PromptShaper</text>
<text x="115" y="106" text-anchor="middle" fill="#8a8478" font-size="10.5">프롬프트 재구성(설득)</text>
<text x="115" y="121" text-anchor="middle" fill="#8a8478" font-size="10.5">read-only</text>
<rect x="290" y="50" width="150" height="70" rx="12" fill="#ffffff" stroke="#cfc9bb"/>
<text x="365" y="80" text-anchor="middle" fill="#1a1a17" font-size="14" font-weight="700">LLM 에이전트</text>
<text x="365" y="100" text-anchor="middle" fill="#8a8478" font-size="11">행동(요청) 생성</text>
<line x1="210" y1="85" x2="288" y2="85" stroke="#9c7c1f" stroke-width="2" marker-end="url(#ar)"/>
<rect x="290" y="170" width="150" height="120" rx="12" fill="#1a1a17"/>
<text x="365" y="200" text-anchor="middle" fill="#fff" font-size="13.5" font-weight="700">InterceptPoint</text>
<text x="365" y="222" text-anchor="middle" fill="#c9a94a" font-size="11">PolicyChain</text>
<text x="365" y="244" text-anchor="middle" fill="#cfc9bb" font-size="10.5">ALLOW · DENY</text>
<text x="365" y="260" text-anchor="middle" fill="#cfc9bb" font-size="10.5">MODIFY · DELAY</text>
<text x="365" y="278" text-anchor="middle" fill="#8a8478" font-size="9.5">우선순위·short-circuit</text>
<line x1="365" y1="120" x2="365" y2="168" stroke="#9c7c1f" stroke-width="2" marker-end="url(#ar)"/>
<rect x="510" y="170" width="190" height="120" rx="12" fill="#f3eede" stroke="#9c7c1f"/>
<text x="605" y="200" text-anchor="middle" fill="#7a5f13" font-size="14" font-weight="700">출력측 정책</text>
<text x="605" y="222" text-anchor="middle" fill="#5d5a52" font-size="11.5">Policy (cap·평판·배제)</text>
<text x="605" y="244" text-anchor="middle" fill="#8a8478" font-size="10.5">전달 행동 가로채기</text>
<text x="605" y="262" text-anchor="middle" fill="#8a8478" font-size="10.5">read-only</text>
<line x1="440" y1="230" x2="508" y2="230" stroke="#9c7c1f" stroke-width="2" marker-end="url(#ar)"/>
<rect x="760" y="60" width="140" height="230" rx="12" fill="#ffffff" stroke="#2f5d9e" stroke-dasharray="5 4"/>
<text x="830" y="92" text-anchor="middle" fill="#2f5d9e" font-size="13.5" font-weight="700">SharedState</text>
<text x="830" y="120" text-anchor="middle" fill="#5d5a52" font-size="10.5">자원 예산</text>
<text x="830" y="142" text-anchor="middle" fill="#5d5a52" font-size="10.5">시도/전달 집계</text>
<text x="830" y="164" text-anchor="middle" fill="#5d5a52" font-size="10.5">턴 로그</text>
<text x="830" y="186" text-anchor="middle" fill="#5d5a52" font-size="10.5">파생 평판</text>
<text x="830" y="222" text-anchor="middle" fill="#8a8478" font-size="9.5">단일 기록자</text>
<text x="830" y="238" text-anchor="middle" fill="#8a8478" font-size="9.5">(오케스트레이터만 변경)</text>
<line x1="700" y1="200" x2="758" y2="200" stroke="#2f5d9e" stroke-width="1.5" stroke-dasharray="4 3"/>
<line x1="210" y1="100" x2="758" y2="140" stroke="#2f5d9e" stroke-width="1.2" stroke-dasharray="3 3" opacity="0.5"/>
</svg>"""


def design_diagram_svg():
    """통제 설계 — 공통 기준점 + 대조군 분해."""
    return """<svg viewBox="0 0 900 250" class="chart" role="img" aria-label="통제 설계">
<rect x="20" y="30" width="860" height="46" rx="10" fill="#1a1a17"/>
<text x="450" y="58" text-anchor="middle" fill="#fff" font-size="14" font-weight="700">하나의 공통 기준점 · 하나의 실험 (N=30) — 7개 조건 동시 측정</text>
<g font-size="11.5">
<rect x="20" y="100" width="150" height="56" rx="9" fill="#f3eede" stroke="#9c7c1f"/>
<text x="95" y="125" text-anchor="middle" fill="#7a5f13" font-weight="700">reputation_feedback</text>
<text x="95" y="143" text-anchor="middle" fill="#8a8478">평판·또래·규범 + 숫자</text>
<rect x="200" y="100" width="150" height="56" rx="9" fill="#fbf6e8" stroke="#c9a94a"/>
<text x="275" y="125" text-anchor="middle" fill="#7a5f13" font-weight="700">fairshare_anchor</text>
<text x="275" y="143" text-anchor="middle" fill="#8a8478">숫자 앵커만</text>
<rect x="380" y="100" width="150" height="56" rx="9" fill="#f4f3ef" stroke="#cfc9bb"/>
<text x="455" y="125" text-anchor="middle" fill="#5d5a52" font-weight="700">neutral_filler</text>
<text x="455" y="143" text-anchor="middle" fill="#8a8478">동일 길이·무내용</text>
<rect x="560" y="100" width="150" height="56" rx="9" fill="#f4f3ef" stroke="#cfc9bb"/>
<text x="635" y="125" text-anchor="middle" fill="#5d5a52" font-weight="700">none</text>
<text x="635" y="143" text-anchor="middle" fill="#8a8478">무규제 기준점</text>
</g>
<g font-size="11" fill="#b23b3b" font-weight="700">
<text x="185" y="186" text-anchor="middle">− 사회적 성분</text>
<text x="365" y="186" text-anchor="middle">− 숫자 앵커</text>
<text x="545" y="186" text-anchor="middle">− 프롬프트 길이</text>
</g>
<line x1="95" y1="160" x2="275" y2="160" stroke="#b23b3b" stroke-width="1.3"/>
<line x1="275" y1="166" x2="455" y2="166" stroke="#b23b3b" stroke-width="1.3"/>
<line x1="455" y1="172" x2="635" y2="172" stroke="#b23b3b" stroke-width="1.3"/>
<text x="450" y="222" text-anchor="middle" fill="#5d5a52" font-size="12">각 대조군 차이가 입력 효과를 (사회적)+(앵커)+(길이) 세 성분으로 *분해*한다</text>
</svg>"""


def slides():
    S = []

    S.append(f"""<div class="s title">
<div class="kicker">A2A · 다중 에이전트 거버넌스 · 통제 실험</div>
<h1>LLM 에이전트의 탐욕 거버넌스 효과<br>대부분은 <span class="hl">측정 아티팩트</span>다</h1>
<p class="en">Most Greed-Governance Effects on LLM Agents Are Measurement Artifacts<br>
<span class="ensub">A Controlled Test of Output Capping vs. Input Framing</span></p>
<div class="tmeta">통제·앵커대조·다중보정 실험 + 거버넌스 메커니즘 확장(BCDE) · GLM-4.6 / glm-4.7-flash · 원자료 공개</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">문제</div>
<h2>여러 LLM이 자원을 다투면 <span class="hl">공유지의 비극</span>이 되살아난다</h2>
<div class="two">
<div>
<p class="lead">자율 LLM 에이전트는 A2A 프로토콜로 연결되어 공유 자원을 나눠 쓴다. 그 순간 <b>행동적 탐욕</b>이 창발한다 — 공유 자원을 선점해 남을 굶기는 이기적 착취.</p>
<div class="analogy"><b>사무실 프린터 비유.</b> 한 사람이 1,000장짜리 작업을 계속 걸어두면 나머지는 한 장도 못 뽑는다. 이걸 막는 손잡이가 둘 있다.</div>
</div>
<ul class="big">
<li><span class="tag out">출력측</span> 나온 행동을 <b>깎는다</b> — cap·요청 제한·평판·배제</li>
<li><span class="tag in">입력측</span> 행동 전에 프롬프트로 <b>타이른다</b> — 정체성·책임감·평판 피드백</li>
</ul>
</div>
<div class="foot">Hammond et al. 2025 · Piatti et al. (GovSim) 2024 · Vallinder &amp; Hughes 2025</div>
</div>""")

    S.append(f"""<div class="s center">
<div class="snum">시작 전에 · 딱 세 단어</div>
<h2>이 세 단어만 알면 끝까지 이해됩니다</h2>
<div class="terms">
<div class="term"><div class="ts">낮을수록 좋음</div><div class="th">독점</div><p>한 에이전트가 자원을 얼마나 <b>싹쓸이</b>했나. 높으면 한 명이 다 가져간 것 → 나쁨. <i>(top-share)</i></p></div>
<div class="term"><div class="ts">높을수록 좋음</div><div class="th">후생</div><p>결국 <b>몇 명이나 자기 일을 끝냈나</b>(완료율). 다 같이 성공할수록 높음 → 좋음. <i>(welfare)</i></p></div>
<div class="term"><div class="ts">이 발표의 뼈대</div><div class="th">통제 실험</div><p>약 효과를 <b>가짜약과 비교</b>하듯, 거버넌스도 "아무것도 안 함·말만 그럴싸함"과 나란히 재야 진짜인지 안다.</p></div>
</div>
<div class="easy center"><span class="lab">💡</span> 즉 이 발표는 "<b>한 명의 독식을 줄이고(독점↓) 모두가 일을 끝내게(후생↑)</b> 하는 방법"을 찾되, 그중 <b>진짜 효과만 골라내는</b> 이야기입니다.</div>
</div>""")

    S.append(f"""<div class="s center">
<div class="snum">핵심 질문</div>
<h2>"어느 쪽이 나은가"보다 먼저 —<br><span class="hl">진짜 효과를 설계가 만든 착시와 구별</span>해야 한다</h2>
<div class="cards3">
<div class="card"><div class="cn">9</div><div class="cl">미리 정한 비교</div></div>
<div class="card gold"><div class="cn">2</div><div class="cl">통제 검정 통과</div></div>
<div class="card"><div class="cn">7</div><div class="cl">측정 아티팩트</div></div>
</div>
<p class="lead center">이 발표의 기여는 <b>방법론적·부정적</b>이다: 통제·앵커대조·다중보정 설계만이 진짜 기제를 노이즈와 구별하며, 보고된 효과 대부분은 그 검정을 통과하지 못한다.</p>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 · 토대</div>
<h2>재사용 가능한 A2A 거버넌스 토대</h2>
<p class="lead">모든 행동은 전달 전 하나의 관문을 통과한다. 두 레버가 <b>같은 상태</b> 위에서 돌고, 정책·셰이퍼는 상태를 <b>읽기 전용</b>으로만 본다.</p>
{substrate_svg()}
<div class="foot">출력측 = nullcap.py + social_reputation 프리셋 · 입력측 = prompt_shapers.py · 단일 기록자 규칙</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 · 대시보드</div>
<h2>라이브 A/B 시연 대시보드 — 같은 에이전트, <span class="hl">오직 정책만 다름</span></h2>
<div class="dash">
<img src="{img_b64('dash_idle.png')}" alt="Antigreedy A/B 시연 대시보드 구조 — 좌측 baseline 패널, 우측 governed 패널, 상단 정책·시나리오·예산 컨트롤"/>
<ul class="dnote">
<li><b>좌(baseline) vs 우(governed)</b> 두 패널을 <b>동시</b>에 스트리밍 — 노드 크기 = 점유, 게이지 = 커먼즈</li>
<li><b>거버넌스 토글</b> · 정책 프리셋 · <b>라이브 정책 편집기</b> · 에이전트 수 · 예산</li>
<li><b>대화 보기</b>(프롬프트→출력→전달 diff) · <b>기만 탐지</b> 🚩 · 공정성(Jain) 메트릭</li>
<li>같은 거버넌스 메트릭이 <b>화면·논문에서 동일</b>(metrics = 로그의 순수함수)</li>
</ul>
</div>
<div class="foot">FastAPI + WebSocket · MockBackend(무료) / OpenRouter 실 LLM(opt-in) · 헤더에서 논문·BCDE 리포트 연동</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 · 대시보드</div>
<h2>거버넌스 OFF면 둘 다 고갈, ON이면 governed가 <span class="hl">생존</span></h2>
<div class="dashfull">
<img src="{img_b64('dash_running.png')}" alt="A/B 시연 실행 — baseline 패널은 한 노드가 비대하게 독점하고 governed 패널은 고르게 분배"/>
</div>
<div class="foot">▶ Run A/B 한 번으로 통제 대비를 시각화 — 발표 현장에서 실시간 재현 가능</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 · 설계</div>
<h2>통제된 검정 — 공통 기준점 + 앵커/길이 대조군 + 정직한 통계</h2>
{design_diagram_svg()}
<div class="three">
<div class="mini"><b>공통 기준점</b><br>7개 조건을 하나의 실험·N=30에서 동시 측정 (조건별 기준점은 효과만큼 표류)</div>
<div class="mini"><b>대조군 분해</b><br>앵커·길이 대조군으로 입력 효과를 사회적/숫자/길이 성분으로 분리</div>
<div class="mini"><b>원자료 통계</b><br>bootstrap CI · 순열검정(정규근사 X) · 9비교 Holm 보정</div>
</div>
</div>""")

    v6 = bars([("none", 0.651, GRAY, "독점"), ("superord.", 0.412, GOLD, "p_holm&lt;.001"),
               ("none", 0.66, GRAY, "후생"), ("social", 0.39, RED, "p_holm=.022")],
              vmax=0.8, caption="V6 생존 효과", w=640, h=300)
    S.append(f"""<div class="s">
<div class="snum">결과 · V6 (GLM-4.6, N=30)</div>
<h2>9개 중 단 2개만 살아남았다</h2>
<div class="two">
<div>{v6}</div>
<ul class="big">
<li><b>상위 정체성</b>이 독점을 줄임 <span class="num">0.65→0.41</span> <span class="sig">p_holm&lt;.001</span></li>
<li>출력 <b>"사회" 정책</b>이 후생을 <b>해침</b> <span class="num">0.66→0.39</span> <span class="sig">p_holm=.022</span></li>
<li class="muted">나머지 7개 — 평판 피드백·길이·앵커 — 전부 보정에서 증발</li>
</ul>
</div>
<div class="easy"><span class="lab">💡 쉽게:</span> 공들여 만든 방법 <b>9개 중 통계를 통과한 건 단 2개</b>. 나머지는 진짜 효과가 아니라 <b>실험 설계가 만든 착시</b>였다.</div>
<div class="foot">superordinate는 앵커 대조군 미보유 → 견고하나 정체성/지시로 미분해</div>
</div>""")

    S.append(f"""<div class="s center">
<div class="snum">결과 · 아티팩트의 정체</div>
<h2>평판 피드백 = <span class="hl">앵커링</span> &nbsp;·&nbsp; 내용 없는 배너가 후생 1등</h2>
<div class="cards2">
<div class="bigcard">
<div class="bch">평판 되먹임 ≈ 숫자 앵커</div>
<p>평판·또래·규범 표현을 <b>모두 벗기고</b> 숫자 공정-몫 문장만 남겨도 결과가 같다.</p>
<div class="eq">welfare rep vs anchor &nbsp;<b class="gold">p = .88</b> &nbsp;(ns)</div>
<p class="muted">→ 사회적 기제가 아니라 앵커링. 조건별 기준점이 이 앵커를 "사회적 효과"로 오인하게 만든다.</p>
</div>
<div class="bigcard">
<div class="bch">neutral_filler 후생 최고 0.82</div>
<p>자원·공정성 얘기가 <b>하나도 없는</b> 배너가 정성껏 설계한 모든 셰이퍼를 이겼다.</p>
<div class="eq">"입력은 <i>사회적이라</i> 통한다"의 <b class="red">반증</b></div>
<p class="muted">→ 입력 배너의 후생 차이는 사회적 기제 설계 덕이 아니다.</p>
</div>
</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">결과 · 위약-군집 대조</div>
<h2>정체성 프레이밍의 <span class="hl">해악은 군집 내용과 무관</span>하다</h2>
<div class="two">
<p class="lead">관측 행동에서 정체성을 <b>창발</b>시키면(emergent_identity)? 오히려 <b>역효과</b> — "탐욕 부류"로 명시하니 자기범주화로 더 독식(카스트화).<br><br>
멤버십만 무작위로 섞은 <b>위약(placebo)</b> 군집과 비교: <b>emergent ≈ placebo</b> <span class="sig">p_holm=1.0</span> (n=3·6).<br><br>
해악은 군집의 <i>내용</i>이 아니라 <b>분열적 "관측된 그룹" 배너를 주입하는 행위 자체</b>에서 온다 — 진실이든 날조든.</p>
<div class="mirror">
<div class="mrow"><span class="ml">§5.4</span> <b>중립</b> 배너의 <b class="green">이득</b> = 사회 설계와 무관</div>
<div class="mx">거울상</div>
<div class="mrow"><span class="ml">§5.6</span> <b>분열</b> 배너의 <b class="red">해악</b> = 군집 내용과 무관</div>
<div class="mc">→ 입력 효과는 설계된 기제가 아니라 <b>프레임의 성격(중립↔분열)</b>이라는 거친 축을 따른다</div>
</div>
</div>
</div>""")

    S.append(f"""<div class="s center">
<div class="snum">확장 · BCDE (glm-4.7-flash)</div>
<h2>더 <span class="hl">정교한</span> 기제 셋을 같은 통제 검정에 걸다</h2>
<div class="cards3">
<div class="card"><div class="ci">§6.1</div><div class="ct">평판 망각</div><div class="cl">Beta + λ<br>카스트화 검정</div></div>
<div class="card"><div class="ci">§6.2</div><div class="ct">Elder 판관</div><div class="cl">LLM 판관 원장<br>신호 vs 앵커</div></div>
<div class="card"><div class="ci">§6.3</div><div class="ct">진짜 QV</div><div class="cl">2차 비용+예산<br>독점 억제</div></div>
</div>
<p class="lead center">동일 방법론(공통 기준점·bootstrap·순열·Holm·원자료 0불일치). 결론은 하나로 수렴 — <b>단순한 기반이 정교한 신호를 이긴다.</b></p>
</div>""")

    caste = bars([("none", 0.0, GRAY, "배제無"), ("linear", 0.0, RED, "현행=카스트"),
                  ("β λ1.0", 0.267, GOLDL, ""), ("β λ0.9", 0.316, GOLDL, ""),
                  ("β λ0.7", 0.356, GOLD, "p_holm=.0007")],
                 vmax=0.4, caption="회복률", w=640, h=290)
    S.append(f"""<div class="s">
<div class="snum">§6.1 평판 망각 (N=30)</div>
<h2>현행 누적 평판은 <span class="red2">영구 카스트</span>를 만든다</h2>
<div class="two">
<div><div class="ctitle">recovery_rate — 저평판에서 복귀하는 속도 (0=고착)</div>{caste}</div>
<ul class="big">
<li>배제하는 평판 중 <b>현행 선형(linear)만 회복률 0</b> — 한 번 찍히면 영원히 배제</li>
<li><b>망각 λ&lt;1</b>이 회복을 되살림 <span class="sig">λ0.7 vs 선형 p_holm=.0007</span></li>
<li class="muted">미세 λ-기울기(0.7 vs 1.0)는 N=30서 무유의 — 진짜 절벽은 <b>선형↔Beta</b> 경계</li>
<li class="muted">공정성의 극단 ↔ 회복가능성은 같은 축의 양 끝</li>
</ul>
</div>
<div class="easy"><span class="lab">💡 쉽게:</span> 지금 평판은 한 번 "욕심쟁이"로 찍히면 <b>영영 복귀 못 함</b>(카스트). 평판이 <b>과거를 조금씩 잊게</b> 만들면 복귀가 살아난다 — "용서의 여지".</div>
</div>""")

    elder_top = bars([("none", 0.475, GRAY, ""), ("numbers", 0.461, GOLDL, "앵커"),
                      ("rule α=1", 0.367, GREEN, "최선"), ("elder α=.5", 0.757, RED, "최악")],
                     vmax=0.8, caption="Elder 독점", w=620, h=290)
    S.append(f"""<div class="s">
<div class="snum">§6.2 Elder LLM-판관 (N=20)</div>
<h2>판관은 신호가 아니라 <span class="red2">동결된 노이즈</span>였다</h2>
<div class="two">
<div><div class="ctitle">top-share(독점) — 낮을수록 공정</div>{elder_top}</div>
<ul class="big">
<li>LLM 판관 혼합(elder)이 rule·앵커와 <b>유의하게 다름</b> <span class="sig">모두 p_holm≤.0028</span> — 단 <b class="red">더 나쁜 쪽</b></li>
<li><b>순수 행동 평판(rule, α=1)이 최선</b> (후생 0.95 vs elder 0.33)</li>
<li class="muted">진단: 판관이 라운드0에 전원 가혹채점(0.2~0.3) → <b>불변 원장이 동결</b> → 공정 에이전트(rule .60)도 배제</li>
<li class="muted">단 라운드-0 1회 채점이라는 최악 타이밍의 결과 — "이른·불변 판단의 위험"</li>
</ul>
</div>
<div class="easy"><span class="lab">💡 쉽게:</span> AI 심판은 <b>첫인상</b>만 보고 모두에게 박한 점수를 줬고, 그게 <b>영구 기록</b>으로 남아 나중에 착해진 참가자까지 쫓아냈다. <b>"말"보다 "행동"</b>을 봐야 한다.</div>
<div class="foot">§6.1 카스트의 자매 결과 — 거기선 행동 누적, 여기선 LLM 판단 오류가 불변성에 동결 · "말보다 행동"</div>
</div>""")

    qv = bars([("none", 0.475, GRAY, "독점"), ("qv_flat", 0.261, GOLD, "−45%"),
               ("qv_rep", 0.276, GOLDL, "이득無"),
               ("none", 0.78, GRAY, "후생"), ("qv_flat", 0.93, GREEN, "")],
              vmax=1.0, caption="QV", w=660, h=300)
    S.append(f"""<div class="s">
<div class="snum">§6.3 진짜 QV (N=20, 4에이전트)</div>
<h2>2차 비용 + 고정 예산 — 프로그램의 첫 <span class="hl">양면 개선 방향</span></h2>
<div class="two">
<div>{qv}</div>
<ul class="big">
<li>독점·후생을 <b>동시에 점추정상</b> 개선한 유일한 방향 (독점 0.475→0.26, 후생 0.78→0.93)</li>
<li class="muted warn">단 통제 검정 미통과: 독점은 Holm <b>간발 미달</b>(.054/.065), 후생 상승은 미유의(p=.10) → <b>유망하나 미확정</b></li>
<li><b>평판가중(qv_rep)은 이득 0</b> — 예산이 먼저 binding ("단순한 게 낫다")</li>
<li class="muted">비결은 사회적 정교함이 아니라 <b>고정 예산</b>이라는 구조 제약 · Sybil 취약점/방어는 단위 회계로 검증</li>
</ul>
</div>
<div class="easy"><span class="lab">💡 쉽게:</span> <b>"몰아 쓰면 손해 보는 예산제"</b>를 넣으니 독식이 절반으로 줄고 모두 더 잘 끝냈다 — 둘 다 좋아진 유일한 방법(단 통계적으론 아슬아슬, 더 큰 실험 필요).</div>
</div>""")

    S.append(f"""<div class="s center">
<div class="snum">종합</div>
<h2>단순한 기반이 <span class="hl">정교한 신호를 이긴다</span></h2>
<div class="cards3 tall">
<div class="card"><div class="ct">평판 피드백 = 앵커</div><div class="cl">§5.3</div></div>
<div class="card"><div class="ct">미세 λ · LLM 판관 · 평판가중<br>= 단순 기반에 이득 0/해악</div><div class="cl">§6.1·6.2·6.3</div></div>
<div class="card gold"><div class="ct">유일한 성공 = 고정 예산</div><div class="cl">구조 제약(진짜 QV)</div></div>
</div>
<div class="prescript"><b>처방.</b> 정교한 사회적/판단적 장치를 덧대기 전에, 그것이 단순 기반(행동 평판·고정 예산)을 <b>유의하게 이기는지부터</b> 통제 검정하라.</div>
<div class="warn-box"><b>새 위험.</b> <b>불변성</b>(누적 평판이든 불변 판관 원장이든)은 오류를 동결해 회복 불가능한 <b>카스트</b>를 만든다.</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">방법론 처방</div>
<h2>탐욕-거버넌스 효과를 검정하는 3원칙</h2>
<ol class="pres">
<li><b>하나의 공통 기준점.</b> 모든 조건을 한 실험·한 기준점에서 재라 — 조건별 기준점은 N≤30에서 효과만큼 표류해 가짜 양성을 만든다.</li>
<li><b>앵커링·길이 대조군.</b> 프롬프트 개입엔 규범·사회 표현을 벗긴 맨 정보 대조군을 넣어라 — 없으면 "사회적 기제"가 단순 지시-따르기와 구별 안 된다.</li>
<li><b>원자료 위 정직한 통계.</b> 이산·소표본엔 정규근사 말고 순열/bootstrap + 다중성 보정 — 우리 "p&lt;.05" 효과 셋이 Holm 뒤 증발했다.</li>
</ol>
<div class="foot">문헌 함의: GovSim·ALIGN 계열 입력측 결과는 앵커링 귀무가설에 대해 먼저 재검정되어야 한다</div>
</div>""")

    S.append(f"""<div class="s">
<div class="snum">한계 (정직)</div>
<h2>주장하지 않는 것</h2>
<ul class="lim">
<li><b>단일 모델·시나리오.</b> §5 = GLM-4.6, §6 = glm-4.7-flash. 모델 일반성 미주장 — §6의 §5 일치는 직접 비교가 아니라 동일 방법론의 독립 적용.</li>
<li><b>귀무 ≠ 0.</b> N=20~30은 작은 효과를 못 잡는다. "유의하지 않음"은 "효과 0"이 아니다(단 앵커링 귀무 p=.88은 사회적 해석엔 양의 반대 증거).</li>
<li><b>진짜 QV는 Holm-간발.</b> 독점 감소 .054/.065 — 확정엔 더 큰 N. 사후 N 증량 안 함(goalpost 회피).</li>
<li><b>Elder는 라운드-0 1회 채점 + 진단 1회.</b> 판관 최악 타이밍 · Sybil은 단위 회계만(실 LLM arm 미수행).</li>
</ul>
</div>""")

    S.append(f"""<div class="s center closing">
<div class="snum">결론</div>
<h2>대부분의 거버넌스 효과는 <span class="hl">측정 착시</span>다</h2>
<p class="lead center">기여: 재사용 가능한 A2A 거버넌스 토대 · 앵커링-대조 방법론 · 통과/미통과 효과의 명확한 구분 · 메커니즘 확장의 "단순 기반 우선" 처방.</p>
<div class="links">
<div class="lk"><span class="lkh">라이브 대시보드</span><span class="lkv">/ (A/B · Live · 정책 편집기)</span></div>
<div class="lk"><span class="lkh">논문 리포트</span><span class="lkv">/report (§1–9 + 차트)</span></div>
<div class="lk"><span class="lkh">BCDE 리포트</span><span class="lkv">/caste · /elder · /qv</span></div>
<div class="lk"><span class="lkh">원자료</span><span class="lkv">verify_*.json (0불일치 재계산)</span></div>
</div>
<div class="tmeta">전 실험 TDD · 통제 검정 · 원자료 독립 재계산 · Pretendard 리포트 · 누적 실험비 ~$0.9</div>
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
.s{position:absolute;inset:0;display:none;flex-direction:column;justify-content:center;
  padding:64px 80px;background:var(--bg);opacity:0;transition:opacity .25s ease;}
.s.on{display:flex;opacity:1;}
.s.center{align-items:center;text-align:center;}
.snum{font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--gold);margin-bottom:14px;}
h1{font-size:50px;font-weight:800;line-height:1.22;letter-spacing:-.02em;margin-bottom:24px;}
h2{font-size:34px;font-weight:800;line-height:1.28;letter-spacing:-.02em;margin-bottom:22px;}
.hl{color:var(--gold);}
.red2{color:var(--red);}
.lead{font-size:19px;line-height:1.72;color:#2c2a24;max-width:760px;}
.lead.center{margin:18px auto 0;}
p.en{font-family:'Crimson Pro',serif;font-size:21px;font-style:italic;color:var(--mut);line-height:1.5;margin-top:6px;}
.ensub{font-size:16px;color:#8a8478;}
.kicker{font-family:'Crimson Pro',serif;font-size:16px;letter-spacing:.04em;color:var(--gold);margin-bottom:26px;}
.title{align-items:flex-start;}
.title h1{margin-top:8px;}
.tmeta{margin-top:30px;font-size:14px;color:var(--mut);border-top:2px solid var(--line);padding-top:18px;}
.two{display:grid;grid-template-columns:1.05fr .95fr;gap:46px;align-items:center;}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:18px;}
.mini{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--gold);border-radius:10px;padding:14px 16px;font-size:14px;line-height:1.6;color:#2c2a24;}
.mini b{color:var(--ink);}
ul.big{list-style:none;display:flex;flex-direction:column;gap:16px;}
ul.big li{position:relative;padding-left:26px;font-size:18px;line-height:1.55;color:#2c2a24;}
ul.big li::before{content:'';position:absolute;left:0;top:11px;width:11px;height:11px;border-radius:2px;background:var(--gold);}
ul.big li.muted{color:var(--mut);font-size:16px;}
ul.big li.muted::before{background:#cfc9bb;}
ul.big li.warn::before{background:var(--red);}
.num{font-family:'Crimson Pro',serif;font-weight:700;color:var(--ink);}
.sig{display:inline-block;font-size:13px;font-weight:700;color:#fff;background:var(--green);border-radius:5px;padding:1px 8px;margin-left:4px;vertical-align:middle;}
.tag{display:inline-block;font-size:13px;font-weight:700;color:#fff;border-radius:5px;padding:2px 9px;margin-right:8px;}
.tag.out{background:var(--red);}.tag.in{background:var(--blue);}
.analogy{margin-top:18px;background:#f3eede;border-radius:10px;padding:14px 18px;font-size:15px;line-height:1.6;color:#5a4d2a;}
.easy{margin-top:20px;background:#eef7f0;border:1px solid #cfe6d6;border-left:4px solid #2f9e57;border-radius:10px;padding:13px 18px;font-size:16px;line-height:1.6;color:#234a32;}
.easy b{color:#1c7a42;}.easy .lab{font-weight:800;color:#1c7a42;margin-right:6px;}
.easy.center{margin:20px auto 0;max-width:900px;text-align:left;}
.terms{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:26px;width:100%;max-width:980px;}
.term{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px 22px;text-align:left;}
.term .ts{font-size:12.5px;color:var(--gold);font-weight:800;letter-spacing:.02em;margin-bottom:8px;}
.term .th{font-family:'Crimson Pro',serif;font-size:26px;font-weight:700;color:var(--ink);margin-bottom:8px;}
.term p{font-size:15px;line-height:1.62;color:#2c2a24;}
.chart{width:100%;height:auto;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;}
.ctitle,.foot{font-size:13px;color:var(--mut);}
.ctitle{margin-bottom:8px;font-weight:600;}
.foot{margin-top:22px;border-top:1px solid var(--line);padding-top:12px;}
.cards3{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:28px 0;width:100%;max-width:840px;}
.cards3.tall .card{min-height:150px;}
.cards2{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:24px;width:100%;max-width:900px;}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px 20px;text-align:center;display:flex;flex-direction:column;justify-content:center;gap:8px;}
.card.gold{border:2px solid var(--gold);background:#fdfaf0;}
.cn{font-family:'Crimson Pro',serif;font-size:58px;font-weight:700;line-height:1;color:var(--ink);}
.card.gold .cn{color:var(--gold);}
.cl{font-size:14px;color:var(--mut);line-height:1.45;}
.ci{font-family:'Crimson Pro',serif;font-size:20px;color:var(--gold);font-weight:700;}
.ct{font-size:18px;font-weight:800;color:var(--ink);line-height:1.35;}
.bigcard{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px 26px;text-align:left;}
.bch{font-size:19px;font-weight:800;margin-bottom:12px;color:var(--ink);}
.bigcard p{font-size:15.5px;line-height:1.6;color:#2c2a24;margin:8px 0;}
.bigcard .muted{color:var(--mut);font-size:14px;}
.eq{font-family:'Crimson Pro',serif;font-size:18px;background:#1a1a17;color:#f3eede;border-radius:8px;padding:10px 14px;margin:12px 0;}
.eq .gold{color:var(--goldl);}.eq .red{color:#e58a8a;}
.dash{display:grid;grid-template-columns:1.35fr 1fr;gap:30px;align-items:center;}
.dash img{width:100%;border-radius:12px;border:1px solid var(--line);box-shadow:0 8px 30px rgba(40,36,28,.13);}
.dashfull{display:flex;justify-content:center;}
.dashfull img{max-width:82%;max-height:60vh;width:auto;height:auto;border-radius:12px;border:1px solid var(--line);box-shadow:0 10px 36px rgba(40,36,28,.16);}
ul.dnote{list-style:none;display:flex;flex-direction:column;gap:14px;}
ul.dnote li{position:relative;padding-left:22px;font-size:15.5px;line-height:1.55;color:#2c2a24;}
ul.dnote li::before{content:'';position:absolute;left:0;top:9px;width:9px;height:9px;border-radius:50%;background:var(--gold);}
.mirror{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px 24px;}
.mrow{font-size:16px;line-height:1.6;color:#2c2a24;padding:8px 0;}
.ml{font-family:'Crimson Pro',serif;color:var(--gold);font-weight:700;margin-right:8px;}
.mx{text-align:center;font-size:13px;color:#a8a296;font-weight:700;letter-spacing:.05em;margin:4px 0;}
.green{color:var(--green);}.red{color:var(--red);}.gold{color:var(--gold);}
.mc{margin-top:12px;padding-top:14px;border-top:1px solid var(--line);font-size:15px;line-height:1.6;color:#2c2a24;}
.prescript{margin:8px auto 0;max-width:820px;background:#1a1a17;color:#f3eede;border-radius:12px;padding:18px 24px;font-size:17px;line-height:1.6;}
.prescript b{color:var(--goldl);}
.warn-box{margin:18px auto 0;max-width:820px;background:#fbf2f2;border:1px solid #e6c9c9;border-left:4px solid var(--red);border-radius:10px;padding:14px 20px;font-size:15.5px;line-height:1.55;color:#5a2a2a;}
.warn-box b{color:var(--red);}
ol.pres{counter-reset:p;list-style:none;display:flex;flex-direction:column;gap:20px;margin-top:8px;max-width:1000px;}
ol.pres li{counter-increment:p;position:relative;padding-left:64px;font-size:18px;line-height:1.6;color:#2c2a24;min-height:44px;display:flex;align-items:center;}
ol.pres li::before{content:counter(p);position:absolute;left:0;top:0;width:44px;height:44px;border-radius:50%;background:var(--gold);color:#fff;font-family:'Crimson Pro',serif;font-size:24px;font-weight:700;display:flex;align-items:center;justify-content:center;}
ul.lim{list-style:none;display:flex;flex-direction:column;gap:18px;margin-top:6px;max-width:1000px;}
ul.lim li{position:relative;padding-left:26px;font-size:17px;line-height:1.6;color:#2c2a24;}
ul.lim li::before{content:'';position:absolute;left:0;top:10px;width:11px;height:11px;border-radius:2px;border:2px solid var(--mut);}
.closing h2{font-size:38px;}
.links{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:26px auto 0;max-width:720px;width:100%;}
.lk{display:flex;justify-content:space-between;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 18px;}
.lkh{font-weight:700;font-size:15px;color:var(--ink);}
.lkv{font-family:'Crimson Pro',serif;font-size:14px;color:var(--gold);}
.bar{position:absolute;top:0;left:0;height:4px;background:var(--gold);z-index:30;transition:width .25s;}
.pg{position:absolute;bottom:20px;right:30px;font-family:'Crimson Pro',serif;font-size:15px;color:#a8a296;z-index:30;}
.brand{position:absolute;bottom:20px;left:30px;font-size:12.5px;letter-spacing:.06em;color:#bdb7a8;z-index:30;text-transform:uppercase;}
.hint{position:absolute;bottom:18px;left:50%;transform:translateX(-50%);font-size:12px;color:#cfc9bb;z-index:30;}
@media (prefers-reduced-motion:reduce){.s,.bar{transition:none;}}
"""

JS = """
const slides=[...document.querySelectorAll('.s')];
let i=0;
const bar=document.querySelector('.bar'),pg=document.querySelector('.pg');
function show(n){i=Math.max(0,Math.min(slides.length-1,n));
  slides.forEach((s,k)=>s.classList.toggle('on',k===i));
  bar.style.width=((i+1)/slides.length*100)+'%';
  pg.textContent=(i+1)+' / '+slides.length;
  location.hash=i+1;}
function next(){show(i+1);}function prev(){show(i-1);}
document.addEventListener('keydown',e=>{
  if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();next();}
  else if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();prev();}
  else if(e.key==='Home'){show(0);}else if(e.key==='End'){show(slides.length-1);}});
document.querySelector('.deck').addEventListener('click',e=>{
  if(e.target.closest('a'))return;
  const x=e.clientX/window.innerWidth; x>0.5?next():prev();});
const start=parseInt(location.hash.slice(1))-1; show(isNaN(start)?0:start);
"""


def main():
    body = "".join(slides())
    page = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Antigreedy — 탐욕 거버넌스 통제 실험 (발표자료)</title>
<style>{CSS}</style></head><body>
<div class="bar"></div>
<div class="deck">{body}</div>
<div class="pg"></div><div class="brand">Antigreedy · A2A Governance</div>
<div class="hint">← → 또는 클릭으로 이동</div>
<script>{JS}</script></body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(page):,} bytes, {len(slides())} slides)")


if __name__ == "__main__":
    main()
