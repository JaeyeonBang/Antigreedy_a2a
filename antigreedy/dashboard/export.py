"""Standalone HTML export for a recorded run.

Produces a single self-contained HTML document with the run's event log inlined
and a minimal replay renderer (Cytoscape via CDN, no WebSocket / no server). The
file opens offline and replays the run into per-condition panels — for sharing a
result or dropping into a slide deck. The event log is the product (design §7),
so the export is just the events + a thin renderer.
"""
from __future__ import annotations

import json
from typing import Any

_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Antigreedy 내보내기 — __RUNID__</title>
<script src="https://unpkg.com/cytoscape@3.30.2/dist/cytoscape.min.js"></script>
<style>
  :root{--bg:#0e1116;--panel:#161b22;--ink:#e6edf3;--mut:#9aa6b2;--ok:#3fb950;--warn:#d29922;--bad:#f85149;}
  *{box-sizing:border-box;} body{margin:0;font:14.5px/1.6 system-ui,"Malgun Gothic",sans-serif;background:var(--bg);color:var(--ink);}
  header{padding:16px 22px;border-bottom:1px solid #21262d;}
  h1{font-size:17px;margin:0 0 4px;} .sub{color:var(--mut);font-size:12.5px;}
  .wrap{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#21262d;}
  .panel{background:var(--panel);padding:16px;min-height:50vh;}
  .panel h2{margin:0 0 8px;font-size:15px;} .panel.baseline h2{color:var(--bad);} .panel.governed h2{color:var(--ok);}
  .graph{height:320px;background:#0d1117;border:1px solid #21262d;border-radius:8px;}
  .gauge{height:12px;background:#0d1117;border-radius:6px;margin:11px 0 4px;overflow:hidden;}
  .gauge>span{display:block;height:100%;background:var(--ok);}
  .meta{display:flex;justify-content:space-between;color:var(--mut);font-size:12.5px;}
  .metrics{margin-top:9px;font-size:12.5px;color:var(--mut);background:#0d1117;border:1px solid #2a3340;border-radius:7px;padding:9px 11px;}
  .fair{font-weight:700;font-size:13.5px;} .mbar{height:10px;background:#161b22;border-radius:5px;overflow:hidden;display:flex;margin-top:6px;}
  .mbar i{height:100%;}
  .feed{margin-top:12px;max-height:220px;overflow:auto;font:12.5px/1.5 ui-monospace,monospace;}
  .feed div{padding:3px 0;border-bottom:1px solid #1b2129;}
  .v-allow{color:var(--ok);} .v-modify{color:var(--warn);} .v-deny{color:var(--bad);}
  .note{padding:8px 22px;color:var(--mut);font-size:12px;}
</style>
</head>
<body>
<header>
  <h1>Antigreedy — 실험 내보내기</h1>
  <div class="sub">런 __RUNID__ · __CREATED__ · 모드 __MODE__ · 오프라인 재생 (서버 불필요)</div>
</header>
<div class="wrap" id="wrap"></div>
<div class="note">이 파일은 기록된 이벤트 로그를 그대로 재생합니다 — 인터넷은 Cytoscape 로드에만 필요합니다.</div>
<script>
const RECORD = __DATA__;
const COL={allow:'#3fb950',modify:'#d29922',deny:'#f85149',delay:'#a371f7'};
const AGC=['#1f6feb','#3fb950','#d29922','#a371f7','#f85149','#39c5cf','#db61a2','#c9d1d9'];
const KO={baseline:'베이스라인 · 무규제',governed:'거버넌스 적용'};
const OUT={survived:'생존',exhausted:'고갈',decided:'합의',cap_aborted:'중단',probe_complete:'완료',errored:'오류'};
function panel(cond){
  const sec=document.createElement('section'); sec.className='panel '+cond;
  sec.innerHTML=`<h2>${KO[cond]||cond}</h2><div class="graph" id="g-${cond}"></div>`+
    `<div class="gauge"><span id="bar-${cond}" style="width:100%"></span></div>`+
    `<div class="meta"><span id="commons-${cond}">커먼즈: —</span><span id="out-${cond}">—</span></div>`+
    `<div class="metrics" id="metrics-${cond}" style="display:none"></div>`+
    `<div class="feed" id="feed-${cond}"></div>`;
  document.getElementById('wrap').appendChild(sec); return sec;
}
const conds=[...new Set(RECORD.events.map(e=>e.condition).filter(Boolean))];
(conds.length?conds:['governed']).forEach(panel);
const S={};
function mk(id,agents){ const cy=cytoscape({container:document.getElementById(id),
  style:[{selector:'node',style:{'label':'data(id)','color':'#fff','text-valign':'center','font-size':12,'width':'data(sz)','height':'data(sz)','background-color':'data(col)'}},
         {selector:'edge',style:{'width':1,'line-color':'#30363d','opacity':.4}}],
  layout:{name:'circle'},userZoomingEnabled:false,userPanningEnabled:false});
  agents.forEach(a=>cy.add({data:{id:a,sz:24,col:'#1f6feb'}}));
  for(let i=0;i<agents.length;i++)for(let j=i+1;j<agents.length;j++)cy.add({data:{id:agents[i]+agents[j],source:agents[i],target:agents[j]}});
  cy.layout({name:'circle'}).run(); return cy; }
function metrics(cond,m){ const el=document.getElementById('metrics-'+cond); if(!el)return;
  const j=(typeof m.jain_delivered==='number')?m.jain_delivered:0;
  const ag=Object.keys(m.delivered||{}).sort(); const tot=ag.reduce((s,a)=>s+(m.delivered[a]||0),0)||1;
  const bars=ag.map((a,i)=>`<i title="${a}" style="width:${100*(m.delivered[a]||0)/tot}%;background:${AGC[i%AGC.length]}"></i>`).join('');
  const col=j>=0.8?'#3fb950':j>=0.6?'#d29922':'#f85149';
  el.innerHTML=`<span class="fair" style="color:${col}">공정성(Jain) ${j.toFixed(2)}</span> · 최대 점유 ${Math.round((m.top_share||0)*100)}%<div class="mbar">${bars}</div>`;
  el.style.display='block'; }
RECORD.events.forEach(ev=>{ const c=ev.condition; if(!c)return; const d=ev.data||{};
  const st=S[c]||(S[c]={cy:null,budget:1,deliv:{}});
  if(ev.type==='episode_start'){ st.budget=d.budget||0; st.deliv={}; (d.agents||[]).forEach(a=>st.deliv[a]=0); st.cy=mk('g-'+c,d.agents||[]); }
  else if(ev.type==='turn'){ const a=d.agent_id; st.deliv[a]=(st.deliv[a]||0)+(d.delivered_tokens||0);
    if(st.cy){const n=st.cy.$('#'+a); n.data('sz',Math.min(150,24+Math.sqrt(st.deliv[a])*6)); n.data('col',COL[d.verdict]||'#1f6feb');}
    if(st.budget>0&&typeof d.commons_left==='number'){const p=Math.max(0,Math.min(100,100*d.commons_left/st.budget));
      const b=document.getElementById('bar-'+c); b.style.width=p+'%'; b.style.background=p<25?'#f85149':p<60?'#d29922':'#3fb950';
      document.getElementById('commons-'+c).textContent='커먼즈: '+Math.max(0,d.commons_left)+' / '+st.budget;}
    const f=document.getElementById('feed-'+c); const r=document.createElement('div');
    r.innerHTML=`r${d.round} <b>${a}</b> <span class="v-${d.verdict}">${d.verdict}</span> 시도 ${d.attempted_tokens}→전달 ${d.delivered_tokens}`;
    f.prepend(r); }
  else if(ev.type==='ground_truth'){ if(d.deceptive){const f=document.getElementById('feed-'+c);const r=document.createElement('div');r.style.color='#f85149';
    r.innerHTML=`🚩 <b>${d.agent_id}</b> 기만 — 보고값 ${d.reported} vs 실제 ${d.true_value}`; f.prepend(r);} }
  else if(ev.type==='episode_end'){ const o=document.getElementById('out-'+c); if(o)o.textContent=OUT[d.outcome]||d.outcome||'';
    if(d.metrics)metrics(c,d.metrics); }
});
</script>
</body>
</html>
"""


def build_standalone_html(record: dict[str, Any]) -> str:
    """Render a recorded run into a self-contained, offline-replayable HTML doc."""
    data = json.dumps(record, ensure_ascii=False)
    return (_TEMPLATE
            .replace("__DATA__", data)
            .replace("__RUNID__", str(record.get("id", "")))
            .replace("__CREATED__", str(record.get("created_iso", "")))
            .replace("__MODE__", str(record.get("mode", ""))))
