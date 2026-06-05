"""Generate a single self-contained HTML viewer for the rolled-exposure data
and the monthly-review brief drafts.

Quick local way to eyeball the outputs — no server, no build step. Reads the
canonical multisignal CSV + coverage CSV + the per-fund monthly-review brief
JSON, embeds them, and writes one HTML file you can open directly in a browser.

    python scripts/build_data_viewer.py
    # then open artifacts/data_viewer.html

This is a data inspector, not the product frontend.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from portfolio_analyst_agent.monthly_review import DEFAULT_FUND_ORDER  # noqa: E402
except Exception:  # pragma: no cover - ordering is cosmetic only
    DEFAULT_FUND_ORDER = []


def _load(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _fund_slug(fund: str) -> str:
    return fund.lower().replace(" ", "-")


def _load_briefs(review_root: Path, snapshot_date: str, fund: str) -> dict[str, object]:
    """Load the three brief drafts for one fund, if present."""
    fund_dir = review_root / snapshot_date / _fund_slug(fund)
    briefs: dict[str, object] = {}
    for key, name in (
        ("change", "change_brief_draft.json"),
        ("sizing", "sizing_considerations_draft.json"),
        ("challenge", "challenge_brief_draft.json"),
    ):
        path = fund_dir / name
        if path.exists():
            try:
                briefs[key] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                briefs[key] = None
    return briefs


def build_viewer(
    multisignal_csv: Path,
    coverage_csv: Path,
    review_root: Path,
    output_html: Path,
) -> Path:
    rows = _load(multisignal_csv)
    coverage = _load(coverage_csv) if coverage_csv.exists() else []

    snapshot_date = max((r.get("snapshot_date", "") for r in rows), default="")
    source_file = next((r.get("source_file", "") for r in rows if r.get("source_file")), "")
    funds = sorted({r["fund"] for r in rows})
    if DEFAULT_FUND_ORDER:
        order = {f: i for i, f in enumerate(DEFAULT_FUND_ORDER)}
        funds.sort(key=lambda f: order.get(f, len(order)))

    briefs = {fund: _load_briefs(review_root, snapshot_date, fund) for fund in funds}

    payload = {
        "snapshot_date": snapshot_date,
        "source_file": source_file,
        "funds": funds,
        "rows": rows,
        "coverage": {c["fund"]: c for c in coverage},
        "briefs": briefs,
        "row_count": len(rows),
    }
    data_json = json.dumps(payload).replace("</", "<\\/")

    html = _TEMPLATE.replace("__DATA__", data_json)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html, encoding="utf-8")
    return output_html


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>MIM Analyst — Data &amp; Briefs Viewer</title>
<style>
  :root {
    --bg:#0f1115; --panel:#171a21; --panel2:#1e222b; --line:#2a2f3a;
    --text:#e6e9ef; --muted:#9aa4b2; --accent:#5b9dd9;
    --pos:#3fb27f; --neg:#e0685f; --warn:#e0b341;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
    font:14px/1.5 ui-sans-serif,system-ui,Segoe UI,Roboto,Helvetica,Arial; }
  header { padding:16px 24px; border-bottom:1px solid var(--line); background:var(--panel);
    display:flex; align-items:center; gap:20px; flex-wrap:wrap; }
  header h1 { margin:0; font-size:17px; font-weight:650; }
  header .meta { color:var(--muted); font-size:12px; }
  header .meta code { color:var(--accent); }
  .toggle { margin-left:auto; display:flex; gap:4px; background:var(--panel2); padding:3px; border-radius:9px; }
  .toggle button { background:transparent; color:var(--muted); border:0; padding:7px 16px; border-radius:7px;
    cursor:pointer; font-size:13px; font-weight:600; }
  .toggle button.active { background:var(--accent); color:#fff; }
  .wrap { display:flex; min-height:calc(100vh - 66px); }
  nav { width:250px; flex:0 0 250px; border-right:1px solid var(--line);
    background:var(--panel); padding:12px; overflow:auto; }
  nav button { display:block; width:100%; text-align:left; margin:2px 0; padding:9px 11px;
    background:transparent; color:var(--text); border:1px solid transparent; border-radius:7px;
    cursor:pointer; font-size:13px; }
  nav button:hover { background:var(--panel2); }
  nav button.active { background:var(--panel2); border-color:var(--accent); }
  nav button .badge { float:right; font-size:11px; color:var(--muted); }
  main { flex:1; padding:20px 24px; overflow:auto; }
  .cards { display:flex; flex-wrap:wrap; gap:12px; margin-bottom:18px; }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:10px;
    padding:12px 14px; min-width:130px; }
  .card .k { color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.04em; }
  .card .v { font-size:20px; font-weight:600; margin-top:3px; font-variant-numeric:tabular-nums; }
  .pill { display:inline-block; padding:2px 9px; border-radius:999px; font-size:12px; font-weight:600; }
  .pill.ok { background:rgba(63,178,127,.16); color:var(--pos); }
  .pill.no { background:rgba(224,179,65,.16); color:var(--warn); }
  h2 { font-size:13px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted);
    margin:22px 0 8px; font-weight:600; }
  h2 .sub { text-transform:none; font-weight:400; color:var(--muted); }
  .typegrid { display:flex; flex-wrap:wrap; gap:10px; }
  .typebox { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:11px 14px; }
  .typebox .t { font-size:12px; color:var(--accent); font-weight:600; }
  .typebox .nums { margin-top:6px; font-variant-numeric:tabular-nums; font-size:13px; }
  .typebox .nums span { color:var(--muted); }
  .toolbar { display:flex; gap:10px; align-items:center; margin:6px 0 10px; }
  .toolbar input { background:var(--panel2); border:1px solid var(--line); color:var(--text);
    padding:8px 11px; border-radius:7px; width:280px; font-size:13px; }
  .toolbar .count { color:var(--muted); font-size:12px; }
  table { width:100%; border-collapse:collapse; font-size:12.5px; }
  th, td { text-align:left; padding:7px 9px; border-bottom:1px solid var(--line); white-space:nowrap; }
  th { position:sticky; top:0; background:var(--panel); cursor:pointer; user-select:none;
    color:var(--muted); font-weight:600; }
  th:hover { color:var(--text); }
  th.sorted::after { content:" \25BE"; color:var(--accent); }
  th.sorted.asc::after { content:" \25B4"; }
  td.num { text-align:right; font-variant-numeric:tabular-nums; }
  td.pos { color:var(--pos); } td.neg { color:var(--neg); }
  td.sample, td.wrapcell { white-space:normal; color:var(--muted); max-width:420px; font-size:11.5px; }
  tr:hover td { background:rgba(91,157,217,.06); }
  .muted { color:var(--muted); }
  .banner { background:rgba(224,179,65,.10); border:1px solid rgba(224,179,65,.35); color:#e8d39a;
    border-radius:9px; padding:10px 14px; margin-bottom:16px; font-size:12.5px; }
  .summary { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:13px 16px;
    margin-bottom:16px; font-size:13.5px; }
  .countpills { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:6px; }
  .countpills .cp { background:var(--panel2); border:1px solid var(--line); border-radius:8px; padding:6px 11px;
    font-size:12px; }
  .countpills .cp b { font-variant-numeric:tabular-nums; }
  .item { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:12px 15px; margin:8px 0; }
  .item .acid { font-weight:650; }
  .item .tag { font-size:11px; color:var(--accent); margin-left:8px; }
  .item .narr { color:var(--muted); font-size:12.5px; margin-top:5px; }
  .item .empty { color:var(--warn); font-size:12px; }
  .kv { font-size:12.5px; } .kv b { color:var(--muted); font-weight:600; }
  .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media (max-width:1000px){ .grid2 { grid-template-columns:1fr; } }
</style>
</head>
<body>
<header>
  <h1>MIM Analyst</h1>
  <div class="meta">snapshot <code id="snap"></code> · source <code id="src"></code> ·
    <span id="rc"></span> rows · <span class="muted">local inspector</span></div>
  <div class="toggle">
    <button id="tab-exposures" class="active">Exposures</button>
    <button id="tab-briefs">Briefs</button>
  </div>
</header>
<div class="wrap">
  <nav id="nav"></nav>
  <main id="main"></main>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const COLS = [
  {k:"acid_type", label:"Type"}, {k:"acid", label:"ACID"},
  {k:"fund_target_rolled_exposure", label:"Target", num:true},
  {k:"fund_benchmark_rolled_exposure", label:"Bench", num:true},
  {k:"active_rolled_exposure", label:"Active", num:true, signed:true},
  {k:"vir_stf", label:"VIR STF", num:true},
  {k:"vir_delta_stf", label:"VIR dSTF", num:true},
  {k:"algo_active_weight", label:"Algo Act", num:true, signed:true},
  {k:"algo_perspective", label:"Perspective"},
  {k:"source_security_count", label:"Sec", num:true},
  {k:"sample_source_securities", label:"Sample Securities", sample:true},
];
let state = { view:"exposures", fund:DATA.funds[0], sort:"active_rolled_exposure", asc:false, filter:"" };

document.getElementById('snap').textContent = DATA.snapshot_date || "—";
document.getElementById('src').textContent = DATA.source_file || "—";
document.getElementById('rc').textContent = DATA.row_count;

function num(v){ if(v===""||v==null) return null; const n=parseFloat(v); return isNaN(n)?null:n; }
function fmt(v){ const n=num(v); return n==null?'<span class="muted">·</span>':n.toFixed(4); }
function esc(s){ return (s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function rowsFor(fund){ return DATA.rows.filter(r=>r.fund===fund); }

function perType(rows){
  const seen=new Set(), out={};
  for(const r of rows){
    const key=r.acid_type+'|'+r.acid; if(seen.has(key)) continue; seen.add(key);
    const t=r.acid_type; out[t]=out[t]||{target:0,bench:0};
    out[t].target+=num(r.fund_target_rolled_exposure)||0;
    out[t].bench+=num(r.fund_benchmark_rolled_exposure)||0;
  }
  return out;
}

function renderNav(){
  const nav=document.getElementById('nav'); nav.innerHTML='';
  for(const f of DATA.funds){
    const b=document.createElement('button');
    b.className=(f===state.fund?'active':'');
    const badge = state.view==='exposures' ? rowsFor(f).length
      : (((DATA.briefs[f]||{}).change||{}).triggers_fired_summary||{}).fired_count;
    b.innerHTML=esc(f.replace('MStar ',''))+'<span class="badge">'+(badge==null?'':badge)+'</span>';
    b.onclick=()=>{ state.fund=f; state.filter=''; render(); };
    nav.appendChild(b);
  }
}

function card(k,v){ return '<div class="card"><div class="k">'+k+'</div><div class="v">'+v+'</div></div>'; }

function renderExposures(){
  const rows=rowsFor(state.fund);
  const cov=DATA.coverage[state.fund]||{};
  const ok = String((rows[0]||{}).benchmark_coverage_ok).toLowerCase()==='true';
  const types=perType(rows);
  let view=rows.slice();
  if(state.filter){
    const q=state.filter.toLowerCase();
    view=view.filter(r=>(r.acid+' '+r.acid_type+' '+r.sample_source_securities).toLowerCase().includes(q));
  }
  view.sort((a,b)=>{
    const col=COLS.find(c=>c.k===state.sort)||{};
    let x=a[state.sort], y=b[state.sort];
    if(col.num){ x=num(x); y=num(y); x=(x==null?-Infinity:x); y=(y==null?-Infinity:y); return state.asc?x-y:y-x; }
    x=(x||'').toString(); y=(y||'').toString(); return state.asc?x.localeCompare(y):y.localeCompare(x);
  });
  const pct=(v)=>{const n=num(v);return n==null?'—':(n*100).toFixed(1)+'%';};
  let h='<div class="cards">';
  h+=card('Benchmark coverage','<span class="pill '+(ok?'ok':'no')+'">'+(ok?'OK':'NONE')+'</span>');
  h+=card('Target match',pct(cov.target_match_pct));
  h+=card('Benchmark match',pct(cov.benchmark_match_pct));
  h+=card('ACID rows',rows.length);
  h+='</div>';
  h+='<h2>Rolled exposure by ACID type <span class="sub">(deduped by ACID — sums within type, never across)</span></h2><div class="typegrid">';
  for(const t of Object.keys(types).sort())
    h+='<div class="typebox"><div class="t">'+esc(t)+'</div><div class="nums">target <b>'+types[t].target.toFixed(2)+'</b> &nbsp; <span>bench '+types[t].bench.toFixed(2)+'</span></div></div>';
  h+='</div><h2>ACID rows</h2>';
  h+='<div class="toolbar"><input id="filter" placeholder="filter by ACID / type / security…" value="'+esc(state.filter).replace(/"/g,'&quot;')+'"><span class="count">'+view.length+' of '+rows.length+' rows</span></div>';
  h+='<table><thead><tr>';
  for(const c of COLS){ const cls=(c.k===state.sort?'sorted '+(state.asc?'asc':''):'')+(c.num?' num':''); h+='<th class="'+cls+'" data-k="'+c.k+'">'+c.label+'</th>'; }
  h+='</tr></thead><tbody>';
  for(const r of view){
    h+='<tr>';
    for(const c of COLS){
      if(c.sample){ h+='<td class="sample">'+esc(r[c.k])+'</td>'; continue; }
      if(c.num){ const n=num(r[c.k]); let cls='num'; if(c.signed&&n!=null){ cls+=n>0?' pos':(n<0?' neg':''); }
        h+='<td class="'+cls+'">'+(c.k==='source_security_count'?esc(r[c.k]):fmt(r[c.k]))+'</td>'; }
      else { h+='<td>'+(r[c.k]?esc(r[c.k]):'<span class="muted">·</span>')+'</td>'; }
    }
    h+='</tr>';
  }
  h+='</tbody></table>';
  document.getElementById('main').innerHTML=h;
  document.querySelectorAll('th').forEach(th=>th.onclick=()=>{
    const k=th.dataset.k; if(state.sort===k) state.asc=!state.asc; else { state.sort=k; state.asc=false; } render();
  });
  const f=document.getElementById('filter');
  f.oninput=()=>{ state.filter=f.value; render(); const el=document.getElementById('filter'); el.focus(); el.setSelectionRange(el.value.length,el.value.length); };
}

function moverTable(movers){
  if(!movers||!movers.length) return '<div class="muted">none</div>';
  let h='<table><thead><tr><th>ACID</th><th class="num">Active</th><th class="num">Target</th><th class="num">Bench</th><th class="num">VIR STF</th><th>Narrative</th></tr></thead><tbody>';
  for(const m of movers){
    const a=num(m.active_rolled_exposure);
    h+='<tr><td>'+esc(m.acid)+'</td><td class="num '+(a>0?'pos':(a<0?'neg':''))+'">'+fmt(m.active_rolled_exposure)+
       '</td><td class="num">'+fmt(m.target_rolled_exposure)+'</td><td class="num">'+fmt(m.benchmark_rolled_exposure)+
       '</td><td class="num">'+fmt(m.vir_stf)+'</td><td class="wrapcell">'+esc(m.narrative)+'</td></tr>';
  }
  return h+'</tbody></table>';
}
function narrList(items){
  if(!items||!items.length) return '<div class="muted">none</div>';
  return items.map(i=>'<div class="item"><span class="acid">'+esc(i.acid)+'</span>'+
    (i.perspective?'<span class="tag">'+esc(i.perspective)+'</span>':'')+
    '<div class="narr">'+esc(i.narrative)+'</div></div>').join('');
}

function renderBriefs(){
  const b=DATA.briefs[state.fund]||{};
  const change=b.change, sizing=b.sizing, challenge=b.challenge;
  let h='';
  h+='<div class="banner">Brief drafts are <b>deterministic placeholders</b>: the narrative judgment fields '+
     '(cleaner expression, falsification framing, memory ops) are produced by the LLM agent, which is not built yet '+
     '(Tier 3). Numbers below reflect the corrected exposure data.</div>';
  if(!change){ document.getElementById('main').innerHTML=h+'<div class="muted">No brief drafts for this fund.</div>'; return; }

  const hd=change.header||{};
  h+='<div class="summary"><div class="kv"><b>run</b> '+esc(hd.review_run_id)+' &nbsp; <b>as-of</b> '+esc(hd.as_of_date)+
     ' &nbsp; <b>mode</b> '+esc(hd.run_mode)+' &nbsp; <b>mapping</b> '+esc(hd.mapping_version)+
     ' &nbsp; <b>governance</b> '+esc(hd.governance_version)+'</div>'+
     '<div style="margin-top:8px">'+esc(change.executive_summary)+'</div></div>';

  const ts=change.triggers_fired_summary||{};
  h+='<h2>Triggers</h2><div class="countpills">';
  [['candidates','candidate_count'],['fired','fired_count'],['borderline','borderline_count'],
   ['suppressed','suppressed_count'],['not triggered','not_triggered_count'],['not evaluable','not_evaluable_count']]
   .forEach(([lab,k])=>{ h+='<div class="cp">'+lab+' <b>'+(ts[k]==null?'—':ts[k])+'</b></div>'; });
  h+='</div>';

  h+='<h2>Change Brief — material movers <span class="sub">('+((change.material_movers||[]).length)+')</span></h2>'+moverTable(change.material_movers);

  if(sizing){
    h+='<h2>Sizing Considerations <span class="sub">'+esc(sizing.coverage_notes||'')+'</span></h2>';
    h+='<div class="grid2"><div><h2 style="margin-top:0">Algo agreement</h2>'+narrList(sizing.algo_vs_positioning_agreement)+'</div>'+
       '<div><h2 style="margin-top:0">Algo disagreement</h2>'+narrList(sizing.algo_vs_positioning_disagreement)+'</div></div>';
    h+='<h2>Largest algo MoM changes</h2>'+narrList(sizing.largest_algo_mom_changes);
  }

  h+='<h2>Challenge Brief</h2>';
  if(challenge && (challenge.items||[]).length){
    for(const it of challenge.items){
      h+='<div class="item"><span class="acid">'+esc(it.acid)+'</span><span class="tag">'+esc(it.trigger_type)+'</span>'+
         '<div class="narr">'+esc(it.disagreement_statement||it.challenge)+'</div>'+
         '<div class="empty">judgment fields empty (agent unbuilt): cleaner_expression · falsification_framing · next_review_checkpoint</div></div>';
    }
  } else { h+='<div class="muted">No challenge items (no triggers accepted for this fund).</div>'; }

  const mu=change.memory_updates_summary||{};
  const anyMem=Object.keys(mu).some(k=>k!=='proposed_memory_ops'&&mu[k]);
  h+='<h2>Memory updates</h2><div class="muted">'+(anyMem?JSON.stringify(mu):'No memory operations — proposed-only write path runs through the agent, which is not built yet.')+'</div>';

  document.getElementById('main').innerHTML=h;
}

function render(){
  document.getElementById('tab-exposures').className=(state.view==='exposures'?'active':'');
  document.getElementById('tab-briefs').className=(state.view==='briefs'?'active':'');
  renderNav();
  if(state.view==='exposures') renderExposures(); else renderBriefs();
}
document.getElementById('tab-exposures').onclick=()=>{ state.view='exposures'; render(); };
document.getElementById('tab-briefs').onclick=()=>{ state.view='briefs'; render(); };
render();
</script>
</body>
</html>
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a self-contained HTML data + briefs viewer.")
    parser.add_argument(
        "--multisignal-csv",
        default="artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv",
    )
    parser.add_argument(
        "--coverage-csv",
        default="artifacts/rolled_exposures/fund_rollthrough_coverage.csv",
    )
    parser.add_argument("--review-root", default="artifacts/monthly_review")
    parser.add_argument("--output-html", default="artifacts/data_viewer.html")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    out = build_viewer(
        Path(args.multisignal_csv),
        Path(args.coverage_csv),
        Path(args.review_root),
        Path(args.output_html),
    )
    print(f"data_viewer={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
