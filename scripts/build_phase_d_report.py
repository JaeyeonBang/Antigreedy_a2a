#!/usr/bin/env python3
"""Phase D(창발 정체성) 구현/설계 리포트 → Pretendard HTML.

실험(GLM)은 크레딧 대기이므로 이 리포트는 *구현·설계*를 다룬다 — 메커니즘·수식·실험 설계·한계.
크레딧 충전 후 `verify_claims.py phase_d`를 돌리면, build_welfare_report.py와 같은 방식으로
결과 리포트를 별도 생성한다.

    .venv/bin/python scripts/build_phase_d_report.py  →  docs/phase_d_report.html
"""
from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "phase_d_report.html"


def diagram_imposed_vs_emergent():
    W, H = 720, 300
    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="부과 vs 창발">']
    s.append('<text x="180" y="28" text-anchor="middle" fill="#0f1722" font-size="14" font-weight="700">부과 (imposed) — superordinate</text>')
    s.append('<rect x="60" y="48" width="240" height="44" rx="8" fill="#fdecea" stroke="#e5534b"/>')
    s.append('<text x="180" y="75" text-anchor="middle" fill="#a3271f" font-size="12.5">설계자가 고정 배너 주입</text>')
    s.append('<text x="180" y="120" text-anchor="middle" fill="#5b6675" font-size="12">"You are ONE TEAM. 전원 완료 시 1점,</text>')
    s.append('<text x="180" y="138" text-anchor="middle" fill="#5b6675" font-size="12">한 명이라도 굶으면 0점."</text>')
    s.append('<text x="180" y="172" text-anchor="middle" fill="#8a94a6" font-size="11.5">→ 모든 라운드 동일, 행동과 무관</text>')
    s.append('<text x="180" y="198" text-anchor="middle" fill="#1f9d55" font-size="12" font-weight="700">V6에서 유일하게 살아남은 효과</text>')
    s.append('<text x="180" y="216" text-anchor="middle" fill="#5b6675" font-size="11.5">(독점 0.65→0.41, p_holm&lt;.001)</text>')
    s.append(f'<line x1="360" y1="40" x2="360" y2="{H-30}" stroke="#e3e8ef" stroke-width="1.5"/>')
    s.append('<text x="540" y="28" text-anchor="middle" fill="#0f1722" font-size="14" font-weight="700">창발 (emergent) — Phase D ★</text>')
    s.append('<rect x="420" y="48" width="240" height="44" rx="8" fill="#eef4ff" stroke="#2f6feb"/>')
    s.append('<text x="540" y="75" text-anchor="middle" fill="#1b4fc0" font-size="12.5">관측 행동에서 군집을 *창발*</text>')
    s.append('<text x="540" y="120" text-anchor="middle" fill="#5b6675" font-size="12">"관측상 너는 [B]와 같은 부류,</text>')
    s.append('<text x="540" y="138" text-anchor="middle" fill="#5b6675" font-size="12">[A]는 다른 부류. (배정 아님, 창발)"</text>')
    s.append('<text x="540" y="160" text-anchor="middle" fill="#5b6675" font-size="12">+ 같은 상위 목표(전원 완료)</text>')
    s.append('<text x="540" y="192" text-anchor="middle" fill="#8a94a6" font-size="11.5">→ 라운드마다 행동에서 재계산</text>')
    s.append('<text x="540" y="216" text-anchor="middle" fill="#1f6feb" font-size="12" font-weight="700">질문: 정체성이 효과? vs 지시가 효과?</text>')
    s.append("</svg>")
    return (f'<figure class="fig wide"><figcaption><b>그림 1. 부과 vs 창발 — 정체성의 *출처*가 다르다</b>'
            f'<br><span class="sub">둘 다 같은 상위 목표를 달지만, 부과형은 고정 배너, 창발형은 관측 행동에서 군집을 도출한다. '
            f'V6의 부과형 효과가 "정체성" 때문인지 "지시" 때문인지를 이 대비가 분해한다.</span></figcaption>{"".join(s)}</figure>')


def diagram_clustering():
    W, H = 720, 260
    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="클러스터링">']

    def agent_bar(x, label, share, col):
        h = share * 150
        out = f'<rect x="{x}" y="{180-h:.0f}" width="40" height="{h:.0f}" rx="3" fill="{col}"/>'
        out += f'<text x="{x+20}" y="198" text-anchor="middle" fill="#0f1722" font-size="12" font-weight="700">{label}</text>'
        out += f'<text x="{x+20}" y="{180-h-6:.0f}" text-anchor="middle" fill="#5b6675" font-size="10.5">share {share:.2f}</text>'
        return out

    s.append('<text x="110" y="24" text-anchor="middle" fill="#5b6675" font-size="12">① 점유율(행동)</text>')
    s.append(agent_bar(50, "A", 0.71, "#e5534b") + agent_bar(110, "B", 0.14, "#2f6feb") + agent_bar(170, "C", 0.14, "#2f6feb"))
    s.append('<text x="300" y="110" text-anchor="middle" fill="#8a94a6" font-size="20">&#8594;</text>')
    s.append('<text x="300" y="130" text-anchor="middle" fill="#8a94a6" font-size="10">|&#916;share|&#8804;0.15</text>')
    s.append('<text x="430" y="24" text-anchor="middle" fill="#5b6675" font-size="12">② 단일-연결 군집</text>')
    s.append('<rect x="360" y="60" width="64" height="80" rx="10" fill="none" stroke="#e5534b" stroke-dasharray="4 3"/>')
    s.append('<text x="392" y="105" text-anchor="middle" fill="#a3271f" font-size="13" font-weight="700">A</text>')
    s.append('<text x="392" y="155" text-anchor="middle" fill="#a3271f" font-size="10.5">독식 부류</text>')
    s.append('<rect x="436" y="60" width="100" height="80" rx="10" fill="none" stroke="#2f6feb" stroke-dasharray="4 3"/>')
    s.append('<text x="486" y="105" text-anchor="middle" fill="#1b4fc0" font-size="13" font-weight="700">B  C</text>')
    s.append('<text x="486" y="155" text-anchor="middle" fill="#1b4fc0" font-size="10.5">공정 부류</text>')
    s.append('<text x="600" y="110" text-anchor="middle" fill="#8a94a6" font-size="20">&#8594;</text>')
    s.append('<text x="660" y="24" text-anchor="middle" fill="#5b6675" font-size="12">③ 정체성 주입</text>')
    s.append('<rect x="612" y="60" width="100" height="80" rx="8" fill="#eef4ff" stroke="#2f6feb"/>')
    s.append('<text x="662" y="92" text-anchor="middle" fill="#1b4fc0" font-size="10.5">"너는 C와</text>')
    s.append('<text x="662" y="108" text-anchor="middle" fill="#1b4fc0" font-size="10.5">같은 부류,</text>')
    s.append('<text x="662" y="124" text-anchor="middle" fill="#1b4fc0" font-size="10.5">A는 다름"</text>')
    s.append(f'<text x="{W/2:.0f}" y="{H-14}" text-anchor="middle" fill="#8a94a6" font-size="11">순수 파이썬 union-find — Leiden(igraph/leidenalg 부재)의 자리표시자, drop-in 교체 가능</text>')
    s.append("</svg>")
    return (f'<figure class="fig wide"><figcaption><b>그림 2. 행동 클러스터링 → 창발 정체성 (3단계)</b>'
            f'<br><span class="sub">점유율이 비슷한 에이전트끼리 묶여(단일-연결) "부류"가 창발하고, 그 군집을 각 프롬프트에 데이터로 명시한다.</span>'
            f'</figcaption>{"".join(s)}</figure>')


CSS = """
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
:root{--ink:#1a2230;--mut:#5b6675;--line:#e3e8ef;--bg:#fbfcfe;--card:#fff;}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:'Pretendard',-apple-system,system-ui,sans-serif;font-size:16px;line-height:1.72;-webkit-font-smoothing:antialiased;}
.wrap{max-width:880px;margin:0 auto;padding:40px 24px 96px;}
h1{font-size:26px;font-weight:800;letter-spacing:-.02em;line-height:1.34;margin:0 0 8px;}
h2{font-size:21px;font-weight:700;margin:36px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--line);}
h3{font-size:17px;font-weight:700;margin:24px 0 8px;color:#26303f;}
p{margin:10px 0;}ul{margin:10px 0;padding-left:20px;}li{margin:5px 0;}
b,strong{font-weight:700;color:#0f1722;}em,i{color:#3a4150;font-style:italic;}
a{color:#1f6feb;text-decoration:none;}a:hover{text-decoration:underline;}
code{background:#eef1f6;border-radius:5px;padding:1px 6px;font-size:13.5px;
  font-family:'Pretendard',ui-monospace,Menlo,monospace;color:#b21f6b;}
.formula{background:#0f1722;color:#e6edf3;border-radius:10px;padding:15px 18px;margin:12px 0;
  font-family:ui-monospace,Menlo,monospace;font-size:13px;line-height:1.7;white-space:pre-wrap;overflow-x:auto;}
.lead{font-size:17px;color:#2a333f;}
.status{background:#fff;border:1px solid var(--line);border-left:4px solid #d29922;border-radius:10px;
  padding:13px 17px;font-size:14px;color:var(--mut);margin:16px 0;}
.callout{margin:12px 0;padding:12px 16px;border-radius:9px;font-size:14px;line-height:1.6;border:1px solid var(--line);}
.callout.q{background:#f1f6ff;border-left:4px solid #2f6feb;}
.callout.warn{background:#fff8e6;border-left:4px solid #e0b341;}
.fig{margin:0;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 14px 8px;}
.fig.wide{margin:16px 0;}
figcaption{font-size:13px;color:var(--mut);margin-bottom:6px;}figcaption b{color:#0f1722;font-size:13.5px;}
figcaption .sub{color:#7a8699;font-size:12px;}
.chart{width:100%;height:auto;}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:13.5px;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;}
th,td{padding:9px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;}
th{background:#f4f7fb;font-weight:700;}tr:last-child td{border-bottom:0;}
.ok{color:#1f9d55;font-weight:700;}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);color:#9aa6b6;font-size:12.5px;}
"""


def main():
    body = f"""
<h2 id="what">1. Phase D는 무엇인가</h2>
<p>V6의 통제 실험에서 <b>유일하게 살아남은 입력측 효과</b>는 <em>부과된</em> "ONE TEAM" 배너(superordinate)였다
(독점 0.65&#8594;0.41, p_holm&lt;.001). 그런데 그 효과가 <b>"정체성" 때문인가, 아니면 단지 "지시(instruction)"가
주어졌기 때문인가</b>? — 이것이 논문 &#167;7의 미해결 질문이다.</p>
<div class="callout q"><b>Phase D의 핵심 아이디어.</b> 정체성을 *위에서 부과*하지 말고, <b>관측된 행동에서
*창발*</b>시켜 보자. 누가 누구와 비슷하게 자원을 점유했는지로 "부류(group)"를 군집화하고, 그 군집을 각
에이전트에게 데이터로 알려준다. 부과형과 같은 상위 목표를 달면, 둘의 비교가 곧 <b>"정체성 vs 지시"의 분해</b>다.</div>
{diagram_imposed_vs_emergent()}

<h2 id="how">2. 메커니즘 &#183; 수식 (구현)</h2>
<p>구현은 <code>antigreedy/scenario/reputation_identity.py</code> + <code>emergent_identity</code> 셰이퍼다.
세 단계: <b>&#9312; 행동 특징 &#8594; &#9313; 군집 &#8594; &#9314; 정체성 주입.</b></p>
<div class="formula">&#9312; 점유율(행동):  share_i = mine / total          # turn_log 누적 전달량
&#9313; 군집(단일-연결 union-find):
     |share_i &#8722; share_j| &#8804; thresh(=0.15) 이면 같은 부류로 연결
     &#8594; 점유율이 비슷한 에이전트끼리 묶임 (독식 부류 / 공정 부류)
&#9314; 정체성 주입(emergent_identity 셰이퍼):
     "관측상 너는 [내 부류]와 같고, [다른 부류]는 다르다 &#8212; 배정 아님, 창발.
      그러나 전원 완료해야 팀 1점, 한 명이라도 굶으면 0점."</div>
{diagram_clustering()}
<p><b>각 요소의 의미.</b></p>
<ul>
<li><b>왜 점유율 기반인가</b> &#8212; 이 환경의 평판은 점유율(과점도)에서 파생되므로, 행동 군집은 곧 "독식 부류 vs 공정 부류"가 된다.
  이는 SCM의 <i>따뜻함(warmth)=착취 의도</i> 축에 대응한다(<code>related_work.md</code> &#167;C.3).</li>
<li><b>왜 단일-연결(union-find)인가</b> &#8212; 설계 의도는 *Leiden 커뮤니티 검출*이지만 igraph/leidenalg/numpy가
  설치돼 있지 않아(설치성&#183;크레딧-프리 유지), <b>순수 파이썬 단일-연결을 *자리표시자*로</b> 썼다. 셰이퍼&#183;하니스가
  동일하므로 <b>Leiden으로 drop-in 교체 가능</b>하다. (정직성: 이건 Leiden이 아니다.)</li>
<li><b>부과형과 같은 상위 목표</b>를 달아 둔 것이 핵심 &#8212; 두 arm의 차이는 *정체성의 출처(부과 vs 창발)*뿐이라,
  대비가 "정체성이 효과인가"를 깨끗이 겨눈다.</li>
</ul>
<div class="callout warn">&#9888; <b>창발의 그림자 &#8212; 카스트화 위험.</b> 한 번 "독식 부류"로 군집되면 *자기범주화*로 더 독식하고
(자기실현) 배제될 수 있다(<code>related_work.md</code> &#167;C.2&#183;C.10). 이 v0은 *매 라운드 재계산*(고착 방지)하지만,
불변 원장과 결합하면 위험이 커진다 &#8212; 향후 Beta 감쇠 뷰로 완화 검정 예정.</div>

<h2 id="exp">3. 실험 설계 (크레딧 대기)</h2>
<p>하니스: <code>verify_claims.py phase_d</code>. V6와 동일 방법론(공통 baseline&#183;순열검정&#183;Holm). 4 arm &#215; N:</p>
<table><thead><tr><th>arm</th><th>주입</th><th>역할</th></tr></thead><tbody>
<tr><td><code>none</code></td><td>없음</td><td>기준선</td></tr>
<tr><td><code>imposed</code></td><td>superordinate(고정 "ONE TEAM")</td><td>부과형 = V6 생존 효과</td></tr>
<tr><td><code>emergent</code> &#9733;</td><td>창발 정체성(행동 군집)</td><td>Phase D 처치</td></tr>
<tr><td><code>neutral_filler</code></td><td>무내용 동일길이 배너</td><td>길이/지시성 대조</td></tr>
</tbody></table>
<p><b>사전 대조(Holm 6개)와 각 질문:</b></p>
<ul>
<li><b>top: emergent vs none</b> &#8212; 창발 정체성이 *독점을 줄이는가*(부과 효과 재현?).</li>
<li><b>top: emergent vs imposed</b> &#8212; <b>핵심 분해.</b> &#8776;(ns)면 "정체성이 효과"(출처 무관), &#8800;면 "부과/지시가 효과".</li>
<li><b>top: imposed vs none</b> &#8212; V6 superordinate 효과의 *재현 점검*.</li>
<li><b>top: emergent vs neutral_filler</b> &#8212; 효과가 *프롬프트 길이 이상*인가.</li>
<li>welfare emergent vs none / vs imposed &#8212; welfare 부작용 점검.</li>
</ul>
<p>실행(크레딧 충전 후):</p>
<div class="formula">set -a; . &lt;(grep -E '^OPENROUTER_API_KEY=' /mnt/d/projects/A2A/oldman_agent/.env); set +a
.venv/bin/python -u scripts/verify_claims.py phase_d --seeds 30 --out docs/verify_phase_d.json</div>
<p>실행 후엔 <code>build_welfare_report.py</code>와 동일한 방식으로 결과 리포트를 생성한다.</p>

<h2 id="status">4. 상태 &#183; 한계 (정직)</h2>
<ul>
<li><span class="ok">&#10003; 구현 완료</span> &#8212; 모듈&#183;셰이퍼&#183;하니스 arm. <b>9개 결정적 단위테스트</b>(클러스터링&#183;정체성 프레임&#183;셰이퍼) 포함, <b>전체 220 통과</b>. mock 스모크로 하니스 동작 확인(mock은 배너를 안 읽으므로 arm 동일 &#8212; 정상).</li>
<li><b>GLM 실험은 크레딧 대기</b> &#8212; mock은 결정론이라 정체성 효과를 못 만든다. 진짜 신호는 실제 모델이 배너를 읽어야 나온다.</li>
<li><b>Leiden 자리표시자</b> &#8212; 클러스터러는 순수 파이썬 단일-연결이다. 설계의 Leiden-on-cosine으로 교체 시 결과가 달라질 수 있음(특히 큰 n).</li>
<li><b>n=3&#183;단일 모델&#183;단일 시나리오</b> &#8212; V6와 동일 일반화 한계. 창발 정체성은 n이 클수록 더 의미 있다(군집이 풍부).</li>
<li><b>환원 배제 미수행</b> &#8212; "창발 정체성이 *인과적* 스크리닝인가 단순 상관인가"는 위약 군집&#183;모듈성 귀무검정이 필요(<code>related_work.md</code> &#167;C.9). v1 과제.</li>
</ul>
"""
    page = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Phase D — 창발 정체성 구현/설계 리포트</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Phase D — 정체성을 <em>부과</em>하지 말고 행동에서 <em>창발</em>시키기</h1>
<p class="lead">창발 정체성(emergent identity) 구현&#183;설계 리포트. V6의 유일 생존 효과(부과된 "ONE TEAM")가
"정체성"인지 "지시"인지를 분해하기 위한 Phase D.</p>
<div class="status">&#128230; <b>구현 완료, 실험은 크레딧 대기.</b> 코드&#183;단위테스트(220 통과)&#183;실험 하니스 모두 준비됨.
실제 GLM 실험은 OpenRouter 크레딧 충전 후 1회 실행. 이 리포트는 *메커니즘&#183;수식&#183;실험 설계*를 다룬다.</div>
{body}
<footer>생성: <code>scripts/build_phase_d_report.py</code> &#183; 구현: <code>antigreedy/scenario/reputation_identity.py</code>,
<code>prompt_shapers.py</code>(emergent_identity), <code>verify_claims.py</code>(phase_d) &#183;
설계&#183;문헌: <code>docs/design_identity_dao.md</code> &#167;3.4, <code>docs/related_work.md</code> &#167;C &#183; 폰트: Pretendard</footer>
</div></body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(OUT.parent.parent)} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
