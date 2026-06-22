#!/usr/bin/env python3
"""논문(한국어) + V6 실험 데이터 → 단일 HTML 리포트.

기존 프로젝트 파일을 재활용한다:
  - 본문:   docs/paper_draft_ko.md  (자연스러운 한국어 번역본)
  - 데이터: docs/verify_v6.json     (원시 반복별 결과 — 차트는 여기서 그려짐)
  - 스타일: antigreedy/dashboard/static/theater.html 의 다크 테마 토큰

출력:     docs/paper_report.html   (완전 자립형 · 오프라인 열람 가능, 외부 의존 0)

차트는 데이터에서 SVG로 직접 생성하므로 JSON이 바뀌면 다시 실행만 하면 된다:
    .venv/bin/python scripts/build_paper_html.py
"""
from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "docs" / "paper_draft_ko.md"
DATA = ROOT / "docs" / "verify_v6.json"
OUT = ROOT / "docs" / "paper_report.html"

# 한국어 라벨 + 색 의미(대시보드 팔레트와 동일 계열)
ARM_LABEL = {
    "none": "none · 무규제",
    "dumb_cap": "dumb_cap · 더미 캡",
    "social": "social · 평판+배제",
    "reputation_feedback": "reputation_feedback · 평판 되먹임",
    "superordinate": "superordinate · 상위 정체성",
    "fairshare_anchor": "fairshare_anchor · 앵커 대조",
    "neutral_filler": "neutral_filler · 무내용 대조",
}
ARM_ORDER = list(ARM_LABEL)
LAYER = {  # 출력측 vs 입력측 vs 무규제
    "none": "base", "dumb_cap": "out", "social": "out",
    "reputation_feedback": "in", "superordinate": "in",
    "fairshare_anchor": "ctrl", "neutral_filler": "ctrl",
}
LAYER_COLOR = {"base": "#6e7b8a", "out": "#f85149", "in": "#1f6feb", "ctrl": "#8b949e"}


# ───────────────────────── 차트 (SVG, 데이터 기반) ─────────────────────────
def _bar_chart(arms, key_mean, key_boot, title, sub, *, lower_is_better,
               highlight, baseline_arm="none"):
    """세로 막대 + bootstrap 95% CI whisker. highlight=강조할 arm 집합."""
    W, H = 760, 340
    pad_l, pad_r, pad_t, pad_b = 48, 16, 18, 96
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b
    n = len(arms)
    slot = plot_w / n
    bar_w = slot * 0.52

    def y(v):  # 값 0..1 → 픽셀
        return pad_t + plot_h * (1 - v)

    parts = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" '
             f'aria-label="{html.escape(title)}">']
    for g in (0, 0.25, 0.5, 0.75, 1.0):
        gy = y(g)
        parts.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{W-pad_r}" y2="{gy:.1f}" '
                     f'class="grid"/>')
        parts.append(f'<text x="{pad_l-6}" y="{gy+3:.1f}" class="ytick">{g:.2f}</text>')
    base_v = next(a[key_mean] for a in arms if a["name"] == baseline_arm)
    by = y(base_v)
    parts.append(f'<line x1="{pad_l}" y1="{by:.1f}" x2="{W-pad_r}" y2="{by:.1f}" '
                 f'class="baseline"/>')
    parts.append(f'<text x="{W-pad_r}" y="{by-5:.1f}" class="baselbl" '
                 f'text-anchor="end">none 기준 {base_v:.2f}</text>')

    for i, a in enumerate(arms):
        cx = pad_l + slot * i + slot / 2
        x = cx - bar_w / 2
        mean = a[key_mean]
        lo, hi = a[key_boot]
        col = LAYER_COLOR[LAYER[a["name"]]]
        is_hi = a["name"] in highlight
        opacity = "1" if is_hi else "0.45"
        parts.append(f'<rect x="{x:.1f}" y="{y(mean):.1f}" width="{bar_w:.1f}" '
                     f'height="{(y(0)-y(mean)):.1f}" rx="3" fill="{col}" '
                     f'fill-opacity="{opacity}"/>')
        parts.append(f'<line x1="{cx:.1f}" y1="{y(lo):.1f}" x2="{cx:.1f}" '
                     f'y2="{y(hi):.1f}" class="whisk"/>')
        for yy in (lo, hi):
            parts.append(f'<line x1="{cx-5:.1f}" y1="{y(yy):.1f}" x2="{cx+5:.1f}" '
                         f'y2="{y(yy):.1f}" class="whisk"/>')
        parts.append(f'<text x="{cx:.1f}" y="{y(hi)-6:.1f}" class="val" '
                     f'text-anchor="middle">{mean:.2f}</text>')
        if is_hi:
            parts.append(f'<text x="{cx:.1f}" y="{y(hi)-19:.1f}" class="star" '
                         f'text-anchor="middle">★</text>')
        parts.append(f'<text x="{cx:.1f}" y="{H-pad_b+14:.1f}" class="xtick" '
                     f'text-anchor="end" transform="rotate(-35 {cx:.1f} '
                     f'{H-pad_b+14:.1f})">{html.escape(a["name"])}</text>')

    arrow = "↓ 낮을수록 좋음" if lower_is_better else "↑ 높을수록 좋음"
    parts.append('</svg>')
    return (f'<figure class="fig"><figcaption><b>{html.escape(title)}</b>'
            f'<span class="dir">{arrow}</span><br><span class="sub">'
            f'{html.escape(sub)}</span></figcaption>{"".join(parts)}</figure>')


def _contrast_chart(contrasts):
    """9개 대조를 -log10(p_holm) 막대로. 임계선 -log10(.05)=1.30 을 넘으면 생존."""
    thr = -math.log10(0.05)
    maxv = max((-math.log10(max(c["p_holm"], 1e-6)) for c in contrasts), default=3)
    maxv = max(maxv, thr + 0.5)
    W = 760
    bararea = 350
    lblarea = 300
    rowh = 30
    H = rowh * len(contrasts) + 34
    x0 = lblarea + 10
    parts = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" '
             f'aria-label="대조별 유의성">']
    tx = x0 + bararea * (thr / maxv)
    parts.append(f'<line x1="{tx:.1f}" y1="6" x2="{tx:.1f}" y2="{H-22}" class="thr"/>')
    parts.append(f'<text x="{tx:.1f}" y="{H-8}" class="thrlbl" text-anchor="middle">'
                 f'p_holm=.05 임계</text>')
    for i, c in enumerate(contrasts):
        cy = 8 + i * rowh
        val = -math.log10(max(c["p_holm"], 1e-6))
        w = bararea * (val / maxv)
        col = "#3fb950" if c["sig"] else "#39414d"
        parts.append(f'<text x="{lblarea}" y="{cy+rowh/2+4:.1f}" class="clbl" '
                     f'text-anchor="end">{html.escape(c["label"])}</text>')
        parts.append(f'<rect x="{x0}" y="{cy+5:.1f}" width="{max(w,1):.1f}" '
                     f'height="{rowh-12}" rx="3" fill="{col}"/>')
        tag = f'p_holm={c["p_holm"]:.3f}' if c["p_holm"] < 0.999 else "p_holm≈1.0"
        mark = "✅ 생존" if c["sig"] else "ns"
        parts.append(f'<text x="{x0+max(w,1)+8:.1f}" y="{cy+rowh/2+4:.1f}" '
                     f'class="ctag">{mark} · {tag}</text>')
    parts.append('</svg>')
    return (f'<figure class="fig wide"><figcaption><b>그림 3. 9개 사전 대조의 '
            f'다중보정(Holm) 유의성</b><br><span class="sub">막대가 길수록 유의. '
            f'초록 임계선을 넘은 2개만 살아남는다.</span></figcaption>'
            f'{"".join(parts)}</figure>')


def build_charts(data):
    arms = [data["arms"][k] for k in ARM_ORDER]
    welfare = _bar_chart(
        arms, "comp_mean", "comp_boot",
        "그림 1. arm별 welfare(완료율)", "막대=평균, whisker=bootstrap 95% CI · N=30",
        lower_is_better=False, highlight={"neutral_filler", "social"})
    top = _bar_chart(
        arms, "top_mean", "top_boot",
        "그림 2. arm별 top-share(독점)", "막대=평균, whisker=bootstrap 95% CI · N=30",
        lower_is_better=True, highlight={"superordinate"})
    contrasts = _contrast_chart(data["contrasts"])
    legend = (
        '<div class="clegend">'
        '<span><i style="background:#6e7b8a"></i>무규제(none)</span>'
        '<span><i style="background:#f85149"></i>출력측 정책</span>'
        '<span><i style="background:#1f6feb"></i>입력측 셰이퍼</span>'
        '<span><i style="background:#8b949e"></i>대조군</span>'
        '<span class="star">★</span>=Holm 생존/주목 효과'
        '</div>')
    return (f'<section class="viz"><h2 class="vh">실험 결과 한눈에 보기 '
            f'(V6 · GLM-4.6 · N=30)</h2>{legend}'
            f'<div class="grid2">{welfare}{top}</div>{contrasts}</section>')


# ───────────────────── 대시보드 연동 위젯 (라이브 · 히스토리) ─────────────────────
# 대시보드(FastAPI)에서 /report 로 서빙되면 같은 출처의 /history 를 직접 읽어
# 과거 run 노드를 나열하고 각 run 의 export.html 로 연결한다. file:// 로 열면
# 서버가 없으므로 안내만 표시한다(우아한 강등).
DASHBOARD_WIDGET = """
<section class="dash" id="dash">
  <p class="dnote">이 리포트의 V6 수치는 배치 스크립트(<code>scripts/verify_claims.py</code>)에서
  나온 것이고, 아래 <b>라이브/히스토리</b>는 대시보드에서 사람이 직접 돌린 A/B run 들이다.
  같은 <code>resource-task</code> 시나리오·같은 출력/입력 레버를 쓰므로, 표의 각 조건을
  <b>직접 눈으로 재현</b>해 볼 수 있다.</p>
  <div class="dbtns">
    <a class="dbtn live" href="/" target="_blank" rel="noopener">▶ 라이브 시어터 열기 (A/B 실행)</a>
    <a class="dbtn" href="/governance" target="_blank" rel="noopener">거버넌스 설명</a>
    <a class="dbtn" href="/history" target="_blank" rel="noopener">/history (원시 JSON)</a>
  </div>
  <h3 class="dh">과거 실험 노드 (히스토리)</h3>
  <div id="dhist" class="dhist"><span class="dhint">불러오는 중…</span></div>
</section>
<script>
(function(){
  var box = document.getElementById('dhist');
  if (location.protocol === 'file:') {
    box.innerHTML = '<span class="dhint">📁 지금은 파일로 열려 있어 히스토리를 못 가져옵니다. '
      + '대시보드 서버에서 <code>/report</code> 로 열면 과거 run 이 여기에 직접 연결됩니다 '
      + '(<code>python -m antigreedy.dashboard</code>).</span>';
    return;
  }
  fetch('/history').then(function(r){return r.json();}).then(function(d){
    var runs = (d && d.runs) || [];
    if (!runs.length){ box.innerHTML = '<span class="dhint">아직 저장된 run 이 없습니다. '
      + '라이브 시어터에서 한 번 실행하면 여기에 노드로 쌓입니다.</span>'; return; }
    var html = '<table class="dtab"><thead><tr><th>run id</th><th>mode</th>'
      + '<th>요약</th><th>열기</th></tr></thead><tbody>';
    runs.forEach(function(run){
      var s = run.summary || {};
      var parts = [];
      if (s.top_share != null) parts.push('top ' + Number(s.top_share).toFixed(2));
      if (s.completion_rate != null) parts.push('welfare ' + Number(s.completion_rate).toFixed(2));
      html += '<tr><td><code>' + (run.id||'') + '</code></td><td>' + (run.mode||'-')
        + '</td><td>' + (parts.join(' · ') || '-') + '</td>'
        + '<td><a href="/history/' + encodeURIComponent(run.id)
        + '/export.html" target="_blank" rel="noopener">▶ 리플레이</a></td></tr>';
    });
    box.innerHTML = html + '</tbody></table>';
  }).catch(function(){
    box.innerHTML = '<span class="dhint">히스토리 엔드포인트(/history)에 연결하지 못했습니다.</span>';
  });
})();
</script>
"""


# ───────────────────────── 초경량 Markdown → HTML ─────────────────────────
# 순서 중요: 링크 먼저(원문 인용 연결) → code → bold → italic.
_INLINE = [
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),
     r'<a href="\2" target="_blank" rel="noopener">\1</a>'),
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)"), r"<em>\1</em>"),
]


def _inline(text):
    out = html.escape(text)
    for pat, rep in _INLINE:
        out = pat.sub(rep, out)
    return out


def _table(rows):
    head = rows[0]
    body = rows[2:]  # rows[1] = 구분선
    cells_h = [c.strip() for c in head.strip().strip("|").split("|")]
    th = "".join(f"<th>{_inline(c)}</th>" for c in cells_h)
    trs = []
    for r in body:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        win = any("✅" in c for c in cells)
        cls = ' class="win"' if win else ""
        tds = "".join(f"<td>{_inline(c)}</td>" for c in cells)
        trs.append(f"<tr{cls}>{tds}</tr>")
    return f'<table><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table>'


def md_to_html(md):
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):  # 펜스 코드블록 (수식/알고리즘)
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # 닫는 ``` 소비
            out.append(f"<pre><code>{html.escape(chr(10).join(buf))}</code></pre>")
            continue
        if s == "---":
            out.append("<hr>")
            i += 1
            continue
        if s.startswith(">"):  # 블록인용 → 용어/주의 callout
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            inner = "<br>".join(_inline(b) if b else "" for b in buf)
            out.append(f'<blockquote>{inner}</blockquote>')
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", s)
        if m:
            lv = len(m.group(1))
            out.append(f"<h{lv}>{_inline(m.group(2))}</h{lv}>")
            i += 1
            continue
        if s.startswith("|"):  # 표 블록
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            out.append(_table(block))
            continue
        if re.match(r"^(\d+\.|[-*])\s+", s):  # 리스트
            ol = bool(re.match(r"^\d+\.", s))
            tag = "ol" if ol else "ul"
            items = []
            while i < len(lines) and re.match(r"^(\d+\.|[-*])\s+", lines[i].strip()):
                item = re.sub(r"^(\d+\.|[-*])\s+", "", lines[i].strip())
                items.append(f"<li>{_inline(item)}</li>")
                i += 1
            out.append(f"<{tag}>{''.join(items)}</{tag}>")
            continue
        out.append(f"<p>{_inline(s)}</p>")
        i += 1
    return "\n".join(out)


CSS = """
:root{--bg:#0e1116;--panel:#161b22;--ink:#e6edf3;--mut:#9aa6b2;--line:#21262d;
      --ok:#3fb950;--bad:#f85149;--blue:#1f6feb;--card:#0d1117;}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.7 system-ui,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;}
.wrap{max-width:980px;margin:0 auto;padding:34px 22px 80px;}
h1{font-size:25px;line-height:1.35;margin:0 0 6px;}
h2{font-size:19px;margin:30px 0 8px;border-bottom:1px solid var(--line);padding-bottom:6px;}
h3{font-size:16px;margin:22px 0 6px;color:#cdd9e5;}
h4{font-size:14px;margin:16px 0 4px;color:var(--mut);}
p{margin:9px 0;}
em{color:#cdd9e5;font-style:italic;}
strong{color:#fff;}
code{background:var(--card);border:1px solid #2a3340;border-radius:5px;
  padding:1px 6px;font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#a5d6ff;}
pre{background:#0a0d12;border:1px solid #2a3340;border-radius:8px;padding:13px 15px;
  overflow-x:auto;margin:12px 0;}
pre code{background:none;border:0;padding:0;color:#cdd9e5;font-size:12.5px;line-height:1.6;}
hr{border:0;border-top:1px solid var(--line);margin:24px 0;}
a{color:#58a6ff;text-decoration:none;}
a:hover{text-decoration:underline;}
blockquote{margin:14px 0;padding:12px 15px;background:var(--card);
  border:1px solid #2a3340;border-left:3px solid #d29922;border-radius:8px;
  color:#cdd9e5;font-size:13.5px;line-height:1.65;}
blockquote strong{color:#fff;}
/* 대시보드 연동 */
.dash{background:var(--card);border:1px solid #2a3340;border-radius:12px;
  padding:16px 18px 20px;margin:18px 0;}
.dnote{font-size:13px;color:var(--mut);margin:2px 0 12px;}
.dbtns{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:14px;}
.dbtn{background:#161b22;border:1px solid #30363d;border-radius:7px;
  padding:8px 14px;font-size:13px;color:var(--ink);font-weight:600;}
.dbtn:hover{background:#1b222c;text-decoration:none;}
.dbtn.live{background:#1f6feb;border-color:#1f6feb;color:#fff;}
.dh{font-size:14px;color:#cdd9e5;margin:6px 0 8px;}
.dhist{font-size:13px;}
.dhint{color:#6e7b8a;}
.dtab{width:100%;border-collapse:collapse;font-size:12.5px;}
.dtab th,.dtab td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;}
.dtab th{background:#11161d;color:#fff;}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13.5px;
  background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden;}
th,td{padding:8px 11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;}
th{background:#11161d;color:#fff;font-weight:700;}
tr:last-child td{border-bottom:0;}
tr.win td{background:rgba(63,185,80,.09);}
ul,ol{margin:9px 0;padding-left:22px;}
li{margin:4px 0;}
.status{background:var(--card);border:1px solid #2a3340;border-left:3px solid var(--blue);
  border-radius:8px;padding:11px 14px;font-size:13px;color:var(--mut);margin:14px 0;}
.viz{background:var(--card);border:1px solid #2a3340;border-radius:12px;
  padding:18px 18px 22px;margin:22px 0;}
.vh{font-size:17px;margin:2px 0 12px;border:0;padding:0;color:#fff;}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
@media(max-width:820px){.grid2{grid-template-columns:1fr;}}
.fig{margin:0;background:var(--panel);border:1px solid var(--line);
  border-radius:10px;padding:12px 12px 6px;}
.fig.wide{margin-top:16px;}
figcaption{font-size:12.5px;color:var(--mut);margin-bottom:6px;}
figcaption b{color:#fff;font-size:13px;}
figcaption .dir{float:right;color:#8b949e;font-size:11.5px;}
figcaption .sub{color:#6e7b8a;font-size:11.5px;}
.chart{width:100%;height:auto;}
.grid{stroke:#1b212a;stroke-width:1;}
.baseline{stroke:#6e7b8a;stroke-width:1.4;stroke-dasharray:4 3;}
.baselbl{fill:#6e7b8a;font-size:10.5px;}
.ytick{fill:#6e7b8a;font-size:10px;text-anchor:end;}
.xtick{fill:#9aa6b2;font-size:10.5px;}
.whisk{stroke:#c9d1d9;stroke-width:1.4;}
.val{fill:#e6edf3;font-size:11px;font-weight:700;}
.star{fill:#d29922;font-size:13px;font-weight:700;}
.clbl{fill:#c9d1d9;font-size:11.5px;}
.ctag{fill:#9aa6b2;font-size:11px;}
.thr{stroke:#3fb950;stroke-width:1.4;stroke-dasharray:3 3;}
.thrlbl{fill:#3fb950;font-size:10.5px;}
.clegend{display:flex;flex-wrap:wrap;gap:14px;align-items:center;font-size:12px;
  color:var(--mut);margin-bottom:12px;}
.clegend i{display:inline-block;width:12px;height:12px;border-radius:3px;
  vertical-align:-1px;margin-right:5px;}
.clegend .star{color:#d29922;font-weight:700;}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);
  color:#6e7b8a;font-size:12px;}
"""


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    md = MD.read_text(encoding="utf-8")
    body = md_to_html(md)
    charts = build_charts(data)

    marker = "<h2>5. 결과</h2>"
    if marker in body:
        body = body.replace(marker, marker + "\n" + charts, 1)
    else:
        body = charts + body

    # 대시보드 연동 위젯을 부록 B 자리표시자에 주입
    if "<p>DASHBOARD_WIDGET</p>" in body:
        body = body.replace("<p>DASHBOARD_WIDGET</p>", DASHBOARD_WIDGET, 1)

    cfg = data["config"]
    meta = (f'모델 {cfg["model"]} · 온도 {cfg["temp"]} · 에이전트 {len(cfg["agents"])} · '
            f'풀 {cfg["pool"]} · {cfg["rounds"]}라운드 · N={cfg["seeds"]}')
    page = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Antigreedy — 논문 리포트 (V6)</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<div class="status">📄 자동 생성 리포트 · 본문 <code>docs/paper_draft_ko.md</code> +
데이터 <code>docs/verify_v6.json</code> · 차트는 원자료에서 직접 렌더 · {html.escape(meta)}</div>
{body}
<footer>생성: <code>scripts/build_paper_html.py</code> ·
모든 수치는 <code>docs/verify_v6.json</code> 원시 반복별 배열에서 산출 ·
재현: <code>.venv/bin/python scripts/build_paper_html.py</code></footer>
</div></body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
