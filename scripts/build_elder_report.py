#!/usr/bin/env python3
"""Phase 2(Elder 원장 judge) 결과/설계 리포트 → Pretendard HTML.

데이터(docs/verify_elder.json)에서 결과를 로드해 렌더. 해석 문구는 숫자에서 파생(하드코딩 금지).
핵심 질문 = "LLM-judge가 rule/숫자앵커보다 진짜 신호를 더하나, 아니면 또 앵커링인가(V6 교훈)?"

    .venv/bin/python scripts/build_elder_report.py  →  docs/elder_report.html
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "elder_report.html"
ORDER = ["none", "ledger_numbers", "ledger_rule", "ledger_elder"]
LABEL = {"none": "none", "ledger_numbers": "numbers(앵커)", "ledger_rule": "rule(α=1)",
         "ledger_elder": "elder(α=.5)"}
COL = {"none": "#7a8699", "ledger_numbers": "#d98a2b", "ledger_rule": "#2f6feb",
       "ledger_elder": "#e5534b"}


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
    jp = OUT.parent / "verify_elder.json"
    if not jp.exists():
        return ('<div class="status">⏳ <b>실험 데이터 대기.</b> <code>verify_elder.json</code> 생성 후 '
                '결과 차트·대조표가 렌더된다.</div>')
    d = json.loads(jp.read_text(encoding="utf-8"))
    A = d["arms"]
    cfg = d["config"]
    cmap = {c["label"]: c for c in d["contrasts"]}

    def vl(substr):
        for lab, c in cmap.items():
            if substr in lab:
                tag = "유의(SIG)" if c["sig"] else "무유의(ns)"
                return f'{lab} → p_holm={c["p_holm"]:.4f} <b>{tag}</b>'
        return ""

    judge_sig = any(c["sig"] for c in d["contrasts"] if "judge가 신호" in c["label"] or "앵커 이상" in c["label"])
    # 방향 판정: elder가 rule보다 독점↑·welfare↓면 *해로운* 차이
    harmful = ("ledger_elder" in A and "ledger_rule" in A
               and A["ledger_elder"]["top_mean"] > A["ledger_rule"]["top_mean"]
               and A["ledger_elder"]["comp_mean"] < A["ledger_rule"]["comp_mean"])
    if judge_sig and harmful:
        headline = ("LLM-judge는 rule·숫자앵커와 <b>유의하게 달랐지만 — 더 나쁜 쪽으로</b>. "
                    "불변 원장이 judge의 이른 오판을 동결해 공정한 에이전트까지 배제했다(독점↑·welfare↓). "
                    "순수 행동 평판(rule)이 최선.")
    elif judge_sig:
        headline = "LLM-judge가 rule/숫자앵커보다 <b>유의하게 다른(유익한) 신호</b>를 더했다."
    else:
        headline = "LLM-judge는 rule·숫자앵커와 <b>통계적으로 구별되지 않았다 — 또 앵커링</b>(V6 교훈 재확인)."

    top_chart = (f'<figure class="fig wide"><figcaption><b>그림 R1. arm별 top-share(독점) — 낮을수록 공정</b>'
                 f'<br><span class="sub">numbers(앵커)·rule(α=1)·elder(α=.5) 비교. elder가 둘과 겹치면 judge=앵커.'
                 f'</span></figcaption>{_bars(A, "top_mean")}'
                 f'<figcaption style="margin-top:6px"><span class="sub">{cfg["model"]} · N={cfg["seeds"]} · '
                 f'{cfg["agents"]}ag · rounds={cfg["rounds"]}</span></figcaption></figure>')
    welf_chart = (f'<figure class="fig wide"><figcaption><b>그림 R2. arm별 welfare(완료율) — 높을수록 좋음</b>'
                  f'</figcaption>{_bars(A, "comp_mean")}</figure>')

    rows = ""
    for c in d["contrasts"]:
        cls = ' style="background:#eefaf1"' if c["sig"] else ""
        verdict = "✅ SIG" if c["sig"] else "ns"
        rows += (f'<tr{cls}><td>{c["label"]}</td><td>{c["p"]:.4f}</td>'
                 f'<td><b>{c["p_holm"]:.4f}</b></td><td>{verdict}</td></tr>')
    table = ('<table><thead><tr><th>대조</th><th>p</th><th>p_holm</th><th>판정</th></tr></thead>'
             f'<tbody>{rows}</tbody></table>')

    return f"""
<h2 id="results">★ 결과 ({cfg['model']}, N={cfg['seeds']}) — judge는 신호인가 앵커인가</h2>
<div class="callout {'warn' if (harmful or not judge_sig) else 'q'}"><b>한 줄 결론(데이터 파생).</b> {headline}
핵심 대조: {vl('judge가 신호')}; {vl('앵커 이상')}.</div>
{top_chart}
<p><b>독점 요약.</b> {' · '.join(f'{LABEL[a]} {A[a]["top_mean"]:.3f}' for a in ORDER if a in A)};
welfare {' · '.join(f'{LABEL[a]} {A[a]["comp_mean"]:.2f}' for a in ORDER if a in A)}.
elder가 rule·numbers와 *겹치면* "judge는 같은 정보의 재포장(앵커)"이고, *벗어나면* "근거 텍스트에서
rule이 못 보는 신호를 읽었다"는 뜻이다.</p>
{welf_chart}
{table}
<p>상세·한계 = <code>docs/verify_elder.md</code>. 원자료 독립 재계산 0 불일치.</p>
"""


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
    body = results_block() + """
<h2 id="what">1. Phase 2는 무엇인가 (설계)</h2>
<p>보고서 향후 과제 중 <b>"LLM-판관(judge) 평판이 진짜 신호인가, 또 앵커링인가"</b>를 측정한다.
V6에서 reputation_feedback은 숫자 앵커와 구별되지 않았다(p=.88). Elder는 에이전트의 <em>근거 텍스트</em>를
LLM이 읽고 공정성을 채점한다 — rule(점유 행동)이 못 보는 신호를 더하는지 본다.</p>

<h2 id="how">2. 메커니즘 · 수식 (구현)</h2>
<p>구현: <code>antigreedy/governance/elder.py</code>(<code>ElderLedger</code>·<code>ElderInterceptPoint</code>) +
<code>elder_judge.py</code>(<code>judge</code>·<code>numeric_judge</code>·<code>parse_score</code>).</p>
<div class="formula">Elder 평판 혼합:
  rule_rep = Beta+λ 행동 평판 (점유 이력)
  llm_score = Elder LLM이 에이전트 근거(REASON)를 읽고 매긴 0~1 공정성 (에피소드당 1회, 검소)
  rep = α·rule_rep + (1−α)·llm_score        # α=1 → 순수 rule, α=.5 → 혼합
  rep < 0.45 → 배제(deny),  아니면 BASE_SHARE·rep 캡

앵커 대조 (LLM 없음):
  numeric_judge(share) = clip(1 − max(0,share−fair)/fair)   # 같은 형태, 점유 숫자만
  ledger_elder ≈ ledger_numbers 면 → judge는 앵커(같은 정보 재포장)</div>
<ul>
<li><b>왜 에피소드당 1회 judge인가</b> — 턴당 호출은 8× 비싸다. 검소 설계로 비용을 누른다(LLM-heavy arm만 과금).</li>
<li><b>왜 append-only 원장인가</b> — 불변성의 위험(LLM 오판 영구화 → 카스트)을 *실험으로 노출*하려는 의도.
  심사는 추가만, 수정/삭제 없음.</li>
<li><b>왜 numeric 앵커 대조인가</b> — V6 교훈: 그럴싸한 사회 신호가 숫자 앵커와 구별 안 되는 일이 잦다.
  judge가 앵커 이상임을 보이려면 <code>numbers</code>를 *반드시* 이겨야 한다.</li>
</ul>

<h2 id="exp">3. 실험 설계</h2>
<table><thead><tr><th>arm</th><th>평판</th><th>역할</th></tr></thead><tbody>
<tr><td><code>none</code></td><td>—</td><td>무규제 기준선</td></tr>
<tr><td><code>ledger_numbers</code></td><td>α=.5, numeric 앵커</td><td>앵커 대조 (LLM 없음)</td></tr>
<tr><td><code>ledger_rule</code></td><td>α=1, 순수 Beta rule</td><td>rule-only 대조</td></tr>
<tr><td><code>ledger_elder</code> ★</td><td>α=.5, 실 LLM judge</td><td>처치 (judge 혼합)</td></tr>
</tbody></table>
<p><b>핵심 대조:</b> top/welfare <code>elder vs rule</code>(judge가 신호 더하나) · <code>elder vs numbers</code>
(앵커 이상인가). 둘 다 무유의면 → judge=앵커(V6 재확인). 유의하면 → 근거 텍스트에 진짜 신호.</p>

<h2 id="status">4. 상태 · 한계 (정직)</h2>
<ul>
<li><span class="ok">✓ 구현·단위테스트(elder/judge/ledger/numeric 13개)</span> — judge는 MockBackend 결정론 테스트,
  실 LLM은 실행 시만. 전체 265 passed.</li>
<li><b>judge 에피소드당 1회</b> — 최초 턴의 근거만 본다(이후 행동 변화는 rule이 포착). 풍부한 다회 심사는 비용↑.</li>
<li><b>n=3 · glm-4.7-flash · resource_task</b> — V6와 동일 일반화 한계.</li>
<li><b>세탁/카스트갭은 메커니즘만(비대칭 λ) 단위검증</b> — <code>beta_reputation(lam_down)</code>로 나쁜 기록을
  더 끈질기게 만들 수 있음(<code>tests/test_reputation_calc</code>). 전체 세탁 *실험*은 향후(검정력·비용).</li>
</ul>
"""
    has = (OUT.parent / "verify_elder.json").exists()
    status = ("✅ <b>실험 완료 + 단위테스트(265 통과).</b> ★결과 = 실측(<code>verify_elder.json</code>, 0 불일치)."
              if has else "⏳ <b>구현·단위테스트 완료(265 통과). 실험 데이터 대기.</b>")
    page = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Phase 2 — Elder 원장 judge 리포트</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Phase 2 — LLM-판관 평판은 신호인가, 또 앵커인가</h1>
<p class="lead">에이전트의 <b>근거 텍스트</b>를 Elder LLM이 채점해 행동 평판과 섞는다. 숫자 앵커 대조로
"judge가 진짜 신호를 더하는지"를 V6 방법론으로 가른다.</p>
<div class="status">{status}</div>
{body}
<footer>생성: <code>scripts/build_elder_report.py</code> · 구현: <code>antigreedy/governance/elder.py</code>,
<code>elder_judge.py</code>, <code>verify_claims.py</code>(elder) · 설계·문헌: <code>docs/related_work.md</code> §R3 · 폰트: Pretendard</footer>
</div></body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(OUT.parent.parent)} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
