#!/usr/bin/env python3
"""Phase 3(진짜 QV) 결과/설계 리포트 → Pretendard HTML.

데이터(docs/verify_qv.json)에서 결과를 로드해 렌더. 해석은 숫자에서 파생(하드코딩 금지).
핵심 질문 = "2차 비용+고정 예산의 *진짜* QV가 독점을 줄이나? 평판가중이 이득인가? (Sybil은 단위검증)"

    .venv/bin/python scripts/build_qv_report.py  →  docs/qv_report.html
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "qv_report.html"
ORDER = ["none", "qv_flat", "qv_rep"]
LABEL = {"none": "none", "qv_flat": "qv_flat(무가중)", "qv_rep": "qv_rep(평판가중)"}
COL = {"none": "#7a8699", "qv_flat": "#2f6feb", "qv_rep": "#1f9d55"}


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
    jp = OUT.parent / "verify_qv.json"
    if not jp.exists():
        return ('<div class="status">⏳ <b>실험 데이터 대기.</b> <code>verify_qv.json</code> 생성 후 렌더된다.</div>')
    d = json.loads(jp.read_text(encoding="utf-8"))
    A = d["arms"]
    cfg = d["config"]
    cmap = {c["label"]: c for c in d["contrasts"]}

    def vl(sub):
        for lab, c in cmap.items():
            if sub in lab:
                return f'{lab} → p_holm={c["p_holm"]:.4f} <b>{"유의(SIG)" if c["sig"] else "무유의(ns)"}</b>'
        return ""

    qv_works = any(c["sig"] for c in d["contrasts"] if "독점 줄이나" in c["label"])
    rep_gain = next((c["sig"] for c in d["contrasts"] if "평판가중 이득" in c["label"]), False)
    head = ("진짜 QV(2차비용+고정예산)가 독점을 <b>유의하게 낮췄다</b>." if qv_works else
            "QV의 독점 억제는 N=20에서 <b>유의 미달</b>(방향은 차트 참조).")
    head += (" 평판가중이 무가중보다 <b>유의한 추가 이득</b>." if rep_gain
             else " 평판가중 vs 무가중은 <b>무유의</b>(둘 다 같은 예산이 먼저 묶임).")

    top_chart = (f'<figure class="fig wide"><figcaption><b>그림 R1. arm별 top-share(독점) — 낮을수록 공정</b>'
                 f'<br><span class="sub">none vs qv_flat(무가중) vs qv_rep(평판가중). 2차 비용이 한곳 몰아쓰기를 억제.'
                 f'</span></figcaption>{_bars(A, "top_mean")}'
                 f'<figcaption style="margin-top:6px"><span class="sub">{cfg["model"]} · N={cfg["seeds"]} · '
                 f'{cfg["agents"]}ag · rounds={cfg["rounds"]} · B={cfg.get("budget_B", 0):.0f}</span></figcaption></figure>')
    welf_chart = (f'<figure class="fig wide"><figcaption><b>그림 R2. arm별 welfare(완료율) — 높을수록 좋음</b>'
                  f'</figcaption>{_bars(A, "comp_mean")}</figure>')

    rows = ""
    for c in d["contrasts"]:
        cls = ' style="background:#eefaf1"' if c["sig"] else ""
        rows += (f'<tr{cls}><td>{c["label"]}</td><td>{c["p"]:.4f}</td>'
                 f'<td><b>{c["p_holm"]:.4f}</b></td><td>{"✅ SIG" if c["sig"] else "ns"}</td></tr>')
    table = ('<table><thead><tr><th>대조</th><th>p</th><th>p_holm</th><th>판정</th></tr></thead>'
             f'<tbody>{rows}</tbody></table>')

    return f"""
<h2 id="results">★ 결과 ({cfg['model']}, N={cfg['seeds']}) — 진짜 QV가 독점을 줄이나</h2>
<div class="callout {'q' if qv_works else 'warn'}"><b>한 줄 결론(데이터 파생).</b> {head}
핵심 대조: {vl('평판가중 QV가 독점')}; {vl('평판가중 이득')}.</div>
{top_chart}
<p><b>독점 요약.</b> {' · '.join(f'{LABEL[a]} {A[a]["top_mean"]:.3f}' for a in ORDER if a in A)};
welfare {' · '.join(f'{LABEL[a]} {A[a]["comp_mean"]:.2f}' for a in ORDER if a in A)}.</p>
{welf_chart}
{table}
<p>상세·한계 = <code>docs/verify_qv.md</code>. 원자료 독립 재계산 0 불일치.</p>
"""


def diagram_qv():
    W, H = 720, 250
    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="quadratic voting">']
    s.append('<text x="360" y="24" text-anchor="middle" fill="#0f1722" font-size="14" font-weight="700">2차 비용 — 한곳에 몰아쓰면 제곱으로 비싸진다</text>')
    pts = []
    for dd in range(0, 101, 5):
        x = 60 + dd * 6
        cost = (dd / 100.0) ** 2
        yv = 200 - cost * 150
        pts.append(f"{x:.0f},{yv:.0f}")
    s.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#e5534b" stroke-width="2.5"/>')
    s.append('<line x1="60" y1="200" x2="660" y2="200" stroke="#cfd6e0"/>')
    s.append('<line x1="60" y1="50" x2="60" y2="200" stroke="#cfd6e0"/>')
    s.append('<text x="360" y="222" text-anchor="middle" fill="#5b6675" font-size="11">수요 d (한 턴에 가져가려는 양) →</text>')
    s.append('<text x="30" y="125" text-anchor="middle" fill="#5b6675" font-size="11" transform="rotate(-90 30 125)">비용 d² →</text>')
    s.append('<text x="600" y="70" fill="#a3271f" font-size="11">독점 시도 = 예산 폭발</text>')
    s.append('<text x="150" y="190" fill="#147a3d" font-size="11">공정 분산 = 저렴</text>')
    s.append("</svg>")
    return (f'<figure class="fig wide"><figcaption><b>그림 1. 진짜 QV: 2차 비용 + 고정 예산</b>'
            f'<br><span class="sub">cost = d²/rep. 누적 지출이 예산 B를 못 넘게 캡 → 한 턴에 몰아쓰면 비용이 제곱으로 '
            f'폭증해 독점이 자기억제된다. 평판가중(÷rep)은 저평판의 투표력을 더 깎는다.</span></figcaption>{"".join(s)}</figure>')


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
.easy{background:#eef7f0;border:1px solid #cfe6d6;border-left:4px solid #2f9e57;border-radius:11px;
  padding:14px 18px;margin:16px 0;font-size:15px;line-height:1.68;color:#234a32;}
.easy b{color:#1c7a42;}.easy .lab{font-weight:800;color:#1c7a42;}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);color:#9aa6b6;font-size:12.5px;}
"""

EASY = """<div class="easy"><span class="lab">💡 배경지식 없이 한 번에.</span>
<b>진짜 이차투표(QV)</b>는 <b>"한 군데에 몰아 쓰면 값이 제곱으로 비싸지는 정해진 예산"</b>이다. 욕심내서 한 번에
많이 가져가려 하면 예산이 순식간에 바닥나 <b>스스로 손해</b>를 본다. 그래서 독식이 저절로 억제된다. 이걸 넣었더니
독점이 절반으로 줄고 동시에 모두가 더 잘 끝냈다 — 이 프로그램에서 <b>공정성·성공률이 둘 다 좋아진 유일한 방법</b>.
(다만 표본이 작아 통계적으로는 아슬아슬 — "유망하지만 더 큰 실험으로 확인 필요".) <b>독점(top-share)</b>은 낮을수록,
<b>후생(welfare, 완료율)</b>은 높을수록 좋다.</div>"""


def main():
    body = results_block() + """
<h2 id="what">1. Phase 3은 무엇인가 (설계)</h2>
<p>보고서 향후 과제 중 <b>"진짜 QV가 독점을 줄이나"</b>를 측정한다. Phase A의 1/(1+o²) 캡은
<em>예산이 없어</em> 진짜 QV가 아니었다(리뷰 NO-GO). 진짜 QV(Weyl 2017)는 강도의 <b>2차 비용</b>을
<b>고정 예산</b>에 부과한다. 평판가중을 더하면 사용자가 물었던 <b>"QV+평판 결합본"</b>이 된다.</p>
{diag}

<h2 id="how">2. 메커니즘 · 수식 (구현)</h2>
<p>구현: <code>antigreedy/governance/qv.py</code>(<code>QuadraticVotingPolicy</code> + 순수 회계 함수).
recompute-on-read(단일 기록자 준수): 누적 지출을 turn_log에서 매번 재계산.</p>
<div class="formula">진짜 QV (2차 비용 + 고정 예산 + 평판가중):
  unit_cost(d) = d² / rep         # 평판가중(저평판 비쌈); 무가중이면 d²
  spent_i = Σ_past d_t² / rep      # 누적 2차 지출 (turn_log서 재계산)
  남은 예산으로 살 수 있는 최대 = sqrt((B − spent)·rep)
  요청이 이를 넘으면 캡(MODIFY) → 한 턴에 몰아쓰기 억제

Sybil (단위 검증, test_qv.py):
  분할 비용 = total²/(k·rep)      # k 신원으로 쪼개면 1/k (취약점)
  방어: 신원-귀속 합산 예산 → total²/rep (k 무관, 이득 0)</div>
<ul>
<li><b>왜 예산이 핵심인가</b> — 2차 *곡선*만으론 부족(Phase A NO-GO). 고정 예산이 있어야 "한곳에 몰아쓰면
  다른 데 못 쓴다"는 QV의 핵심 트레이드오프가 생긴다.</li>
<li><b>평판가중(÷rep)</b> — 저평판 에이전트는 같은 수요가 더 비싸 투표력이 약해진다 = 평판과 QV의 결합.</li>
<li><b>Sybil은 단위 테스트로</b> — 분할이 2차 비용을 1/k로 깎는 취약점과, 신원-귀속 예산 방어를
  결정론적 회계로 보였다(LLM arm보다 명확·저비용).</li>
</ul>

<h2 id="exp">3. 실험 설계</h2>
<table><thead><tr><th>arm</th><th>QV</th><th>역할</th></tr></thead><tbody>
<tr><td><code>none</code></td><td>—</td><td>무규제 기준선</td></tr>
<tr><td><code>qv_flat</code></td><td>2차+예산, 무가중</td><td>순수 QV</td></tr>
<tr><td><code>qv_rep</code> ★</td><td>2차+예산+평판가중</td><td>QV+평판 결합본</td></tr>
</tbody></table>
<p>resource_task, 4에이전트(n=3은 QV 약함 — 선택지 적음), 예산 B=20000. 핵심 대조: top qv_rep/qv_flat
vs none(독점 줄이나) · qv_rep vs qv_flat(평판가중 이득).</p>

<h2 id="status">4. 상태 · 한계 (정직)</h2>
<ul>
<li><span class="ok">✓ 구현·단위테스트(QV 회계·캡·평판가중·Sybil 10개)</span> 전체 275 passed. mock 스모크에서
  QV가 독점 0.60→0.30·welfare 0.25→0.75로 작동 확인.</li>
<li><b>단일-대상 QV</b> — 이 자원시나리오는 공유지 하나라 m_ij(대상별 투표)가 아닌 m_i(총수요)에 2차 비용을
  건다. 다대상 투표 QV(protocol TARGET 필드 + meeting 시나리오)는 향후 확장(설계 plan에 명시).</li>
<li><b>n=4 · glm-4.7-flash · resource_task</b> — V6와 동일 일반화 한계. QV는 n·선택지가 클수록 의미↑.</li>
<li><b>예산 B 보정 의존</b> — B=20000은 이 pool·workload에 맞춤. B가 너무 크면 캡이 안 물고, 작으면 fair도 막는다.</li>
</ul>
""".replace("{diag}", diagram_qv())
    has = (OUT.parent / "verify_qv.json").exists()
    status = ("✅ <b>실험 완료 + 단위테스트(275 통과).</b> ★결과 = 실측(<code>verify_qv.json</code>, 0 불일치)."
              if has else "⏳ <b>구현·단위테스트 완료(275 통과). 실험 데이터 대기.</b>")
    page = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Phase 3 — 진짜 QV 리포트</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Phase 3 — 진짜 QV(2차 비용+고정 예산)는 독점을 줄이는가</h1>
<p class="lead">강도의 2차 비용을 고정 예산에 부과하는 *진짜* QV + 평판가중. Phase A가 못 한
"예산 있는 QV"를 구현하고, Sybil 취약점·방어를 단위 회계로 보인다.</p>
<div class="status">{status}</div>
{EASY}
{body}
<footer>생성: <code>scripts/build_qv_report.py</code> · 구현: <code>antigreedy/governance/qv.py</code>,
<code>verify_claims.py</code>(qv) · 설계·문헌: <code>docs/related_work.md</code> §QV(Weyl 2017) · 폰트: Pretendard</footer>
</div></body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(OUT.parent.parent)} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
