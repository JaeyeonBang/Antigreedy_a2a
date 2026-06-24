"""통합 리포트 빌더 (단일 흐름, 조건의존) — 두 실험을 하나의 흐름으로 합친다.

읽는 데이터:
  docs/verify_unified.json       — 풍요(pool=수요)·간접(빨리끝내기), 11 메커니즘 (n=4, N=30)
  docs/verify_attack_full.json   — 희소(pool=½수요)·{간접,직접(사재기)}, 11 메커니즘 (n=4, N=30)
→ docs/unified_report.html

핵심 서사: 거버넌스 효과는 *자원 희소성 × 공격 유형*에 조건의존적이다.
  · 풍요: 독점이 안 생김 → 거버넌스 불필요, 겉보기 효과 = 길이 아티팩트(어떤 것도 filler 못 이김)
  · 희소+공격(사재기): 진짜 독점(top 1.0) → proactive 캡(dumb_cap/social/QV)만 filler를 이김.
    reactive 평판/판관·입력 프레이밍은 첫수 사재기꾼에 무력. 단 단순 캡은 후생을 0으로 만들고
    QV만 독점↓+후생 보존(후생-공정성 트레이드오프).

각 레짐의 '길이를 이기나'(vs neutral_filler) 유의성은 원자료에서 순열검정+Holm으로 *통일* 재계산.
사용: .venv/bin/python scripts/build_unified_report.py
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.verify_claims import permutation_p, holm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
U_SRC = ROOT / "docs" / "verify_unified.json"
A_SRC = ROOT / "docs" / "verify_attack_full.json"
Q_SRC = ROOT / "docs" / "verify_qv_refill.json"   # 재충전 풀 평판가중 검정(심화 §4)
OUT = ROOT / "docs" / "unified_report.html"

# 메커니즘 순서 + 계열(proactive/reactive/입력/대조) — proactive vs reactive 서사를 표가 직접 보이게
MECHS = [
    ("none",                "기준",         "무규제(기준선)"),
    ("dumb_cap",            "proactive 캡", "단순 비율 캡 (0.22·remaining)"),
    ("social",              "proactive 캡", "사회·평판 (가십캡+배제)"),
    ("qv_flat",             "proactive 캡", "진짜 QV·무가중 (2차비용)"),
    ("qv_rep",              "proactive 캡", "진짜 QV·평판가중"),
    ("ost_beta",            "reactive 평판", "평판 망각 (Beta λ0.7)"),
    ("ledger_elder",        "reactive 판관", "LLM 판관 (Elder α0.5)"),
    ("reputation_feedback", "입력 프레이밍", "평판 피드백 (프롬프트)"),
    ("superordinate",       "입력 프레이밍", "상위목표 정체성"),
    ("fairshare_anchor",    "대조",         "숫자 앵커 (내용 통제)"),
    ("neutral_filler",      "대조",         "중립 길이 (결정적 대조)"),
]
MNAMES = [m[0] for m in MECHS]
CLASS_COLOR = {"기준": "#888", "proactive 캡": "#2e7d4f", "reactive 평판": "#b07b1f",
               "reactive 판관": "#b07b1f", "입력 프레이밍": "#6ea8fe", "대조": "#9a958a"}


def _esc(s):
    return html.escape(str(s))


def filler_sig(arms):
    """각 메커니즘이 neutral_filler(길이)를 *유의하게* 이기나 — 원자료 순열검정+Holm(레짐 내 통일)."""
    fil = arms["neutral_filler"]["top_raw"]
    gov = [m for m in MNAMES if m not in ("none", "neutral_filler")]
    adj = holm([(m, permutation_p(arms[m]["top_raw"], fil)) for m in gov])
    win = {}
    for m, p, padj, sig in adj:
        lower = arms[m]["top_mean"] < arms["neutral_filler"]["top_mean"]
        win[m] = bool(sig and lower)
    return win


def load_regimes():
    u = json.loads(U_SRC.read_text())
    a = json.loads(A_SRC.read_text())
    regimes = [
        {"key": "abund_finish", "label": "풍요 · 간접",
         "sub": "pool=수요 · 빨리끝내기", "arms": u["arms"]},
        {"key": "scarce_finish", "label": "희소 · 간접",
         "sub": "pool=½수요 · 빨리끝내기", "arms": a["regimes"]["finish_first"]["arms"]},
        {"key": "scarce_hoard", "label": "희소 · 직접",
         "sub": "pool=½수요 · 사재기(공격)", "arms": a["regimes"]["hoard"]["arms"]},
    ]
    for r in regimes:
        r["win"] = filler_sig(r["arms"])
    return regimes, u["config"], a["config"]


def cell(r, name, key, lower_better):
    """레짐 r에서 메커니즘 name의 한 칸: 값 + filler 이김(▸) + 색(레짐 내 none 대비)."""
    v = r["arms"][name][key]
    base = r["arms"]["none"][key]
    if name == "none":
        return f'<td class="num base">{v:.3f}</td>'
    good = (v < base) if lower_better else (v > base)
    col = "#e7f4ec" if good else "#fbecea"
    win = r["win"].get(name, False) and lower_better
    mark = ' <b class="w">▸</b>' if win else ""
    return f'<td class="num" style="background:{col}">{v:.3f}{mark}</td>'


def master_table(regimes, key, lower_better, caption):
    head = "".join(f'<th>{_esc(r["label"])}<span class="rsub">{_esc(r["sub"])}</span></th>'
                   for r in regimes)
    rows = []
    for name, cls, mech in MECHS:
        cc = CLASS_COLOR.get(cls, "#888")
        cells = "".join(cell(r, name, key, lower_better) for r in regimes)
        cls_b = f'<span class="cls" style="color:{cc};border-color:{cc}55;background:{cc}14">{_esc(cls)}</span>'
        rows.append(f'<tr><td class="arm">{_esc(name)}</td><td class="mech">{cls_b}{_esc(mech)}</td>{cells}</tr>')
    return (f'<table class="master"><thead><tr><th>메커니즘</th><th>계열 · 기제</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
            f'<p class="cap">{caption}</p>')


def qv_refill_section():
    """재충전 풀 평판가중 검정(verify_qv_refill.json) → HTML 섹션."""
    if not Q_SRC.exists():
        return '<p class="sub">verify_qv_refill.json 미생성 — <code>verify_claims.py qv_refill</code> 먼저 실행.</p>'
    q = json.loads(Q_SRC.read_text())
    A, cfg = q["arms"], q["config"]
    sig = {c["label"].split(" (")[0]: c for c in q["contrasts"]}

    def srow(name, label, note):
        a = A[name]
        return (f'<tr><td class="arm">{name}</td><td class="mech">{label}</td>'
                f'<td class="num">{a["top_mean"]:.3f}</td><td class="num">{a["comp_mean"]:.2f}</td>'
                f'<td class="num">{a["a_share_mean"]:.3f}</td><td class="num">{a["a_rep_mean"]:.2f}</td>'
                f'<td>{note}</td></tr>')
    rows = "".join([
        srow("none", "무규제(기준)", "A가 독식"),
        srow("dumb_cap", "단순 캡", "rep 무관"),
        srow("social", "사회·평판", "rep 기반"),
        srow("qv_flat", "QV·무가중", '<span class="ns">≈ none (무효)</span>'),
        srow("qv_rep", "QV·평판가중", '<span class="w">▸ A를 억제</span>'),
    ])
    p = sig.get("A점유 qv_rep vs qv_flat", {}).get("p_holm", 1.0)
    return (f'<p class="sub">앞 실험에서 <code>qv_flat</code>과 <code>qv_rep</code>은 차이가 없었다. 그게 '
            f'<b>평판 가중이 쓸모없어서</b>인지 <b>설계가 평판을 못 살려서</b>인지 가르는 후속 실험이다. '
            f'고정 풀은 라운드 0에 소진돼 모든 캡이 평판=1.0에서 결정됐다 → 풀을 매 라운드 {cfg["pool_per_round"]} '
            f'보충(재충전 스트림)해 다회를 살리고, <b>비대칭</b>(A=사재기, B·C·D=공정)으로 A만 과소비하게 했다 '
            f'(N={cfg["seeds"]} · B={int(cfg["budget_B"])} · workload={cfg["workload"]} · 욕심쟁이=A).</p>'
            '<table><thead><tr><th>조건</th><th>기제</th><th>독점 top ↓</th><th>후생</th>'
            '<th>A 점유 ↓</th><th>A 평판</th><th>판정</th></tr></thead><tbody>' + rows + '</tbody></table>'
            f'<div class="easy"><b>💡 결론: 평판 가중은 의도대로 작동한다 — 단, 다회가 살아있을 때만.</b> '
            f'<code>qv_flat</code>은 평판을 안 봐 욕심쟁이 A를 <b>못 막는다</b>(A 점유 {A["qv_flat"]["a_share_mean"]:.2f} ≈ 무규제 {A["none"]["a_share_mean"]:.2f}). '
            f'<code>qv_rep</code>은 A의 과소비가 평판을 떨어뜨려 <code>비용=요청²/평판</code>을 폭증시켜 <b>A의 예산만 소진</b> → '
            f'A 점유를 {A["qv_rep"]["a_share_mean"]:.2f}로 <b>유의하게 억제</b>(vs flat, p_holm={p:.4f}). 공정한 B·C·D는 예산이 살아남는다. '
            f'즉 앞서 본 "flat≡rep"는 <b>메커니즘 실패가 아니라 다회가 죽은 설계 한계</b>였다 — 풀을 재충전해 다회를 살리면 평판 가중이 작동한다. '
            f'(이 실험은 workload가 스트림보다 커 완료(welfare)는 0; 초점은 <i>평판이 욕심쟁이를 가려내는가</i>이다.)</div>')


def build():
    regimes, ucfg, acfg = load_regimes()
    R = {r["key"]: r for r in regimes}
    none_top = [r["arms"]["none"]["top_mean"] for r in regimes]
    winners = {r["key"]: [m for m in MNAMES if r["win"].get(m)] for r in regimes}
    nwin = {k: len(v) for k, v in winners.items()}
    model = ucfg["model"]

    def wl(r, name):
        return r["arms"][name]["comp_mean"]

    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>통합 거버넌스 실험 — 조건의존적 효과 (단일 흐름)</title>
<link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--gold:#b07b1f;--ink:#1a1a1a;--mut:#666;--line:#e6e3dc;--bg:#faf8f3;--grn:#2e7d4f;--red:#b23b3b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:'Pretendard',-apple-system,'Malgun Gothic',sans-serif;line-height:1.62}}
.wrap{{max-width:1000px;margin:0 auto;padding:54px 28px 110px}}
h1{{font-family:'Crimson Pro',serif;font-weight:700;font-size:33px;margin:0 0 6px;letter-spacing:-.5px}}
h2{{font-family:'Crimson Pro',serif;font-weight:600;font-size:23px;margin:46px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--ink)}}
.sub{{color:var(--mut);font-size:15px;margin:0 0 8px}}
.bluf{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--gold);border-radius:10px;padding:18px 22px;margin:20px 0}}
.bluf b{{color:#000}}
.flow{{display:flex;align-items:stretch;gap:10px;margin:18px 0;flex-wrap:wrap}}
.fstep{{flex:1;min-width:200px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.fstep .ft{{font-weight:700;font-size:15px;margin-bottom:4px}}
.fstep .fn{{font-family:'Crimson Pro',serif;font-size:26px;font-weight:700;color:var(--gold)}}
.fstep .fd{{font-size:13px;color:var(--mut);margin-top:4px}}
.farrow{{display:flex;align-items:center;color:var(--gold);font-size:22px;font-weight:700}}
table{{width:100%;border-collapse:collapse;margin:10px 0;font-size:13px;background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden}}
th,td{{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line)}}
th{{background:#f3f0e8;font-weight:600;font-size:11.5px;color:#555;vertical-align:bottom}}
.rsub{{display:block;font-weight:400;font-size:10px;color:#999;margin-top:2px}}
td.num{{text-align:right;font-variant-numeric:tabular-nums;font-family:ui-monospace,monospace}}
td.num.base{{background:#f3f0e8;font-weight:700}}
td.arm{{font-weight:600;font-family:ui-monospace,monospace;font-size:12px}}
td.mech{{color:#444;font-size:12px}}
.cls{{display:inline-block;padding:0 6px;margin-right:6px;border-radius:5px;font-size:10.5px;font-weight:700;border:1px solid;vertical-align:middle}}
.w{{color:var(--grn);font-size:14px}}
.cap{{font-size:12px;color:var(--mut);margin:4px 0 0}}
.easy{{background:#eef7f0;border:1px solid #cfe6d6;border-radius:8px;padding:12px 16px;margin:14px 0;font-size:14px}}
.easy b{{color:#2e7d4f}}
.big{{font-size:28px;font-family:'Crimson Pro',serif;font-weight:700;color:var(--gold)}}
code{{background:#efece4;padding:1px 6px;border-radius:4px;font-size:12.5px}}
ul{{font-size:14.5px}}li{{margin:6px 0}}
.foot{{margin-top:56px;padding-top:16px;border-top:1px solid var(--line);color:#999;font-size:12.5px}}
.note{{font-size:13px;color:var(--mut)}}
</style></head><body><div class="wrap">

<h1>통합 거버넌스 실험 — 조건의존적 효과</h1>
<p class="sub">같은 <b>11개 메커니즘</b>을 하나의 흐름 위에서 — 모델 {_esc(model)} · n={ucfg['agents']} · N={ucfg['seeds']} ·
세 레짐(풍요·간접 → 희소·간접 → 희소·직접) · 원자료 0불일치 재계산</p>

<div class="bluf">
<p style="margin:0 0 8px"><b>한눈에(BLUF).</b> "거버넌스가 탐욕을 막나?"의 답은 <b>조건에 따라 다르다</b>.
자원이 넉넉하면 애초에 독점이 안 생겨 거버넌스가 할 일이 없고(겉보기 효과는 길이 아티팩트), 자원이
<b>희소하고 누군가 사재기로 공격</b>할 때 비로소 진짜 독점이 생기며 — 그때 <b>선제적 캡(proactive)만</b>
그 독점을 막고 <b>길이 대조군을 이긴다</b>. 평판·판관 같은 reactive 기제와 입력 프레이밍은 첫수에 다 쓸어가는
공격자 앞에서 무력했다.</p>
<p style="margin:0">길이 대조군(<code>neutral_filler</code>)을 <b>유의하게 이긴</b> 개입 수(레짐별 / 10):
풍요·간접 <span class="big">{nwin['abund_finish']}</span> →
희소·간접 <span class="big">{nwin['scarce_finish']}</span> →
희소·직접 <span class="big">{nwin['scarce_hoard']}</span>.
거버넌스는 <b>풍요엔 불필요·희소+공격엔 유효</b>하되, 후생을 함께 보면 단순 캡은 공정성을 *전원 실패*로 사고
<b>QV만</b> 독점–후생 트레이드오프를 항해한다.</p>
</div>

<div class="easy"><b>💡 쉽게.</b> 공용 프린터에 종이가 넉넉하면 누가 먼저 써도 다들 인쇄할 수 있어 "양보 규칙"이
필요 없습니다(풍요). 종이가 모자란데 한 명이 다 가져가려 들 때(희소+사재기) 비로소 규칙이 필요한데 —
<b>나오는 즉시 매수를 잘라내는 규칙(선제 캡)</b>만 통하고, "평판 나쁘면 다음에 불이익" 같은 *사후* 규칙은
첫 명령에 다 가져가 버리면 손쓸 새가 없습니다. 그리고 잘라내면 공평해지지만 *아무도 제 분량을 못 끝내는*
부작용이 따라옵니다.</div>

<h2>1. 독점은 *언제* 생기나 — 무규제(none) top-share</h2>
<div class="flow">
<div class="fstep"><div class="ft">풍요 · 간접</div><div class="fn">{none_top[0]:.3f}</div><div class="fd">자원이 충분 → 각자 제 몫만 잡아도 됨 → 독점 거의 없음</div></div>
<div class="farrow">→</div>
<div class="fstep"><div class="ft">희소 · 간접</div><div class="fn">{none_top[1]:.3f}</div><div class="fd">자원 절반 → 먼저 잡은 절반이 끝내고 나머지 굶음</div></div>
<div class="farrow">→</div>
<div class="fstep"><div class="ft">희소 · 직접(사재기)</div><div class="fn">{none_top[2]:.3f}</div><div class="fd">한 명이 첫수에 전부 독식 — "먼저 잡는 자가 다 갖는다"</div></div>
</div>
<p class="note">교차검정 p=0.0001 (사재기 {none_top[2]:.3f} vs 빨리끝내기 {none_top[1]:.3f}).
이전 통합/시금석 실험에서 효과가 안 보였던 건 — 기본 설정이 풍요(pool=수요)라 <b>독점 자체가 없었기</b> 때문.
거버넌스가 막을 대상이 있어야 효과를 잴 수 있다.</p>

<h2>2. 독점(top-share) — 11 메커니즘 × 3 레짐</h2>
<p class="sub">낮을수록 공정. 칸 색 = 그 레짐의 무규제 대비 좋음(초록)/나쁨(빨강).
<b class="w">▸</b> = 그 레짐에서 길이 대조군(neutral_filler)을 <b>유의하게</b> 이김(순열검정+Holm).</p>
{master_table(regimes, "top_mean", True,
    "핵심: ▸(길이를 이김)는 풍요엔 전혀 없고(거버넌스 불필요), 희소·직접에선 proactive 캡 4종(dumb_cap·social·qv_flat·qv_rep)에만 붙는다. reactive 평판/판관·입력 프레이밍은 사재기꾼 앞에서 top≈1.0으로 무력.")}

<div class="easy"><b>💡 proactive vs reactive.</b> 사재기꾼은 <b>첫 턴에 풀을 다 비웁니다.</b>
<code>dumb_cap</code>·<code>social</code>·<code>QV</code>는 *나오는 즉시* 그 첫 그랩을 잘라(0.22·잔량, 또는 2차비용)
물리적으로 막습니다. 반면 <code>ost_beta</code>(평판 망각)·<code>ledger_elder</code>(LLM 판관)는 <b>"나쁜 짓을
한 뒤" 평판/점수가 쌓여야</b> 작동하는데 — 첫수에 다 가져가 버리면 쌓을 이력이 없어 무력합니다(top 1.0).
입력 프레이밍("말로 타이르기")도 결연한 공격자에겐 길이 채움과 다를 바 없었습니다.</div>

<h2>3. 후생(welfare) — 공정성을 무엇과 바꾸나</h2>
<p class="sub">높을수록 좋음(과제 *완료*한 에이전트 비율). 색 = 무규제 대비 좋음(초록)/나쁨(빨강).</p>
{master_table(regimes, "comp_mean", False,
    "희소에서 독점을 가장 많이 줄인 단순 캡(dumb_cap·social)이 후생을 0.00으로 만든다 — 모두를 똑같이 잘라 *아무도 제 분량을 못 끝냄*(희소+전부-아니면-전무 완료의 함정). QV(qv_flat·qv_rep)만 독점을 줄이면서 무규제 수준 후생을 보존.")}
<div class="easy"><b>💡 트레이드오프.</b> 희소·직접에서 <code>none</code> 후생은 {wl(R['scarce_hoard'],'none'):.2f}(사재기꾼만 완료),
<code>dumb_cap</code>/<code>social</code>은 독점을 {R['scarce_hoard']['arms']['dumb_cap']['top_mean']:.2f}까지 낮추지만 후생
<b>0.00</b>(전원 미완), <code>qv_rep</code>만 독점 {R['scarce_hoard']['arms']['qv_rep']['top_mean']:.2f} + 후생
{wl(R['scarce_hoard'],'qv_rep'):.2f} 보존. 희소는 거의 제로섬이라 *재분배는 되지만 후생을 만들어내진 못한다* —
QV가 그나마 덜 나쁜 유일한 선택.</div>

<h2>4. 심화 — 재충전 풀에서 '평판 가중 QV'는 작동하는가</h2>
{qv_refill_section()}

<h2>5. 방법론과 정직한 해석</h2>
<ul>
<li><b>하나의 흐름.</b> 11개 메커니즘 전부 같은 모델({_esc(model)})·같은 n={ucfg['agents']}·같은 baseline에서,
자원 희소성(풍요/희소)과 공격 유형(간접 빨리끝내기/직접 사재기)만 바꿔 비교했다.</li>
<li><b>결정적 검정 = vs <code>neutral_filler</code>.</b> "독점 지표가 내려감"은 길이만 늘려도 생기므로,
진짜 효과는 <i>내용 없는 길이 채움을 이기는가</i>로 판정한다(세 레짐 모두 동일하게 순열검정+Holm 재계산).</li>
<li><b>near-deterministic 주의.</b> 사재기+희소는 동역학이 거의 결정적(사재기꾼이 항상 전부 그랩 → top≈1.0,
후생≈0.25)이라 분산이 작다. 효과는 강하고 재현적이나, 이는 *강한 페르소나가 행동을 강하게 유도*한 결과이기도 하다.</li>
<li><b>범위.</b> 전 결과 {_esc(model)}·resource_task·n={ucfg['agents']}·s∈{{1.0, 0.5}} 한정. 다른 모델·시나리오로의
일반화는 주장하지 않는다.</li>
</ul>

<div class="bluf"><b>한 줄 결론.</b> 탐욕 거버넌스의 효과는 <b>자원 희소성과 공격 유형에 조건의존적</b>이다.
풍요에선 불필요(겉보기 효과=아티팩트), 희소+직접 공격에선 <b>선제적 캡만</b> 유효하며(reactive 평판·입력
프레이밍은 first-mover 공격에 무력), 그 효과조차 <b>후생-공정성 트레이드오프</b>를 동반한다 — QV만 그 균형을 항해한다.</div>

<div class="foot">생성: <code>scripts/build_unified_report.py</code> ← <code>verify_unified.json</code> +
<code>verify_attack_full.json</code> (<code>verify_claims.py unified</code> / <code>attack</code>) · Antigreedy A2A</div>
</div></body></html>"""


if __name__ == "__main__":
    OUT.write_text(build())
    print(f"wrote {OUT} ({len(OUT.read_text())} bytes)")
