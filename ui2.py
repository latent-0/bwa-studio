"""Studio UI part 2: Launch board, Ops dashboard, CRM board, Integrations page, and the brand workspace tabs
(Go-live, Compliance, Integrations, Video, Activity). Imported by the server; extends ui.CSS and ui.SPRITE."""
import html
import json

import compliance
import core
import integrations
import publish
import store
import ui
import video
from ui import e, ico, shell

ui.SPRITE = ui.SPRITE.replace("</defs></svg>", """
<symbol id="i-rocket" viewBox="0 0 24 24"><path d="M5 15c-1.5 1.5-2 5-2 5s3.5-.5 5-2M14 4c3-1.5 6-1 6-1s.5 3-1 6l-5 5-4-4z"/><circle cx="15.5" cy="8.5" r="1.3"/><path d="M9 11l-3 .5L4 9l4-1M13 15l-.5 3L15 20l1-4"/></symbol>
<symbol id="i-chart" viewBox="0 0 24 24"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></symbol>
<symbol id="i-users" viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6M16 4.8a3.5 3.5 0 0 1 0 6.4M18 14.2c2 .7 3.5 2.6 3.5 5.8"/></symbol>
<symbol id="i-plug" viewBox="0 0 24 24"><path d="M9 3v5M15 3v5M6 8h12v3a6 6 0 0 1-12 0zM12 17v4"/></symbol>
<symbol id="i-play" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></symbol>
<symbol id="i-video" viewBox="0 0 24 24"><rect x="3" y="6" width="13" height="12" rx="2.5"/><path d="M16 10l5-3v10l-5-3"/></symbol>
<symbol id="i-shield" viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/></symbol>
</defs></svg>""")

CSS2 = """
.tabs{display:flex;gap:4px;margin:0 0 14px;padding:4px;border-radius:14px;background:var(--surface);border:1px solid var(--line);flex-wrap:wrap}
.tabs button{height:36px;padding:0 14px;border:0;border-radius:10px;background:transparent;color:var(--mut);cursor:pointer;font-weight:500;font-size:13.5px;display:inline-flex;align-items:center;gap:8px;transition:background .2s,color .2s}
.tabs button:hover{color:var(--ink)}.tabs button.on{background:var(--surface2);color:var(--ink);box-shadow:inset 0 0 0 1px var(--line2)}
.tabs .tdot{min-width:18px;height:18px;border-radius:9px;background:var(--bad);color:#fff;font-size:11px;display:inline-grid;place-items:center;padding:0 5px}.tabs .tdot.ok{background:var(--ok)}.tabs .tdot.mut{background:var(--faint)}
.tp{display:none}.tp.on{display:block}
.chip2{display:inline-flex;align-items:center;gap:6px;height:24px;padding:0 10px;border-radius:99px;font-size:12px;font-weight:500;background:var(--surface2);color:var(--mut);border:1px solid var(--line);white-space:nowrap}
.chip2.ok{color:var(--ok);background:color-mix(in srgb,var(--ok) 13%,transparent);border-color:transparent}.chip2.bad{color:var(--bad);background:color-mix(in srgb,var(--bad) 12%,transparent);border-color:transparent}
.chip2.warn{color:var(--warn);background:color-mix(in srgb,var(--warn) 13%,transparent);border-color:transparent}.chip2.acc{color:var(--accent);background:color-mix(in srgb,var(--accent) 14%,transparent);border-color:transparent}
.banner{display:flex;align-items:center;gap:14px;padding:16px 18px;border-radius:16px;border:1px solid var(--line);background:var(--surface2);margin-bottom:14px;flex-wrap:wrap}
.banner.live{background:color-mix(in srgb,var(--ok) 12%,var(--surface));border-color:color-mix(in srgb,var(--ok) 35%,transparent)}
.banner b{font:600 16px var(--fd)}.banner .grow{flex:1;min-width:180px}.banner small{display:block;color:var(--mut);font-size:12.5px}
.steps2{display:grid;gap:8px;margin:14px 0}.st2{display:flex;align-items:center;gap:12px;padding:12px 14px;border:1px solid var(--line);border-radius:14px;background:var(--surface2)}
.st2 .t{flex:1;min-width:0}.st2 .t b{display:block;font-weight:500}.st2 .t span{color:var(--mut);font-size:12.5px}
table.tbl{width:100%;border-collapse:collapse;font-size:13.5px}.tbl th{font:500 11px var(--fb);letter-spacing:.12em;text-transform:uppercase;color:var(--faint);text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
.tbl td{padding:10px;border-bottom:1px solid var(--line);vertical-align:top}.tbl tr:last-child td{border-bottom:0}.tbl .mut{color:var(--mut)}
.ctx{color:var(--mut);font-size:12.5px;margin-top:2px;max-width:46em}
.cgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}.icard{border:1px solid var(--line);border-radius:16px;padding:16px;background:var(--surface2)}
.icard h3{font-size:15px;display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px}.icard .row{margin-top:8px}.icard p{margin:6px 0 0;color:var(--mut);font-size:12.5px}
.icard label{display:block;font-size:12px;color:var(--mut);margin:10px 0 4px}
.vrow{border:1px solid var(--line);border-radius:14px;background:var(--surface2);margin-bottom:8px;overflow:hidden}.vrow .vh{cursor:default}
.vrow video{width:100%;max-height:420px;background:#000;display:block}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:18px}.kpi{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px}
.kpi span{display:block;color:var(--mut);font-size:12.5px;margin-bottom:6px}.kpi b{font:600 24px/1 var(--fd);letter-spacing:-.03em}
.alerts{display:grid;gap:8px;margin-bottom:18px}.al{display:flex;gap:10px;align-items:flex-start;padding:11px 14px;border-radius:13px;font-size:13.5px;border:1px solid var(--line);background:var(--surface)}
.al.bad{background:color-mix(in srgb,var(--bad) 10%,var(--surface));border-color:color-mix(in srgb,var(--bad) 35%,transparent)}.al.warn{background:color-mix(in srgb,var(--warn) 9%,var(--surface))}.al.info{color:var(--mut)}
.al .i{margin-top:2px;width:16px;height:16px}
.spark{display:block}.sb{display:flex;align-items:center;gap:10px}
.kanban{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(230px,1fr);gap:12px;overflow-x:auto;padding-bottom:8px}
.kcol{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:12px;min-height:160px}.kcol h4{font:500 12px var(--fb);letter-spacing:.1em;text-transform:uppercase;color:var(--mut);margin:2px 4px 10px;display:flex;justify-content:space-between}
.kcard{background:var(--surface2);border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin-bottom:8px;font-size:13px}.kcard b{display:block;font-weight:500}.kcard span{color:var(--mut);font-size:12px}
.pill-tabs{display:inline-flex;gap:4px;padding:4px;border-radius:12px;background:var(--surface);border:1px solid var(--line);margin-bottom:14px}.pill-tabs button{height:32px;padding:0 14px;border:0;border-radius:9px;background:transparent;color:var(--mut);cursor:pointer;font-weight:500;font-size:13px}.pill-tabs button.on{background:var(--surface2);color:var(--ink);box-shadow:inset 0 0 0 1px var(--line2)}
.dots7{display:inline-flex;gap:4px}.dots7 i{width:9px;height:9px;border-radius:50%;background:var(--bad);display:block}.dots7 i.ok{background:var(--ok)}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}.filters button{height:32px;padding:0 14px;border-radius:99px;border:1px solid var(--line);background:var(--surface);color:var(--mut);cursor:pointer;font-size:13px}.filters button.on{background:var(--surface2);color:var(--ink);border-color:var(--line2)}
.chip2 .x{border:0;background:transparent;color:inherit;cursor:pointer;font-size:15px;line-height:1;padding:0 0 0 2px;flex:none}.chip2:has(.x){overflow:visible;white-space:normal;height:auto;min-height:24px;padding:2px 10px}
.note2{background:var(--surface2);border:1px dashed var(--line2);border-radius:14px;padding:12px 14px;color:var(--mut);font-size:12.5px;margin-top:12px}
.side{overflow-y:auto}.pagehead div[style*="display:flex"]{flex-wrap:wrap}.pagehead>div{min-width:0}.main,.content,.col,.panel,.ws>*{min-width:0}.row{flex-wrap:wrap}.st2{flex-wrap:wrap}.st2 .t{flex:1 1 200px}
.cgrid{grid-template-columns:repeat(auto-fit,minmax(min(280px,100%),1fr))}.icard input[type=text]{width:100%}
table.tbl{display:block;max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}
.chip2{max-width:100%;overflow:hidden;text-overflow:ellipsis}.banner .btn,.st2 .btn{flex:0 0 auto}
@media(max-width:560px){.kpis{grid-template-columns:1fr 1fr}.tabs{overflow-x:auto;flex-wrap:nowrap}.tabs button{flex:0 0 auto}.banner{padding:14px}}
@media(max-width:1180px){.kpis{grid-template-columns:repeat(3,1fr)}}@media(max-width:560px){.kpis{grid-template-columns:1fr 1fr}}
"""
ui.CSS = ui.CSS + CSS2

STAGE_CLASS = {"Live": "ok", "Ready to launch": "ok", "Ready to test": "acc", "Legal review": "warn", "Generated": "", "Draft": "", "Paused": "bad"}
NEXT = {"page": "Generate the page", "tracking": "Regenerate to add the tracking script", "compliance": "Regenerate to build the compliance pages",
        "buyer": "Confirm a buyer", "legal": "Clear claims and get counsel sign-off"}
# Display names only. The stored stage names stay the same because GoHighLevel matches on them.
STAGE_LABEL = {"New call": "New prospects"}
DELIV_LABEL = {"calls": "Calls", "clicks": "Clicks", "leads": "Leads"}


def stage_chip(stage):
    return f'<span class="chip2 {STAGE_CLASS.get(stage, "")}">{e(stage)}</span>'


# ------------------------------------------------------------------ Launch board

def launch_page():
    rows = ""
    brands = core.load_brands()
    sheets = core.sheet_info()
    counts = {"all": len(brands), "todo": 0, "review": 0, "ready": 0, "live": 0}
    for b in brands:
        s = b["slug"]
        cl = core.checklist(s)
        ls = publish.live_status(s)
        stage = integrations.desired_stage(s)
        failing = [i for i in cl["items"] if not i["ok"]]
        group = "live" if ls["live"] else ("ready" if cl["ready"] else ("review" if stage in ("Legal review", "Ready to test") else "todo"))
        counts[group] += 1
        dots = "".join(f'<i class="{"ok" if i["ok"] else ""}" title="{e(i["label"])}: {e(i["detail"])}"></i>' for i in cl["items"])
        nxt = "Live" if ls["live"] else ("Ready to publish" if cl["ready"] else (failing[0]["detail"] if failing[0]["key"] in ("delivery", "test") else NEXT.get(failing[0]["key"], "")))
        sb = sheets.get(s) or {}
        star = '<span class="chip2 acc" style="margin-left:6px">High</span>' if sb.get("priority") == "High" else ('<span class="chip2 ok" style="margin-left:6px">Done</span>' if sb.get("priority") == "Done" else "")
        down = ' <span class="chip2 bad" title="The Sheet marks this website as not up">site down</span>' if str(sb.get("site_up", "")).strip().upper() == "N" else ""
        deliv = " ".join(f'<span class="chip2">{DELIV_LABEL[m]}</span>' for m in cl["delivery"])
        act = (f'<button class="btn primary" data-pub="{s}">{ico("rocket")}Publish</button>' if (cl["ready"] and not ls["live"]) else f'<a class="btn" href="/studio/{s}">Open{ico("arrow")}</a>')
        rows += (f'<tr data-g="{group}"><td><div class="sb"><span class="avatar sm" style="--c:{e(b["accent_color"] or "#6b8cff")}">{e(b["name"][:1])}</span><div><b>{e(b["name"])}</b>{star}{down}<div class="mut" style="font-size:12px;text-transform:capitalize">{e(b["vertical"])}</div></div></div></td>'
                 f'<td>{deliv}</td><td>{stage_chip(stage)}</td><td><span class="dots7">{dots}</span></td><td class="mut">{e(nxt)}</td><td style="text-align:right;white-space:nowrap">{act}</td></tr>')
    f = lambda k, label: f'<button data-f="{k}" class="{"on" if k == "all" else ""}">{label} ({counts[k]})</button>'
    body = (f'<div class="pagehead"><div><h1>Launch board</h1><p>Every brand, where it stands, and the next thing it needs. Seven checks must pass before a brand can go live.</p></div>'
            f'<div style="display:flex;gap:8px"><button class="btn" id="genall">{ico("spark")}Generate missing</button><button class="btn" id="genall2">Regenerate all</button><button class="btn" id="automap">{ico("plug")}Auto-map campaigns</button></div></div>'
            f'<div class="filters">{f("all", "All")}{f("todo", "To do")}{f("review", "In review")}{f("ready", "Ready")}{f("live", "Live")}</div>'
            f'<section class="panel"><table class="tbl"><thead><tr><th>Brand</th><th>Delivery</th><th>Stage</th><th>Checks</th><th>Next step</th><th></th></tr></thead><tbody id="lb">{rows}</tbody></table>'
            f'<p class="note2">Checks, in order: page, delivery set up, tracking, compliance pages, buyer, legal review, test delivery. Calls use Ringba, clicks use Everflow, leads use LeadProsper. Brands, priority, buyers and site status come from the Google Sheet.</p></section>')
    js = """<script>(function(){
 function api(u,b){return fetch(u,{method:'POST',body:JSON.stringify(b||{})}).then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});});}
 document.querySelectorAll('.filters button').forEach(function(b){b.onclick=function(){document.querySelectorAll('.filters button').forEach(function(x){x.classList.toggle('on',x===b);});var f=b.getAttribute('data-f');document.querySelectorAll('#lb tr').forEach(function(r){r.style.display=(f==='all'||r.getAttribute('data-g')===f)?'':'none';});};});
 function gen(missing,btn){btn.disabled=true;api('/api/bulk/generate',{missing_only:missing}).then(function(x){toast('Generated '+x.j.generated.length+' brand'+(x.j.generated.length===1?'':'s'));setTimeout(function(){location.reload();},700);});}
 document.getElementById('automap').onclick=function(){var b=this;b.disabled=true;api('/api/mapping/automap',{}).then(function(x){var n=(x.j.result||[]).length;toast(n?('Mapped campaigns for '+n+' brand'+(n===1?'':'s')):'Nothing new to map');setTimeout(function(){location.reload();},900);});};
 document.getElementById('genall').onclick=function(){gen(true,this);};document.getElementById('genall2').onclick=function(){gen(false,this);};
 document.querySelectorAll('[data-pub]').forEach(function(b){b.onclick=function(){b.disabled=true;api('/api/publish',{slug:b.getAttribute('data-pub'),note:'Published from the launch board'}).then(function(x){if(x.ok){toast('Brand is live');setTimeout(function(){location.reload();},700);}else{toast(x.j.error||'Could not publish',false);b.disabled=false;}});};});
})();</script>"""
    return shell("Launch board", body, "launch", "<b>Launch board</b>", js)


# ------------------------------------------------------------------ Ops dashboard

def spark(series, color, w=120, h=28):
    mx = max(series) or 1
    n = len(series)
    pts = " ".join(f"{i * (w - 4) / max(1, n - 1) + 2:.1f},{h - 3 - (v / mx) * (h - 8):.1f}" for i, v in enumerate(series))
    return f'<svg class="spark" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def ops_page(days=14):
    o = integrations.ops(days)
    t = o["total"]
    live_n = sum(1 for r in o["rows"] if r["live"])
    rpc = round(t["revenue"] / t["clicks"], 2) if t["clicks"] else 0
    k = lambda label, val: f'<div class="kpi"><span>{label}</span><b>{val}</b></div>'
    rf = o["refresh"]
    age = ("never" if rf["age_seconds"] is None else (f"{rf['age_seconds'] // 60} min ago" if rf["age_seconds"] >= 60 else "just now"))
    al = "".join(f'<div class="al {a["level"]}">{ico("warn" if a["level"] != "info" else "clock")}<span>{e(a["msg"])}</span></div>' for a in o["alerts"]) or '<div class="al info">No alerts.</div>'
    rows = "".join(
        f'<tr><td><div class="sb"><span class="avatar sm" style="--c:{e(r["color"])}">{e(r["name"][:1])}</span><a href="/studio/{r["slug"]}"><b>{e(r["name"])}</b></a></div></td><td>{stage_chip(r["stage"])}</td>'
        f'<td>{r["clicks"]:,}</td><td>{r["calls"]:,}</td><td>{r["converted"]:,}</td><td>{r["accepted"]:,}<span class="mut"> / {r["leads"]:,}</span></td><td>${r["revenue"]:,.0f}</td><td>${r["rpc"]:.2f}</td><td>{spark(r["series"], r["color"])}</td></tr>' for r in o["rows"])
    sandbox = ('<div class="al warn">' + ico("warn") + '<span><b>Sandbox data.</b> Ringba, Everflow or LeadProsper is not connected, so its numbers are simulated for brands that are live. Add credentials on the Integrations page to see real numbers.</span></div>') if o["sandbox"] else ""
    dsel = "".join(f'<a class="btn{" primary" if d == days else ""}" href="/ops?days={d}">{d} days</a>' for d in (7, 14, 30))
    body = (f'<div class="pagehead"><div><h1>Ops dashboard</h1><p>Clicks (Everflow), calls (Ringba) and leads (LeadProsper) per brand, with alerts for anything that needs attention. Last refreshed {age}.</p></div><div style="display:flex;gap:8px">{dsel}<button class="btn" id="rf">Refresh live data</button></div></div>'
            f'{sandbox}<div class="kpis">{k("Live brands", live_n)}{k("Clicks", f"{t["clicks"]:,}")}{k("Calls", f"{t["calls"]:,}")}{k("Leads accepted", f"{t["accepted"]:,}")}{k("Revenue", f"${t["revenue"]:,.0f}")}{k("Revenue per click", f"${rpc:.2f}")}</div>'
            f'<h2 style="font:500 12px var(--fb);letter-spacing:.14em;text-transform:uppercase;color:var(--mut);margin:0 0 10px">Alerts</h2><div class="alerts">{al}</div>'
            f'<section class="panel"><h2>Brands, last {days} days</h2><table class="tbl"><thead><tr><th>Brand</th><th>Stage</th><th>Clicks</th><th>Calls</th><th>Converted</th><th>Leads</th><th>Revenue</th><th>RPC</th><th>Calls and leads per day</th></tr></thead><tbody>{rows}</tbody></table></section>')
    js = """<script>document.getElementById('rf').onclick=function(){var b=this;b.disabled=true;b.textContent='Refreshing...';
  fetch('/api/refresh').then(function(r){return r.json();}).then(function(st){
    if(st.serverless){
      fetch('/api/refresh/brands').then(function(r){return r.json();}).then(function(list){var i=0;(function next(){
        if(i>=list.length){location.reload();return;}b.textContent='Refreshing '+(i+1)+' of '+list.length;
        fetch('/api/refresh',{method:'POST',body:JSON.stringify({slug:list[i++]})}).then(next,next);})();});
    } else {
      fetch('/api/refresh',{method:'POST',body:'{}'}).then(function(){var n=0;(function poll(){fetch('/api/refresh').then(function(r){return r.json();}).then(function(s){if(s.running&&n++<60){setTimeout(poll,2000);}else{location.reload();}});})();});
    }
  });};</script>"""
    return shell("Ops", body, "ops", "<b>Ops dashboard</b>", js)


# ------------------------------------------------------------------ CRM board (GoHighLevel)

def crm_page():
    board = integrations.board()
    m = integrations.mode("ghl")
    total_contacts = store.q("select count(*) n from ghl_contacts")[0]["n"]
    tabs = "".join(f'<button data-p="{i}" class="{"on" if i == 0 else ""}">{e(name)}</button>' for i, name in enumerate(board))
    panels = ""
    for i, (name, cols) in enumerate(board.items()):
        cc = ""
        for c in cols:
            cards = "".join(f'<div class="kcard"><b>{e(o["name"])}</b><span>{("$%.0f &middot; " % o["value"]) if o["value"] else ""}{e(o["updated"][5:16])}</span></div>' for o in c["items"][:30])
            more = f'<span class="mut" style="font-size:12px">+{len(c["items"]) - 30} more</span>' if len(c["items"]) > 30 else ""
            cc += f'<div class="kcol"><h4><span>{e(STAGE_LABEL.get(c["stage"], c["stage"]))}</span><span>{len(c["items"])}</span></h4>{cards}{more}</div>'
        panels += f'<div class="pn" data-p="{i}" style="display:{"block" if i == 0 else "none"}"><div class="kanban">{cc}</div></div>'
    mode = ('<span class="chip2 ok">Live</span>' if m == "live" else '<span class="chip2 warn">Sandbox</span>')
    note = ("" if m == "live" else '<p class="note2">Sandbox CRM: these records live in the studio database and mimic GoHighLevel. Add GHL_TOKEN and GHL_LOCATION_ID on the Integrations page to write to your real location. You will need the three pipelines below with these exact stage names.</p>')
    js = """<script>document.querySelectorAll('.pill-tabs button').forEach(function(b){b.onclick=function(){var p=b.getAttribute('data-p');document.querySelectorAll('.pill-tabs button').forEach(function(x){x.classList.toggle('on',x===b);});document.querySelectorAll('.pn').forEach(function(n){n.style.display=n.getAttribute('data-p')===p?'block':'none';});};});</script>"""
    body = (f'<div class="pagehead"><div><h1>CRM {mode}</h1><p>GoHighLevel pipelines driven by the studio: brand launch stages, every call as a lead, and the partner onboarding SOP. {total_contacts} contacts.</p></div></div>'
            f'<div class="pill-tabs">{tabs}</div><section class="panel" style="padding:16px">{panels}</section>{note}')
    return shell("CRM", body, "crm", "<b>CRM</b>", js)


# ------------------------------------------------------------------ Integrations page

def integrations_page():
    st = integrations.status()
    ff = video.ffmpeg()
    import shutil
    ff_ok = bool(shutil.which("ffmpeg"))
    cards = ""
    info = {"ringba": ("Calls: numbers, call logs, buyers and payouts", [("account_id", "Account ID"), ("api_key", "API key")], "Gives each brand its tracking number and pulls call logs for the ops dashboard. Pick each brand's campaigns in its Integrations tab."),
            "everflow": ("Clicks: offers, click and conversion reporting", [("api_key", "API key")], "Pulls valid clicks and conversions per offer. Pick each brand's offers in its Integrations tab."),
            "gemini": ("AI: reads landing page images and writes copy", [("api_key", "API key")], "Used to read the sales pitch off an uploaded image and to write page copy from a prompt. Without a key the studio falls back to Claude or the offline templates."),
            "leadprosper": ("Lead delivery: leads posted to buyers", [("token", "API token")], "Pulls delivered, accepted, duplicated and failed leads with revenue, and posts test leads. Pick each brand's campaigns in its Integrations tab."),
            "ghl": ("CRM pipelines and workflows", [("token", "Private integration token"), ("location_id", "Location ID")], "Used to create contacts and opportunities and to move brands through the Brand launch pipeline.")}
    for n, (sub, fields, blurb) in info.items():
        s = st[n]
        inputs = "".join(f'<label>{lab}</label><input type="text" data-n="{n}" data-k="{k}" placeholder="{e(s["fields"].get(k) or "not set")}" autocomplete="off">' for k, lab in fields)
        cards += (f'<div class="icard"><h3><span>{s["label"]}</span><span class="chip2 {"ok" if s["mode"] == "live" else "warn"}">{s["mode"].title()}</span></h3><div class="mut" style="font-size:13px">{sub}</div>'
                  f'<p>{blurb}</p>{inputs}<div class="row"><button class="btn" data-save="{n}">Save</button><button class="btn" data-test="{n}">Test connection</button></div><p id="r-{n}"></p></div>')
    import sheet
    sst = sheet.status()
    sheet_card = (f'<div class="icard"><h3><span>Google Sheet</span><span class="chip2 {"ok" if "live" in sst["source"] else "warn"}">{e(sst["source"])}</span></h3><div class="mut" style="font-size:13px">Control panel: brands, buyers, priority and site status</div>'
                  f'<p>{len(sheet.roster())} brands from the Priority List, merged with the URLs/Brands, Ringba and Inventory Draft tabs. The Sheet is read-only from here: edit it there and it updates within two minutes.</p>'
                  f'<div class="row"><a class="btn" target="_blank" href="{e(sheet.sheet_url())}">{ico("ext")}Open the Sheet</a><button class="btn" id="shrf">Refresh now</button></div></div>')
    pip = "".join(f'<li><b>{e(k)}</b>: {e(", ".join(v))}</li>' for k, v in integrations.PIPELINES.items())
    body = (f'<div class="pagehead"><div><h1>Integrations</h1><p>Ringba handles calls, Everflow handles clicks, LeadProsper delivers leads and GoHighLevel is the CRM. Without credentials each one runs in a clearly labeled sandbox.</p></div></div>'
            f'<div class="cgrid">{sheet_card}{cards}</div>'
            f'<section class="panel" style="margin-top:16px"><h2>Before you go live</h2><ul style="margin:0;padding-left:18px;color:var(--mut);font-size:13.5px;line-height:1.8">'
            f'<li>Prefer environment variables for secrets: RINGBA_ACCOUNT_ID, RINGBA_API_KEY, EVERFLOW_API_KEY, LEADPROSPER_API_TOKEN, GHL_TOKEN, GHL_LOCATION_ID. Saved values go to <code>data/integrations.json</code> on this machine in plain text.</li>'
            f'<li>Ringba, Everflow and LeadProsper requests were verified read-only against the real accounts. GoHighLevel is still unverified, so use <b>Test connection</b> when its token is added. Nothing here edits campaigns inside those accounts.</li>'
            f'<li>GoHighLevel needs these pipelines and exact stage names:<ul style="margin-top:6px">{pip}</ul></li>'
            f'<li>Everflow postback template: <code>{e(integrations.postback_template())}</code></li>'
            f'<li>Per-brand tracking tags: paste the Ringba and Everflow tags into <code>data/snippets/&lt;brand&gt;/ringba_snippet.html</code> and <code>everflow_snippet.html</code>, then regenerate.</li></ul>'
            f'<div class="row" style="margin-top:14px"><label class="btn" style="gap:10px"><input type="checkbox" id="fs" {"checked" if st["force_sandbox"] else ""}> Force sandbox mode for everything</label></div></section>'
            f'<section class="panel"><h2>Video engine</h2><div class="row" style="align-items:center"><span class="chip2 {"ok" if ff_ok else "bad"}">ffmpeg {"found" if ff_ok else "missing"}</span>'
            f'<span class="chip2 {"ok" if video.FONT else "warn"}">{"Font found" if video.FONT else "No font found"}</span><span class="chip2 acc">Voice: placeholder (Windows speech)</span>'
            f'<a class="btn" href="/api/video/tracker.csv">{ico("ext")}Download Video Tracker CSV</a></div></section>')
    js = """<script>(function(){
 function api(u,b){return fetch(u,{method:'POST',body:JSON.stringify(b||{})}).then(function(r){return r.json();});}
 document.querySelectorAll('[data-save]').forEach(function(b){b.onclick=function(){var n=b.getAttribute('data-save'),o={};o[n]={};document.querySelectorAll('input[data-n="'+n+'"]').forEach(function(i){if(i.value.trim()){o[n][i.getAttribute('data-k')]=i.value.trim();}});api('/api/integrations/save',o).then(function(){toast('Saved');setTimeout(function(){location.reload();},600);});};});
 document.querySelectorAll('[data-test]').forEach(function(b){b.onclick=function(){var n=b.getAttribute('data-test');api('/api/integrations/test',{name:n}).then(function(r){var el=document.getElementById('r-'+n);el.textContent=(r.ok?'OK: ':'Failed: ')+r.detail;el.style.color=r.ok?'var(--ok)':'var(--bad)';});};});
 document.getElementById('shrf').onclick=function(){var b=this;b.disabled=true;api('/api/sheet/refresh',{}).then(function(r){toast('Sheet refreshed: '+r.brands+' brands');setTimeout(function(){location.reload();},600);});};
 document.getElementById('fs').onchange=function(){api('/api/integrations/save',{force_sandbox:this.checked}).then(function(){toast('Updated');setTimeout(function(){location.reload();},500);});};
})();</script>"""
    return shell("Integrations", body, "integrations", "<b>Integrations</b>", js)
