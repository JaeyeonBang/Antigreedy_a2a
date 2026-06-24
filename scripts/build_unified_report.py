"""통합 리포트 빌더 — docs/verify_unified.json(run_unified 산출) → docs/unified_report.html.

단일 흐름(single flow): 모든 거버넌스 개입을 하나의 공통 baseline·하나의 모델(flash)에서 측정한
한 비교를 '무규제→단순캡→사회/평판→입력 프레이밍→평판 망각→LLM 판관→진짜 QV' 스펙트럼으로 렌더.
- BLUF(한눈 결과): Holm 보정 후 독점을 유의하게 줄인 개입 수
- 스펙트럼 표 + top_share 막대(낮을수록 좋음) + 3개 대조 가족(독점/후생/머리맞댐)
- 방법론(공통 baseline·앵커/길이 대조·bootstrap·순열검정·Holm) + 정직한 프레이밍(음성결과/방법론 목적)

표준 라이브러리만 사용. 사용:
  .venv/bin/python scripts/build_unified_report.py
"""
from __future__ import annotations

import html
import json
from pathlib import Path

SRC = Path("docs/verify_unified.json")
OUT = Path("docs/unified_report.html")

LEVER_COLOR = {"입력": "#6ea8fe", "출력": "#e6b800", "—": "#888"}


def _esc(s) -> str:
    return html.escape(str(s))


def sig_map(contrasts, prefix):
    """[{'label':'top X vs none','sig':bool},...] → {arm: (sig, p_holm, p)} for 'PREFIX arm vs none'."""
    out = {}
    for c in contrasts:
        lab = c["label"]
        if lab.startswith(prefix) and " vs none" in lab:
            arm = lab[len(prefix):].split(" vs none")[0].strip()
            out[arm] = (c["sig"], c["p_holm"], c["p"])
    return out


def bars(arms, order, key, boot_key, lower_better=True, width=560):
    """수평 막대(arm별 key 평균 + bootstrap CI 휘스커). baseline(none) 점선 기준."""
    vals = [arms[a][key] for a in order]
    vmax = max(vals + [0.001])
    base = arms["none"][key]
    row_h, pad_l = 30, 150
    h = len(order) * row_h + 24
    px = lambda v: pad_l + (v / vmax) * width
    rows = []
    for i, a in enumerate(order):
        y = 16 + i * row_h
        v = arms[a][key]
        lo, hi = arms[a][boot_key]
        good = (v <= base) if lower_better else (v >= base)
        col = "#2e9e6b" if good and a != "none" else ("#c0563b" if a != "none" and not good else "#999")
        rows.append(
            f'<text x="{pad_l-8}" y="{y+15}" text-anchor="end" class="bl">{_esc(a)}</text>'
            f'<rect x="{pad_l}" y="{y+5}" width="{(v/vmax)*width:.1f}" height="16" rx="3" fill="{col}"/>'
            f'<line x1="{px(lo):.1f}" x2="{px(hi):.1f}" y1="{y+13}" y2="{y+13}" stroke="#222" stroke-width="1.4"/>'
            f'<text x="{px(v)+6:.1f}" y="{y+17}" class="vl">{v:.3f}</text>')
    bx = px(base)
    rows.append(f'<line x1="{bx:.1f}" x2="{bx:.1f}" y1="10" y2="{h-8}" stroke="#e6b800" '
                f'stroke-width="1.3" stroke-dasharray="4 3"/>'
                f'<text x="{bx+4:.1f}" y="{h-2}" class="vl" fill="#e6b800">none={base:.3f}</text>')
    return (f'<svg viewBox="0 0 {pad_l+width+70} {h}" class="chart" role="img">'
            + "".join(rows) + "</svg>")


def fam_table(contrasts):
    rows = []
    for c in sorted(contrasts, key=lambda x: x["p_holm"]):
        tag = '<span class="sig">SIG</span>' if c["sig"] else '<span class="ns">ns</span>'
        rows.append(f'<tr><td>{tag}</td><td class="lab">{_esc(c["label"])}</td>'
                    f'<td class="num">{c["p"]:.4f}</td><td class="num">{c["p_holm"]:.4f}</td></tr>')
    return ('<table class="ct"><thead><tr><th></th><th>대조</th><th>p</th><th>p_holm</th></tr></thead>'
            '<tbody>' + "".join(rows) + "</tbody></table>")


def build() -> str:
    d = json.loads(SRC.read_text())
    cfg, arms, order = d["config"], d["arms"], d["order"]
    meta = d["meta"]
    top_sig = sig_map(d["contrasts_top"], "top ")
    wf_sig = sig_map(d["contrasts_welfare"], "welfare ")
    n_top_sig = sum(1 for _a, t in top_sig.items() if t[0])
    n_wf_sig = sum(1 for _a, t in wf_sig.items() if t[0])

    trs = []
    for a in order:
        m = meta.get(a, {"lever": "—", "mechanism": a})
        lc = LEVER_COLOR.get(m["lever"], "#888")
        ar = arms[a]
        tb, wb = ar["top_boot"], ar["comp_boot"]
        ts = top_sig.get(a, (None, None, None)); ws = wf_sig.get(a, (None, None, None))
        tmark = "" if a == "none" else (' <span class="sig">▼SIG</span>' if ts[0] else ' <span class="ns">ns</span>')
        wmark = "" if a == "none" else (' <span class="sig">SIG</span>' if ws[0] else ' <span class="ns">ns</span>')
        trs.append(
            f'<tr><td><span class="lev" style="background:{lc}1a;color:{lc};border-color:{lc}55">{_esc(m["lever"])}</span></td>'
            f'<td class="arm">{_esc(a)}</td><td class="mech">{_esc(m["mechanism"])}</td>'
            f'<td class="num">{ar["top_mean"]:.3f}<span class="ci">[{tb[0]:.3f},{tb[1]:.3f}]</span>{tmark}</td>'
            f'<td class="num">{ar["comp_mean"]:.2f}<span class="ci">[{wb[0]:.2f},{wb[1]:.2f}]</span>{wmark}</td>'
            f'<td class="num">{ar["n"]}</td></tr>')

    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>통합 거버넌스 실험 — 단일 흐름 리포트</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--gold:#e6b800;--ink:#1a1a1a;--mut:#666;--line:#e6e3dc;--bg:#faf8f3}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
 font-family:'Pretendard',-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;line-height:1.65}}
.wrap{{max-width:920px;margin:0 auto;padding:56px 28px 100px}}
h1{{font-family:'Crimson Pro',serif;font-weight:700;font-size:34px;margin:0 0 6px;letter-spacing:-.5px}}
h2{{font-family:'Crimson Pro',serif;font-weight:600;font-size:24px;margin:48px 0 14px;
 padding-bottom:8px;border-bottom:2px solid var(--ink)}}
h3{{font-size:16px;margin:26px 0 8px;color:#333}}
.sub{{color:var(--mut);font-size:15px;margin:0 0 8px}}
.bluf{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--gold);
 border-radius:10px;padding:20px 22px;margin:22px 0}}
.bluf b{{color:#000}}
.big{{font-size:30px;font-family:'Crimson Pro',serif;font-weight:700;color:var(--gold)}}
table{{width:100%;border-collapse:collapse;margin:10px 0;font-size:13.5px;background:#fff;
 border:1px solid var(--line);border-radius:8px;overflow:hidden}}
th,td{{padding:9px 11px;text-align:left;border-bottom:1px solid var(--line)}}
th{{background:#f3f0e8;font-weight:600;font-size:12px;color:#555;text-transform:uppercase;letter-spacing:.4px}}
td.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
td.arm{{font-weight:600;font-family:ui-monospace,monospace}}
td.mech{{color:#444}} td.lab{{font-size:12.5px}}
.ci{{color:#aaa;font-size:11px;margin-left:5px}}
.lev{{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11px;font-weight:700;border:1px solid}}
.sig{{color:#2e9e6b;font-weight:700;font-size:11px}}
.ns{{color:#b08;opacity:.6;font-size:11px}}
.chart{{width:100%;height:auto;background:#fff;border:1px solid var(--line);border-radius:8px;padding:8px 4px;margin:8px 0}}
.chart .bl{{font:600 12px ui-monospace,monospace;fill:#333}}
.chart .vl{{font:11px ui-monospace,monospace;fill:#777}}
.easy{{background:#eef7f0;border:1px solid #cfe6d6;border-radius:8px;padding:12px 16px;margin:14px 0;font-size:14px}}
.easy b{{color:#2e7d4f}}
.note{{font-size:13px;color:var(--mut);margin-top:6px}}
code{{background:#efece4;padding:1px 6px;border-radius:4px;font-size:12.5px}}
.foot{{margin-top:60px;padding-top:18px;border-top:1px solid var(--line);color:#999;font-size:12.5px}}
ul{{font-size:14.5px}} li{{margin:5px 0}}
</style></head><body><div class="wrap">

<h1>통합 거버넌스 실험 — 단일 흐름 리포트</h1>
<p class="sub">모든 개입을 <b>하나의 공통 baseline·하나의 모델({_esc(cfg['model'])})·하나의 설정</b>에서
측정한 단일 비교 · N={cfg['seeds']} 시드 · {cfg['agents']}에이전트 · {cfg['rounds']}라운드 · 공유풀 {cfg['pool']}</p>

<div class="bluf">
<p style="margin:0 0 8px"><b>한눈에(BLUF).</b> 11개 거버넌스 개입을 한 줄의 스펙트럼
(무규제 → 단순 캡 → 사회·평판 → 입력 프레이밍 → 평판 망각 → LLM 판관 → 진짜 QV) 위에 놓고
공통 baseline(<code>none</code>)과 비교했다.</p>
<p style="margin:0">독점(top_share)을 Holm 보정 후 <b>유의하게</b> 줄인 개입:
<span class="big">{n_top_sig}</span> / 10 &nbsp;·&nbsp; 후생(welfare)을 유의하게 바꾼 개입:
<span class="big">{n_wf_sig}</span> / 10.
이 리포트의 목적은 '작동하는 거버넌스 발견'이 아니라 <b>통제된 비교 방법론으로 각 개입의 효과가
진짜인지 아티팩트인지 가르는 것</b>이다 — 음성 결과도 동등한 기여다.</p>
</div>

<div class="easy"><b>💡 쉽게.</b> 같은 출발선(아무 규제 없는 <code>none</code>)에서 11가지 규제 방식을
하나씩 켜 보고, 독점(<code>top_share</code>: 한 에이전트가 가져간 자원 비율, <b>낮을수록 공평</b>)과
후생(<code>welfare</code>: 전원이 각자 과제를 끝낸 비율, <b>높을수록 좋음</b>)이 통계적으로 의미 있게
바뀌는지를 본다. '의미 있다'의 기준은 여러 번 비교할 때 생기는 운(다중검정)을 Holm 보정으로 깎아낸 뒤의
값(<code>p_holm</code> &lt; 0.05)이다.</div>

<h2>1. 단일 흐름 — 전체 스펙트럼</h2>
<p class="sub">왼쪽 <span class="lev" style="background:#6ea8fe1a;color:#6ea8fe;border-color:#6ea8fe55">입력</span>=프롬프트를
바꾸는 개입(행동 채널), <span class="lev" style="background:#e6b8001a;color:#e6b800;border-color:#e6b80055">출력</span>=요청을
가로채 캡/거부하는 개입. <b>효과 스펙트럼</b>(약한 개입→정교한 개입) 순으로 정렬했다.
▼SIG=해당 개입이 독점을 유의하게 낮춤.</p>
<table><thead><tr><th>레버</th><th>조건</th><th>기제</th><th>top_share ↓</th><th>welfare ↑</th><th>n</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table>

<h3>독점(top_share) — 낮을수록 공평 · 점선=무규제 기준</h3>
{bars(arms, order, 'top_mean', 'top_boot', lower_better=True)}

<h3>후생(welfare) — 높을수록 좋음 · 점선=무규제 기준</h3>
{bars(arms, order, 'comp_mean', 'comp_boot', lower_better=False)}

<h2>2. 대조 검정 — 1차: 독점 각 개입 vs 무규제</h2>
<p class="sub">1차 가족: 각 개입이 무규제 대비 독점을 바꾸나? 순열검정(정규성 가정 없음) → Holm 보정.</p>
{fam_table(d['contrasts_top'])}

<h2>3. 대조 검정 — 2차: 후생 각 개입 vs 무규제</h2>
{fam_table(d['contrasts_welfare'])}

<h2>4. 대조 검정 — 탐색: 정교한 개입이 단순한 것보다 나은가</h2>
<p class="sub">평판가중 QV vs 무가중 QV, QV vs 단순캡, 평판 vs 단순캡, 망각 vs 누적,
LLM 판관 vs 규칙. 정교함이 추가 신호를 주는지의 머리맞댐(별도 Holm 가족).</p>
{fam_table(d['contrasts_heads'])}

<h2>5. 방법론과 정직한 해석</h2>
<p>모든 arm은 <b>동일한 무규제 baseline</b>에서 분기하며, 같은 모델(<code>{_esc(cfg['model'])}</code>)·
같은 {cfg['agents']}에이전트·같은 공유풀({cfg['pool']})·같은 {cfg['rounds']}라운드를 공유한다.
이전에는 V6(독점·후생 통제실험)이 GLM-4.6, BCDE 확장(망각·판관·QV)이 flash로 모델이 달라
직접 비교가 불가능했으나, 본 실험은 <b>전부 flash로 재측정</b>해 한 흐름에 합쳤다.</p>
<ul>
<li><b>앵커/길이 대조군</b>(<code>fairshare_anchor</code>, <code>neutral_filler</code>): 입력 프레이밍의
효과가 '공정성 내용' 때문인지 단지 '프롬프트가 길어져서'인지를 가른다.</li>
<li><b>bootstrap 95% CI</b>: 평균의 불확실성을 원자료 재표집으로 추정(정규성 가정 없음).</li>
<li><b>순열검정 + Holm</b>: 두 표본 평균차의 양측 p를 셔플로 구하고, 여러 대조를 동시에 볼 때의
거짓양성을 Holm–Bonferroni로 보정.</li>
</ul>
<div class="easy"><b>💡 왜 음성 결과가 기여인가.</b> "이 규제가 독점을 줄였다"는 주장은 흔하지만,
대부분 <b>대조군 없이</b> 측정돼 '프롬프트가 길어진 효과'나 '운'과 구별되지 않는다. 본 실험은 그 구별을
강제한다 — 통제하면 대부분의 개입 효과가 사라진다는 것 자체가, 이 분야가 더 엄격한 검정을 필요로 한다는
증거다.</div>

<p class="note">범위: 모든 결과는 {_esc(cfg['model'])} 기준이며 다른 모델로의 일반화를 주장하지 않는다.
n={cfg['agents']}는 QV 같은 메커니즘에는 작은 편(검정력 한계)이라 머리맞댐 가족의 음성 결과는
'효과 없음'이 아니라 '이 규모에서 미검출'로 읽어야 한다.</p>

<div class="foot">생성: <code>scripts/build_unified_report.py</code> ← <code>docs/verify_unified.json</code>
(<code>scripts/verify_claims.py unified</code>) · Antigreedy A2A</div>
</div></body></html>"""


if __name__ == "__main__":
    OUT.write_text(build())
    print(f"wrote {OUT} ({len(OUT.read_text())} bytes)")
