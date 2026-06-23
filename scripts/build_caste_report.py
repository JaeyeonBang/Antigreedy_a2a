#!/usr/bin/env python3
"""Phase 1(카스트화 λ-스윕) 결과/설계 리포트 → Pretendard HTML.

데이터(docs/verify_caste_lambda.json)에서 결과를 *로드*해 렌더한다. 해석 문구는 숫자에서
파생(하드코딩 금지 → stale 방지). 핵심 종속변수 = recovery_rate(저평판 회복률).

    .venv/bin/python scripts/build_caste_report.py  →  docs/caste_report.html
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "caste_report.html"
ORDER = ["none", "ost_linear", "ost_beta_l10", "ost_beta_l09", "ost_beta_l07"]
LABEL = {"none": "none", "ost_linear": "linear(현행)", "ost_beta_l10": "beta λ=1.0",
         "ost_beta_l09": "beta λ=0.9", "ost_beta_l07": "beta λ=0.7"}
COL = {"none": "#7a8699", "ost_linear": "#e5534b", "ost_beta_l10": "#9a4fd0",
       "ost_beta_l09": "#2f6feb", "ost_beta_l07": "#1f9d55"}


def _bars(A, key, fmt="{:.3f}"):
    order = [a for a in ORDER if a in A]
    W, H = 720, 280
    pl, pr, pt, pb = 46, 14, 18, 64
    pw, ph = W - pl - pr, H - pt - pb
    slot = pw / len(order)
    bw = slot * 0.5
    vmax = max([A[a][key] for a in order] + [1e-9])
    scale = 1.0 if vmax <= 1.0 else vmax

    def y(v):
        return pt + ph * (1 - v / scale)

    s = [f'<svg viewBox="0 0 {W} {H}" class="chart">']
    for g in (0, 0.25, 0.5, 0.75, 1.0):
        gv = g * scale
        s.append(f'<line x1="{pl}" y1="{y(gv):.1f}" x2="{W-pr}" y2="{y(gv):.1f}" stroke="#eef1f6"/>')
        s.append(f'<text x="{pl-6}" y="{y(gv)+3:.1f}" text-anchor="end" fill="#9aa6b6" font-size="10">{gv:.2f}</text>')
    for i, arm in enumerate(order):
        v = A[arm][key]
        cx = pl + slot * i + slot / 2
        x = cx - bw / 2
        s.append(f'<rect x="{x:.1f}" y="{y(v):.1f}" width="{bw:.1f}" height="{y(0)-y(v):.1f}" rx="3" fill="{COL[arm]}"/>')
        s.append(f'<text x="{cx:.1f}" y="{y(v)-5:.1f}" text-anchor="middle" fill="#0f1722" font-size="11.5" font-weight="700">{fmt.format(v)}</text>')
        s.append(f'<text x="{cx:.1f}" y="{y(0)+15:.1f}" text-anchor="middle" fill="#3a4150" font-size="10.5" font-weight="600">{LABEL[arm]}</text>')
    s.append("</svg>")
    return "".join(s)


def results_block():
    jp = OUT.parent / "verify_caste_lambda.json"
    if not jp.exists():
        return ('<div class="status">⏳ <b>실험 데이터 대기.</b> <code>verify_caste_lambda.json</code> 생성 후 '
                '결과 차트·대조표가 이 자리에 렌더된다.</div>')
    d = json.loads(jp.read_text(encoding="utf-8"))
    A = d["arms"]
    cfg = d["config"]

    def cmean(a, k):
        return A[a][k]

    rec = {a: A[a]["rec_mean"] for a in ORDER if a in A}
    best = max(rec, key=rec.get)
    cmap = {c["label"]: c for c in d["contrasts"]}

    def verdict_line(substr):
        for lab, c in cmap.items():
            if substr in lab:
                tag = "유의(SIG)" if c["sig"] else "무유의(ns)"
                return f'{lab}: p={c["p"]:.4f}, p_holm={c["p_holm"]:.4f} → <b>{tag}</b>'
        return ""

    rec_chart = (f'<figure class="fig wide"><figcaption><b>그림 R1. arm별 저평판 회복률(recovery_rate)</b>'
                 f'<br><span class="sub">0 = 한 번 찍히면 못 돌아옴(카스트 고착), 높을수록 빠른 회복. '
                 f'각 arm은 *자신의 평판 규칙*으로 측정.</span></figcaption>{_bars(A, "rec_mean")}'
                 f'<figcaption style="margin-top:6px"><span class="sub">{cfg["model"]} · N={cfg["seeds"]} · '
                 f'{cfg["agents"]}ag · rounds={cfg["rounds"]}</span></figcaption></figure>')
    top_chart = (f'<figure class="fig wide"><figcaption><b>그림 R2. arm별 top-share(독점) — 낮을수록 공정</b>'
                 f'</figcaption>{_bars(A, "top_mean")}</figure>')

    rows = ""
    for c in d["contrasts"]:
        cls = ' style="background:#eefaf1"' if c["sig"] else ""
        verdict = "✅ SIG" if c["sig"] else "ns"
        rows += (f'<tr{cls}><td>{c["label"]}</td><td>{c["p"]:.4f}</td>'
                 f'<td><b>{c["p_holm"]:.4f}</b></td><td>{verdict}</td></tr>')
    table = ('<table><thead><tr><th>대조</th><th>p</th><th>p_holm</th><th>판정</th></tr></thead>'
             f'<tbody>{rows}</tbody></table>')

    causal = verdict_line("불변성 인과")
    return f"""
<h2 id="results">★ 결과 ({cfg['model']}, N={cfg['seeds']}) — 망각 λ가 회복을 좌우하는가</h2>
<div class="callout q"><b>한 줄 결론(데이터 파생).</b> 회복률이 가장 높은 조건은 <b>{LABEL[best]}</b>
(recovery {rec[best]:.3f}). 핵심 인과 대조 — {causal or '대조 데이터 없음'}.</div>
{rec_chart}
<p><b>회복률 요약.</b> {' · '.join(f'{LABEL[a]} {rec[a]:.3f}' for a in ORDER if a in A)}.
영구 누적(linear / beta λ=1.0)일수록 낮고, 망각이 빠를수록(λ=0.7) 높으면 <b>"불변성이 카스트를 만든다"</b>는
설계 가설을 지지한다. 반대 패턴이면 가설 기각 — 어느 쪽이든 본 실험이 *답한다*.</p>
{top_chart}
<p><b>독점/welfare 동시 관찰.</b> top-share = {' · '.join(f'{LABEL[a]} {cmean(a, "top_mean"):.3f}' for a in ORDER if a in A)};
welfare = {' · '.join(f'{LABEL[a]} {cmean(a, "comp_mean"):.2f}' for a in ORDER if a in A)}.
배제(ostracism)가 독점을 줄이되 welfare를 해치는지(공유지의 부분완료 함정)도 함께 본다.</p>
{table}
<p>상세·한계 = <code>docs/verify_caste_lambda.md</code>. 원자료 독립 재계산 0 불일치 검증.</p>
"""


def diagram_lambda():
    W, H = 720, 250
    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="lambda forgetting">']
    s.append('<text x="180" y="26" text-anchor="middle" fill="#0f1722" font-size="14" font-weight="700">λ = 1.0 (망각 없음)</text>')
    s.append('<rect x="60" y="44" width="240" height="40" rx="8" fill="#fdecea" stroke="#e5534b"/>')
    s.append('<text x="180" y="69" text-anchor="middle" fill="#a3271f" font-size="12">오래된 과점도 가중치 1 영구 유지</text>')
    s.append('<text x="180" y="120" text-anchor="middle" fill="#5b6675" font-size="12">한 번 "greedy"로 찍히면</text>')
    s.append('<text x="180" y="140" text-anchor="middle" fill="#5b6675" font-size="12">공정해져도 평판이 안 오름</text>')
    s.append('<text x="180" y="176" text-anchor="middle" fill="#e5534b" font-size="12.5" font-weight="700">→ 자기실현 카스트 (고착)</text>')
    s.append(f'<line x1="360" y1="36" x2="360" y2="{H-24}" stroke="#e3e8ef" stroke-width="1.5"/>')
    s.append('<text x="540" y="26" text-anchor="middle" fill="#0f1722" font-size="14" font-weight="700">λ &lt; 1 (지수 망각)</text>')
    s.append('<rect x="420" y="44" width="240" height="40" rx="8" fill="#eaf6ee" stroke="#1f9d55"/>')
    s.append('<text x="540" y="69" text-anchor="middle" fill="#147a3d" font-size="12">오래된 과점은 λ^Δ로 감쇠</text>')
    s.append('<text x="540" y="120" text-anchor="middle" fill="#5b6675" font-size="12">최근 행동이 평판을 지배</text>')
    s.append('<text x="540" y="140" text-anchor="middle" fill="#5b6675" font-size="12">공정해지면 평판이 회복</text>')
    s.append('<text x="540" y="176" text-anchor="middle" fill="#1f9d55" font-size="12.5" font-weight="700">→ 자기교정 (회복 가능)</text>')
    s.append("</svg>")
    return (f'<figure class="fig wide"><figcaption><b>그림 1. 망각계수 λ — 불변성이 카스트를 만드는가</b>'
            f'<br><span class="sub">Beta 평판의 의사관측치(r/s)에 λ^Δ 시간감쇠를 곱한다. λ=1이면 영구 누적, '
            f'λ&lt;1이면 최근 가중 → 회복 가능. 본 실험은 이 차이를 회복률로 측정한다.</span></figcaption>{"".join(s)}</figure>')


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
    body = results_block() + f"""
<h2 id="what">1. Phase 1은 무엇인가 (설계)</h2>
<p>보고서(V6 통제실험)의 향후 과제 중 <b>"불변성이 카스트를 만드나?"</b>를 측정한다. 평판이 <em>영구 누적</em>
(λ=1)이면 한 번 'greedy'로 찍힌 에이전트가 회복 못 해 <b>자기실현 카스트</b>가 된다(<code>related_work.md</code> §R3).
망각 λ&lt;1이 회복을 살리는지 <b>λ-스윕 + 저평판 회복률</b>로 검정한다.</p>
{diagram_lambda()}

<h2 id="how">2. 메커니즘 · 수식 (구현)</h2>
<p>구현은 <code>antigreedy/governance/reputation_calc.py</code>(<code>beta_reputation</code>) +
<code>beta_ostracism.py</code>(<code>BetaOstracismPolicy</code>) + 카스트 지표 <code>antigreedy/caste_metrics.py</code>.</p>
<div class="formula">Beta 평판 + 지수 망각:
  라운드 t의 순간 점유 share_t ≤ fair(=1/n) 이면 긍정 r, 초과면 부정 s
  r = Σ_t λ^Δ · [share_t ≤ fair],   s = Σ_t λ^Δ · [share_t &gt; fair]   (Δ = 현재−t)
  E[rep] = (r + 1) / (r + s + 2)          # Jøsang Beta 평판 기댓값 ∈ (0,1)
  λ=1 → 영구 누적(망각 없음),  λ&lt;1 → 최근 가중(회복 가능)

회복률(카스트 지표):
  rep &lt; 0.45 진입 후 임계 위로 복귀까지 Δrounds → 1/Δrounds (빠를수록 큼)
  끝까지 못 돌아오면 0.  모든 진입 이벤트 평균 = recovery_rate ∈ [0,1]</div>
<ul>
<li><b>왜 Beta 평판인가</b> — 현행 자작식 <code>rep=clip(1−overage/fair, .1, 1)</code>은 누적 점유만 보는 특수형.
  Beta(Jøsang)는 표준 평판 모형이고 λ로 <i>망각</i>을 자연스럽게 끼울 수 있다(<code>related_work.md</code> §R3).</li>
<li><b>왜 회복률인가</b> — "카스트화"의 조작적 정의 = <i>한 번 떨어진 평판이 못 돌아옴</i>. 회복률 0이 곧 카스트.
  λ를 바꿔도 같은 로그를 다른 규칙으로 재평가하므로 *인과*를 분리한다.</li>
<li><b>배제의 자기교정성</b> — <code>BetaOstracismPolicy</code>는 rep&lt;0.45면 배제(deny). 배제되면 점유가 멎어
  λ&lt;1에서 평판이 회복되어 재참여가 허용된다 — λ=1이면 회복이 막혀 영구 배제(카스트).</li>
</ul>

<h2 id="exp">3. 실험 설계</h2>
<p>하니스: <code>verify_claims.py caste_lambda</code>. V6와 동일 방법론(공통 baseline·순열검정·Holm). 5 arm × N:</p>
<table><thead><tr><th>arm</th><th>구동 평판</th><th>역할</th></tr></thead><tbody>
<tr><td><code>none</code></td><td>—</td><td>무규제 기준선</td></tr>
<tr><td><code>ost_linear</code></td><td>선형 누적(현행)</td><td>기존 배제+가십 (영구 누적 대조)</td></tr>
<tr><td><code>ost_beta_l10</code></td><td>Beta λ=1.0</td><td>망각 없는 Beta (불변성)</td></tr>
<tr><td><code>ost_beta_l09</code></td><td>Beta λ=0.9</td><td>느린 망각</td></tr>
<tr><td><code>ost_beta_l07</code> ★</td><td>Beta λ=0.7</td><td>빠른 망각 (회복 가설 처치)</td></tr>
</tbody></table>
<p><b>red-green 핵심(단위 검증 완료):</b> 같은 합성 로그에서 λ=0.7 회복률 &gt; λ=1.0 회복률
(<code>tests/test_caste_metrics.py</code>), Beta 평판이 망각으로 회복을 살림(<code>tests/test_reputation_calc.py</code>).
실 GLM에서도 같은 방향이면 인과 재현.</p>

<h2 id="status">4. 상태 · 한계 (정직)</h2>
<ul>
<li><span class="ok">✓ 구현·단위테스트 완료</span> — beta_reputation·BetaOstracismPolicy·modularity_q·recovery_rate,
  <b>신규 18 테스트</b> 포함 전체 <b>252 통과</b>. 크레딧-프리 mock 스모크로 하니스 동작 확인.</li>
<li><b>n=3·단일 모델(glm-4.7-flash)·단일 시나리오</b> — V6와 동일 일반화 한계. 일반성 미주장.</li>
<li><b>회복률은 arm별 자기 평판으로 측정</b> — 정책 변화와 배분 변화가 함께 들어간다(의도된 통합 효과).
  순수 배분 효과만 보려면 고정 기준 λ로 재측정 필요(향후).</li>
<li><b>modularity_q는 본 실험 종속변수가 아닌 보조 지표</b> — 군집 분리도용. 회복률이 주 DV.</li>
</ul>
"""
    has_data = (OUT.parent / "verify_caste_lambda.json").exists()
    status = ("✅ <b>실험 완료 + 구현·단위테스트(252 통과).</b> 아래 ★결과 = 실측(원자료 "
              "<code>verify_caste_lambda.json</code>, 독립 재계산 0 불일치).") if has_data else \
             ("⏳ <b>구현·단위테스트 완료(252 통과). 실험 데이터 대기.</b> 데이터 생성 후 ★결과가 렌더된다.")
    page = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Phase 1 — 카스트화 λ-스윕 리포트</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Phase 1 — 불변성(λ=1)이 카스트를 만드는가</h1>
<p class="lead">Beta+λ 평판 · 저평판 <b>회복률</b>로 "한 번 찍힌 에이전트가 회복하는가"를 측정. 망각계수 λ를
스윕해 <b>불변성과 카스트화의 인과</b>를 분리한다.</p>
<div class="status">{status}</div>
{body}
<footer>생성: <code>scripts/build_caste_report.py</code> · 구현: <code>antigreedy/governance/reputation_calc.py</code>(beta_reputation),
<code>beta_ostracism.py</code>, <code>antigreedy/caste_metrics.py</code>, <code>verify_claims.py</code>(caste_lambda) ·
설계·문헌: <code>docs/related_work.md</code> §R3 · 폰트: Pretendard</footer>
</div></body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(OUT.parent.parent)} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
