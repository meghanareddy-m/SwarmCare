"""Single-file results dashboard: ``results/dashboard.html``.

No dependencies: the benchmark data is embedded as JSON and drawn with inline
SVG by a small vanilla-JS script (no network access, no external libraries).

Panels: waiting-queue length over time (all algorithms of a scenario, shock
markers), resource utilization over time (selected algorithm, shock markers),
admission decisions per tick (selected algorithm; click a tick for details),
and the extended metrics (ICU saturation, recovery time, bottleneck, latency
budget).

Run:  python -m experiments.dashboard --output results/dashboard.html
"""

import argparse
import json
from pathlib import Path

from evaluation.metrics import DEFAULT_LATENCY_BUDGET_MS
from experiments.runner import (ALGORITHM_LABELS, DEFAULT_SCENARIO, list_scenarios,
                                run_benchmark)

TIMELINE_FIELDS = ["queue", "queue_after", "diagnostic_queue",
                   "doctors_used", "doctors_cap", "icu_used", "icu_cap",
                   "ward_used", "ward_cap", "oxygen_used", "oxygen_cap",
                   "ventilators_used", "ventilators_cap"]


def _event_label(event):
    detail = ""
    if "count" in event:
        detail = f" x{event['count']}"
    elif "percentage" in event:
        detail = f" {event['percentage']}%"
    return event["type"] + detail


def build_dashboard_data(results, latency_budget_ms=DEFAULT_LATENCY_BUDGET_MS):
    """Compact, JSON-serializable payload (timelines are stored column-wise)."""
    runs = {}
    for r in results:
        timeline = r["timeline"]
        entry = {
            "label": r["label"],
            "fitness": r["fitness_mean"],
            "completed": r["completed"],
            "total": r["total_patients"],
            "series": {f: [t[f] for t in timeline] for f in TIMELINE_FIELDS},
            "events": [[t["time"], _event_label(e), e["type"]]
                       for t in timeline for e in t["events"]],
            "decisions": [
                {"q": d["queue"], "def": d["deferred"],
                 "adm": [[a["id"], a["severity"], a["bed"], int(a["oxygen"]), int(a["ventilator"])]
                         for a in d["admitted"]],
                 **{k: d[k] for k in ("messages", "rounds", "reserve_blocked") if k in d}}
                for d in r["decisions"]
            ],
            "extended": r["extended"],
            "critical": r["critical"],
        }
        runs.setdefault(r["scenario"], {})[r["algorithm"]] = entry
    return {"latency_budget_ms": latency_budget_ms, "runs": runs}


def render_dashboard(results, latency_budget_ms=DEFAULT_LATENCY_BUDGET_MS):
    payload = json.dumps(build_dashboard_data(results, latency_budget_ms), separators=(",", ":"))
    payload = payload.replace("</", "<\\/").replace("<!--", "<\\!--")
    return HTML_TEMPLATE.replace("/*__DATA__*/null", payload)


def write_dashboard(results, path, latency_budget_ms=DEFAULT_LATENCY_BUDGET_MS):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dashboard(results, latency_budget_ms), encoding="utf-8")
    return path


def main(argv=None):
    p = argparse.ArgumentParser(description="Write the SwarmCare HTML dashboard")
    p.add_argument("--all", action="store_true", help="include every scenario (default: S5 only)")
    p.add_argument("--scenarios", nargs="+", help="scenario ids or prefixes")
    p.add_argument("--algorithms", nargs="+", choices=list(ALGORITHM_LABELS))
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--latency-budget-ms", type=float, default=DEFAULT_LATENCY_BUDGET_MS)
    p.add_argument("--output", default="results/dashboard.html")
    args = p.parse_args(argv)
    scenarios = list_scenarios() if args.all else (args.scenarios or [DEFAULT_SCENARIO])
    results = run_benchmark(scenarios, args.algorithms, seeds=1, base_seed=args.seed)
    print(f"wrote {write_dashboard(results, args.output, args.latency_budget_ms)}")
    return 0


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SwarmCare dashboard</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--fg:#1c2330;--muted:#627086;--line:#d7dce4;--grid:#e9ecf1;--shock:#c0392b;
--c0:#1f77b4;--c1:#2ca02c;--c2:#9467bd;--c3:#e67e22;--c4:#d62728;--icu:#d62728;--ward:#2e86c1}
@media (prefers-color-scheme:dark){:root{--bg:#10141b;--card:#181e28;--fg:#e6eaf0;--muted:#93a0b5;--line:#2c3443;--grid:#232a37;--shock:#ff7a6b;
--c0:#5dade2;--c1:#58d68d;--c2:#bb8fce;--c3:#f0a04b;--c4:#ff6b6b;--icu:#ff6b6b;--ward:#5dade2}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{padding:16px 20px;border-bottom:1px solid var(--line);background:var(--card)}
h1{font-size:18px;margin:0 0 2px}h2{font-size:14px;margin:0 0 8px}
.sub{color:var(--muted);font-size:12px}
main{max-width:1100px;margin:0 auto;padding:16px 20px 40px;display:grid;gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.controls{display:flex;flex-wrap:wrap;gap:14px;align-items:center}
select,button{font:inherit;color:var(--fg);background:var(--card);border:1px solid var(--line);border-radius:6px;padding:4px 8px}
label{display:inline-flex;gap:5px;align-items:center;cursor:pointer}
svg{width:100%;height:auto;display:block}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:var(--muted);margin-top:4px}
.legend span{display:inline-flex;align-items:center;gap:5px;cursor:pointer}
.legend i{display:inline-block;width:14px;height:3px;border-radius:2px}
.legend .off{opacity:.35;text-decoration:line-through}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}
.metric .v{font-size:20px;font-weight:600}.metric .k{color:var(--muted);font-size:12px}
.bar{height:6px;background:var(--grid);border-radius:3px;margin:2px 0 6px}.bar b{display:block;height:100%;border-radius:3px;background:var(--c0)}
table{border-collapse:collapse;width:100%;font-size:12px}th,td{text-align:left;padding:3px 8px;border-bottom:1px solid var(--grid)}
.ok{color:var(--c1)}.bad{color:var(--shock)}
text{fill:var(--muted);font-size:11px}.axis{stroke:var(--line)}.grid{stroke:var(--grid)}
.shock{stroke:var(--shock);stroke-dasharray:4 3;stroke-width:1.2}.cursor{stroke:var(--fg);stroke-width:1;opacity:.5}
.note{font-size:12px;color:var(--muted)}
input[type=range]{width:min(420px,100%)}
</style>
</head>
<body>
<header>
<h1>SwarmCare dashboard</h1>
<div class="sub">Synthetic hospital simulation &mdash; not clinical data, not decision support. Single file, inline SVG, no dependencies.</div>
</header>
<main>
<div class="card controls">
<label>Scenario <select id="scenario"></select></label>
<span id="algos" role="radiogroup" aria-label="Algorithm"></span>
<label>Tick <input type="range" id="tick" min="0" max="0" value="0"> <b id="tickval">0</b></label>
</div>
<div class="cards" id="metrics"></div>
<div class="card"><h2>Waiting queue over time (all algorithms)</h2><svg id="qchart" role="img" aria-label="Queue length over time"></svg>
<div class="legend" id="qlegend"></div></div>
<div class="card"><h2>Resource utilization (selected algorithm)</h2><svg id="uchart" role="img" aria-label="Utilization per resource over time"></svg>
<div class="legend" id="ulegend"></div>
<div class="note">Utilization = units in use / current capacity; capacity 0 after a shock is drawn as 100 % (nothing available). Dashed red lines are shocks.</div></div>
<div class="card"><h2>Agent decisions per tick (selected algorithm)</h2><svg id="dchart" role="img" aria-label="Admitted patients by severity over time"></svg>
<div class="legend"><span style="cursor:default"><i style="background:var(--icu);height:8px;width:8px;border-radius:50%"></i>ICU admission</span>
<span style="cursor:default"><i style="background:var(--ward);height:8px;width:8px;border-radius:50%"></i>Ward admission</span>
<span style="cursor:default">ring = needs ventilator</span></div>
<div id="detail" class="note" style="margin-top:8px"></div></div>
<div class="card"><h2>Shocks and recovery (selected algorithm)</h2><div id="shocks"></div></div>
</main>
<script type="application/json" id="data">/*__DATA__*/null</script>
<script>
"use strict";
var DATA = JSON.parse(document.getElementById("data").textContent);
var RES = [["doctors","Doctors","--c0"],["icu","ICU beds","--c4"],["ward","Ward beds","--c1"],["oxygen","Oxygen","--c3"],["ventilators","Ventilators","--c2"]];
var ALGO_COLORS = ["--c0","--c1","--c2","--c3"];
var state = {scenario:null, algo:null, tick:0, hidden:{}};
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
function css(v){return "var("+v+")";}
function scen(){return DATA.runs[state.scenario];}
function run(){return scen()[state.algo];}
function pct(x){return (100*x).toFixed(0)+" %";}
function f2(x){return x==null?"-":Number(x).toFixed(2);}

var W=900,H=250,M={l:44,r:14,t:14,b:26};
function scale(n,ymax){
  var xs=function(i){return M.l+(n<=1?0:i*(W-M.l-M.r)/(n-1));};
  var ys=function(v){return H-M.b-(ymax<=0?0:v*(H-M.t-M.b)/ymax);};
  return {x:xs,y:ys};
}
function frame(n,ymax,yfmt){
  var s=scale(n,ymax),o="";
  for(var k=0;k<=4;k++){var v=ymax*k/4,y=s.y(v);
    o+='<line class="grid" x1="'+M.l+'" x2="'+(W-M.r)+'" y1="'+y+'" y2="'+y+'"/><text x="'+(M.l-6)+'" y="'+(y+4)+'" text-anchor="end">'+yfmt(v)+'</text>';}
  var step=Math.max(1,Math.ceil(n/10));
  for(var i=0;i<n;i+=step){o+='<text x="'+s.x(i)+'" y="'+(H-8)+'" text-anchor="middle">'+i+'</text>';}
  o+='<line class="axis" x1="'+M.l+'" x2="'+M.l+'" y1="'+M.t+'" y2="'+(H-M.b)+'"/><line class="axis" x1="'+M.l+'" x2="'+(W-M.r)+'" y1="'+(H-M.b)+'" y2="'+(H-M.b)+'"/>';
  return o;
}
function shockLines(n,events){
  var s=scale(n,1),o="";
  events.forEach(function(e){var x=s.x(e[0]);
    o+='<g><line class="shock" x1="'+x+'" x2="'+x+'" y1="'+M.t+'" y2="'+(H-M.b)+'"/><path d="M'+(x-4)+','+M.t+' L'+(x+4)+','+M.t+' L'+x+','+(M.t+7)+'Z" fill="var(--shock)"/><title>t='+e[0]+': '+esc(e[1])+'</title></g>';});
  return o;
}
function cursor(n){var s=scale(n,1),x=s.x(state.tick);return '<line class="cursor" x1="'+x+'" x2="'+x+'" y1="'+M.t+'" y2="'+(H-M.b)+'"/>';}
function path(vals,ymax,color,dash){
  var s=scale(vals.length,ymax),d="";
  vals.forEach(function(v,i){d+=(i?"L":"M")+s.x(i).toFixed(1)+","+s.y(v).toFixed(1);});
  return '<path d="'+d+'" fill="none" stroke="'+css(color)+'" stroke-width="2"'+(dash?' stroke-dasharray="5 3"':'')+'/>';
}
function hitbands(n,id){
  var s=scale(n,1),bw=(W-M.l-M.r)/Math.max(n-1,1),o="";
  for(var i=0;i<n;i++){o+='<rect data-t="'+i+'" x="'+(s.x(i)-bw/2)+'" y="'+M.t+'" width="'+bw+'" height="'+(H-M.t-M.b)+'" fill="transparent" style="cursor:pointer"/>';}
  return o;
}
function bindBands(el){el.querySelectorAll("rect[data-t]").forEach(function(r){r.addEventListener("click",function(){setTick(+r.getAttribute("data-t"));});});}

function drawQueue(){
  var sc=scen(),algos=Object.keys(sc),n=sc[algos[0]].series.queue.length,ymax=1;
  algos.forEach(function(a){ymax=Math.max(ymax,Math.max.apply(null,sc[a].series.queue));});
  ymax=Math.ceil(ymax/4)*4;
  var o=frame(n,ymax,function(v){return Math.round(v);});
  algos.forEach(function(a,i){o+=path(sc[a].series.queue,ymax,ALGO_COLORS[i%4],a!==state.algo&&false);});
  var diag=run().series.diagnostic_queue;
  if(Math.max.apply(null,diag)>0){o+=path(diag,ymax,"--muted",true);}
  o+=shockLines(n,run().events)+cursor(n)+hitbands(n);
  var svg=document.getElementById("qchart");svg.setAttribute("viewBox","0 0 "+W+" "+H);svg.innerHTML=o;bindBands(svg);
  var lg=algos.map(function(a,i){return '<span style="cursor:default"><i style="background:'+css(ALGO_COLORS[i%4])+'"></i>'+esc(a)+'</span>';}).join("");
  if(Math.max.apply(null,diag)>0){lg+='<span style="cursor:default"><i style="background:var(--muted)"></i>diagnostics queue ('+esc(state.algo)+')</span>';}
  document.getElementById("qlegend").innerHTML=lg;
}
function drawUtil(){
  var r=run(),n=r.series.queue.length,o=frame(n,1,function(v){return Math.round(100*v)+"%";});
  RES.forEach(function(res){
    if(state.hidden[res[0]])return;
    var used=r.series[res[0]+"_used"],cap=r.series[res[0]+"_cap"];
    o+=path(used.map(function(u,i){return cap[i]>0?Math.min(u/cap[i],1):1;}),1,res[2]);
  });
  o+=shockLines(n,r.events)+cursor(n)+hitbands(n);
  var svg=document.getElementById("uchart");svg.setAttribute("viewBox","0 0 "+W+" "+H);svg.innerHTML=o;bindBands(svg);
  var lg=document.getElementById("ulegend");
  lg.innerHTML=RES.map(function(res){return '<span data-r="'+res[0]+'" class="'+(state.hidden[res[0]]?"off":"")+'"><i style="background:'+css(res[2])+'"></i>'+res[1]+'</span>';}).join("");
  lg.querySelectorAll("span").forEach(function(sp){sp.addEventListener("click",function(){var k=sp.getAttribute("data-r");state.hidden[k]=!state.hidden[k];drawUtil();});});
}
function drawDecisions(){
  var r=run(),n=r.decisions.length,s=scale(n,1),o=frame(n,1,function(v){return v.toFixed(2);});
  r.decisions.forEach(function(d,i){
    d.adm.forEach(function(a){
      var cx=s.x(i),cy=s.y(a[1]);
      o+='<circle cx="'+cx+'" cy="'+cy+'" r="3.6" fill="'+(a[2]==="ICU"?css("--icu"):css("--ward"))+'" fill-opacity=".85"'+(a[4]?' stroke="var(--fg)" stroke-width="1.4"':'')+'><title>t='+i+' '+esc(a[0])+' severity '+a[1]+' '+esc(a[2])+(a[3]?' +O2':'')+(a[4]?' +vent':'')+'</title></circle>';
    });
  });
  var y80=s.y(0.8);o+='<line class="grid" x1="'+M.l+'" x2="'+(W-M.r)+'" y1="'+y80+'" y2="'+y80+'" stroke-dasharray="2 3"/><text x="'+(W-M.r)+'" y="'+(y80-3)+'" text-anchor="end">critical (&ge;0.80)</text>';
  o+=shockLines(n,r.events)+cursor(n)+hitbands(n);
  var svg=document.getElementById("dchart");svg.setAttribute("viewBox","0 0 "+W+" "+H);svg.innerHTML=o;bindBands(svg);
}
function drawDetail(){
  var r=run(),d=r.decisions[state.tick],t=state.tick,S=r.series;
  var rows=d.adm.map(function(a){return "<tr><td>"+esc(a[0])+"</td><td>"+a[1]+"</td><td>"+esc(a[2])+"</td><td>"+(a[3]?"yes":"")+"</td><td>"+(a[4]?"yes":"")+"</td></tr>";}).join("");
  var extra=(d.messages!=null?" &middot; "+d.messages+" messages, "+d.rounds+" round(s)":"")+(d.reserve_blocked?" &middot; "+d.reserve_blocked+" reserve refusal(s)":"");
  var res=RES.map(function(x){return x[1]+" "+S[x[0]+"_used"][t]+"/"+S[x[0]+"_cap"][t];}).join(" &middot; ");
  document.getElementById("detail").innerHTML="<b>Tick "+t+"</b>: "+d.q+" waiting, "+d.adm.length+" admitted, "+d.def+" deferred"+extra+
    "<br>"+res+(S.diagnostic_queue[t]?" &middot; diagnostics queue "+S.diagnostic_queue[t]:"")+
    (d.adm.length?'<table style="margin-top:6px"><tr><th>Patient</th><th>Severity</th><th>Bed</th><th>O2</th><th>Vent</th></tr>'+rows+"</table>":"");
}
function drawMetrics(){
  var r=run(),e=r.extended,ic=e.icu_saturation,b=e.bottleneck,lb=e.latency_budget,c=r.critical;
  function card(k,v,extra){return '<div class="card metric"><div class="k">'+k+'</div><div class="v">'+v+'</div>'+(extra||"")+'</div>';}
  var shares=b.resource?RES.map(function(x){var s=b.shares[x[0]]||0;return '<div class="k">'+x[1]+" "+pct(s)+'</div><div class="bar"><b style="width:'+(100*s)+'%"></b></div>';}).join(""):"";
  var rec=e.recovery_time;
  document.getElementById("metrics").innerHTML=
    card("Fitness",r.fitness.toFixed(4),'<div class="k">'+r.completed+"/"+r.total+" completed</div>")+
    card("ICU saturation",pct(ic.saturation),'<div class="k">peak utilization '+pct(ic.peak_utilization)+"; full with queue "+pct(ic.saturated_with_queue)+"</div>")+
    card("Bottleneck",b.resource?esc(b.resource):"none",'<div class="k">saturated share of ticks with a queue ('+b.ticks_with_queue+")</div>"+shares)+
    card("Mean recovery",rec.mean_recovery==null?"-":f2(rec.mean_recovery)+" ticks",'<div class="k">'+rec.shocks.length+" event(s), "+rec.unrecovered+" unrecovered</div>")+
    card("Latency budget "+lb.budget_ms+" ms",'<span class="'+(lb.meets_budget?"ok":"bad")+'">'+(lb.meets_budget?"met":"exceeded")+"</span>",'<div class="k">'+pct(lb.within_budget)+" of ticks within; p95 "+f2(lb.p95_ms)+" ms, max "+f2(lb.max_ms)+" ms (machine dependent)</div>")+
    card("Critical patients wait",f2(c.critical_mean_wait)+" ticks",'<div class="k">max '+c.critical_max_wait+"; non-critical mean "+f2(c.noncritical_mean_wait)+"</div>");
  var t=rec.shocks.length?'<table><tr><th>Tick</th><th>Event</th><th>Queue before</th><th>Peak queue</th><th>Recovery (ticks)</th></tr>'+rec.shocks.map(function(s){return "<tr><td>"+s.time+"</td><td>"+esc(s.type)+"</td><td>"+s.pre_queue+"</td><td>"+s.peak_queue+"</td><td>"+(s.recovery_ticks==null?'<span class="bad">not recovered</span>':s.recovery_ticks)+"</td></tr>";}).join("")+"</table>":'<span class="note">No events in this scenario.</span>';
  document.getElementById("shocks").innerHTML=t;
}
function setTick(t){
  var n=run().decisions.length;state.tick=Math.max(0,Math.min(n-1,t));
  document.getElementById("tick").value=state.tick;document.getElementById("tickval").textContent=state.tick;
  drawQueue();drawUtil();drawDecisions();drawDetail();
}
function refresh(){
  var n=run().decisions.length,sl=document.getElementById("tick");sl.max=n-1;
  drawMetrics();setTick(Math.min(state.tick,n-1));
}
function buildAlgoPicker(){
  var algos=Object.keys(scen());if(algos.indexOf(state.algo)<0)state.algo=algos[algos.length-1];
  document.getElementById("algos").innerHTML=algos.map(function(a){return '<label><input type="radio" name="algo" value="'+esc(a)+'"'+(a===state.algo?" checked":"")+"> "+esc(a)+"</label> ";}).join("");
  document.querySelectorAll('input[name=algo]').forEach(function(el){el.addEventListener("change",function(){state.algo=el.value;refresh();});});
}
(function init(){
  var names=Object.keys(DATA.runs),sel=document.getElementById("scenario");
  sel.innerHTML=names.map(function(n){return '<option value="'+esc(n)+'">'+esc(n)+"</option>";}).join("");
  var withShocks=names.filter(function(n){var a=Object.keys(DATA.runs[n])[0];return DATA.runs[n][a].events.length>0;});
  state.scenario=names.indexOf("S5_pandemic_crisis")>=0?"S5_pandemic_crisis":(withShocks[0]||names[0]);
  sel.value=state.scenario;state.algo="decentralized";buildAlgoPicker();
  sel.addEventListener("change",function(){state.scenario=sel.value;state.tick=0;buildAlgoPicker();refresh();});
  document.getElementById("tick").addEventListener("input",function(e){setTick(+e.target.value);});
  refresh();
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    raise SystemExit(main())
