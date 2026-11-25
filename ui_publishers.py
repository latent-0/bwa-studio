"""Publisher status board (/publishers): publisher, campaign, start date and traffic seen, for click publishers (Everflow) and call publishers (Ringba)."""
import datetime as dt

import publishers
import ui
from ui import e, ico, shell

ui.CSS = ui.CSS + """
.pbsum{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:16px}
.pbsum div{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}.pbsum b{display:block;font:600 26px/1.1 var(--fd)}.pbsum span{font-size:12.5px;color:var(--mut)}
.pbbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px}.pbbar input{height:34px;padding:0 12px;min-width:220px;flex:1 1 220px;max-width:340px}
.pbbar .grow{flex:1}.pbbar .mut{font-size:12.5px}
.tbl.pbt td{white-space:nowrap;padding:10px 7px}.tbl.pbt th{white-space:normal;padding:0 7px 10px;vertical-align:bottom;line-height:1.3}.tbl.pbt td.pub{white-space:normal;min-width:110px}
.tbl.pbt td.camp{white-space:normal;min-width:160px;max-width:220px}.tbl.pbt td.dt{white-space:nowrap}
.tbl.pbt td.num{text-align:right;font:500 12.5px var(--fm)}.pbt th.num{text-align:right}.pbt small{display:block;color:var(--mut);font-size:11.5px}
.pbt tr.zero td.num{color:var(--faint)}
.rej.hi{color:var(--bad);font-weight:600}
.pbnote{font-size:12.5px;color:var(--mut);margin-top:10px;line-height:1.55}
@media(max-width:900px){.pbsum{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""

STATUS = {"live": ("ok", "Live"), "this_week": ("acc", "This week"), "quiet": ("warn", "Quiet 7d+"), "not_started": ("", "No traffic yet"), "pending": ("", "Pending")}
ORDER = {"live": 0, "this_week": 1, "quiet": 2, "not_started": 3, "pending": 4}


def _date(d):
    try:
        x = dt.date.fromisoformat(d)
        return f'<span title="{x.strftime("%d %b %Y")}">{x.strftime("%d %b")}</span>'
    except Exception:
        return ""


def _n(v):
    return f"{v:,}" if v else "0"


def publishers_page():
    b = publishers.board()
    rows = sorted(b.get("rows", []), key=lambda r: (ORDER.get(r["status"], 9), -r.get("d7", 0), -r.get("d30", 0), r["publisher"].lower()))
    counts = {k: sum(1 for r in rows if r["status"] == k) for k in STATUS}
    pubs_live = len({r["publisher"] for r in rows if r["status"] in ("live", "this_week")})
    trs = ""
    for r in rows:
        cls, lab = STATUS.get(r["status"], ("", r["status"]))
        start = _date(r.get("start"))
        if start and not r.get("start_exact"):
            start = f'<span title="Ringba cannot report calls by day, so this is the earliest window the publisher shows up in; the board keeps exact dates from now on">~{start}</span>'
        if not start and r.get("added"):
            start = f'<span class="mut">Added {_date(r["added"])}</span>'
        tot = r.get("d30", 0) + r.get("rej30", 0)
        hi = tot >= 20 and r.get("rej30", 0) / tot > 0.3
        money = f'${r["payout30"]:,.2f}' if r.get("payout30") else ("$0" if r.get("d30") else "")
        trs += (f'<tr data-st="{r["status"]}" data-src="{r["source"]}" data-q="{e((r["publisher"] + " " + r.get("campaign", "") + " " + r.get("buyer", "")).lower())}" class="{"zero" if not r.get("d30") else ""}">'
                f'<td class="pub"><b>{e(r["publisher"])}</b></td>'
                f'<td class="camp">{e(r.get("campaign") or "No campaign yet")}<small>{"Clicks" if r["source"] == "clicks" else "Calls"}{(" &middot; Buyer: " + e(r["buyer"])) if r.get("buyer") else ""}</small></td>'
                f'<td><span class="chip2 {cls}">{lab}</span></td>'
                f'<td class="dt">{start or "<span class=mut>Not yet</span>"}</td><td class="dt">{_date(r.get("last")) or ("<span class=mut>Over 7 days ago</span>" if r.get("d90") else "")}</td>'
                f'<td class="num">{_n(r.get("today", 0))}<small>{_n(r.get("yesterday", 0))}</small></td><td class="num">{_n(r.get("d7", 0))}</td><td class="num">{_n(r.get("d30", 0))}</td>'
                f'<td class="num rej{" hi" if hi else ""}" title="{"Over 30% of this traffic was rejected" if hi else ""}">{_n(r.get("rej30", 0))}</td>'
                f'<td class="num">{_n(r.get("conv30", 0))}</td><td class="num">{money}</td></tr>')
    if not trs:
        trs = '<tr><td colspan="11"><div class="empty">No publishers found. Check that Everflow and Ringba are connected on the Integrations page.</div></td></tr>'
    errs = "".join(f'<p class="note2" style="margin-bottom:12px">{e(x)}</p>' for x in b.get("errors", []))
    chips = "".join(f'<button data-f="{k}"{" class=on" if k == "all" else ""}>{lab} ({n})</button>' for k, lab, n in
                    [("all", "All", len(rows))] + [(k, STATUS[k][1], counts[k]) for k in STATUS])
    body = (f'<div class="pagehead"><div><h1>Publishers</h1><p>Every publisher sending us traffic, per campaign: when they started, when we last saw traffic, and how much. '
            f'Clicks come from Everflow, calls from Ringba. Rejected means invalid or duplicate clicks, or duplicate calls; a red count means more than 30% was rejected.</p></div></div>{errs}'
            f'<div class="pbsum"><div><b>{counts["live"]}</b><span>Live today or yesterday</span></div><div><b>{counts["this_week"]}</b><span>Active this week, quiet the last 2 days</span></div>'
            f'<div><b>{counts["quiet"]}</b><span>Quiet for 7+ days</span></div><div><b>{counts["not_started"] + counts["pending"]}</b><span>Set up, no traffic yet</span></div></div>'
            f'<div class="pbbar"><div class="filters" id="pbf">{chips}</div><div class="grow"></div>'
            f'<select id="pbsrc" aria-label="Traffic type" style="height:34px"><option value="">Clicks and calls</option><option value="clicks">Clicks only</option><option value="calls">Calls only</option></select>'
            f'<input id="pbq" type="search" placeholder="Search publisher, campaign or buyer" aria-label="Search publishers">'
            f'<span class="mut">Updated {e(b.get("refreshed", "")[5:16])}</span><button class="btn" id="pbr" type="button">{ico("clock")}Refresh</button></div>'
            f'<section class="panel"><table class="tbl pbt"><thead><tr><th>Publisher</th><th>Campaign</th><th>Status</th><th>Started</th><th>Last<br>traffic</th>'
            f'<th class="num">Today<small>Yesterday</small></th><th class="num">7<br>days</th><th class="num">30<br>days</th><th class="num">Rejected<br>30d</th><th class="num">Converted<br>30d</th><th class="num">Payout<br>30d</th></tr></thead>'
            f'<tbody id="pbt">{trs}</tbody></table></section>'
            f'<p class="pbnote">{pubs_live} publishers sent traffic in the last 7 days. Start dates marked ~ are estimates for call publishers that were already running before this board existed; '
            f'the board records the exact day for anyone who starts from now on. Data refreshes every {publishers.REFRESH_MIN} minutes when the page is opened.</p>')
    js = """<script>(function(){
var f='all',src='',q='';
function draw(){document.querySelectorAll('#pbt tr[data-st]').forEach(function(tr){var ok=(f==='all'||tr.getAttribute('data-st')===f)&&(!src||tr.getAttribute('data-src')===src)&&(!q||tr.getAttribute('data-q').indexOf(q)>-1);tr.style.display=ok?'':'none';});}
document.querySelectorAll('#pbf button').forEach(function(b){b.onclick=function(){f=b.getAttribute('data-f');document.querySelectorAll('#pbf button').forEach(function(x){x.classList.toggle('on',x===b);});draw();};});
document.getElementById('pbsrc').onchange=function(){src=this.value;draw();};
document.getElementById('pbq').oninput=function(){q=this.value.trim().toLowerCase();draw();};
var r=document.getElementById('pbr');r.onclick=function(){r.disabled=true;fetch('/api/publishers/refresh',{method:'POST',body:'{}'}).then(function(x){return x.json();}).then(function(j){if(j.ok){location.reload();}else{toast(j.error||'Refresh failed',false);r.disabled=false;}}).catch(function(){toast('Refresh failed',false);r.disabled=false;});};
})();</script>"""
    return shell("Publishers", body, "publishers", "<b>Publishers</b>", js)
