"""Daily report page (/report): part 1 the lot (item 35), part 2 affiliate campaigns (item 36), with a copy-ready text version."""
import lot
import ui
from ui import e, ico, shell

ui.CSS = ui.CSS + """
.rpsum{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:16px}
.rpsum div{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}.rpsum b{display:block;font:600 26px/1.1 var(--fd)}.rpsum span{font-size:12.5px;color:var(--mut)}
.rpsum b.neg{color:var(--bad)}.rpsum b.pos{color:var(--ok)}
.rph{display:flex;align-items:baseline;gap:10px;margin:22px 0 10px}.rph h2{margin:0;font:600 18px var(--fd)}.rph span{color:var(--mut);font-size:12.5px}
.stagebar{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}.stagebar span{background:var(--surface2);border-radius:999px;padding:5px 11px;font-size:12px;color:var(--mut)}.stagebar b{color:var(--ink);margin-left:4px}
.mv{list-style:none;margin:0;padding:0;display:grid;gap:6px}.mv li{display:flex;gap:10px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:9px 12px;font-size:13px}
.mv li i{font-style:normal;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font:700 12px var(--fb);flex:none}
.mv li.up i,.mv li.new i{background:color-mix(in srgb,var(--ok) 16%,transparent);color:var(--ok)}.mv li.down i,.mv li.gone i{background:color-mix(in srgb,var(--bad) 14%,transparent);color:var(--bad)}
.mv li small{color:var(--mut);margin-left:auto;font-size:11.5px}
.tbl.rpt td{padding:9px 7px;vertical-align:top}.tbl.rpt th{padding:0 7px 9px;vertical-align:bottom;line-height:1.3}.tbl.rpt td.num,.tbl.rpt th.num{text-align:right;white-space:nowrap}.tbl.rpt td.num{font-family:var(--fm);font-size:12.5px}.rpwrap{overflow-x:auto}
.rpt small{display:block;color:var(--mut);font-size:11.5px;line-height:1.35}.rpt .neg{color:var(--bad)}
.meter{height:6px;border-radius:9px;background:var(--surface2);overflow:hidden;width:90px;margin-top:5px}.meter b{display:block;height:100%;background:var(--accent)}
.rptxt{width:100%;min-height:260px;font:12.5px/1.5 var(--fm);padding:12px;border-radius:10px;border:1px solid var(--line);background:var(--surface);color:var(--ink);white-space:pre}
@media(max-width:900px){.rpsum{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""

AFF = {"live": ("ok", "Live"), "this_week": ("acc", "This week"), "signed": ("warn", "Signed, quiet"), "pending": ("", "Pending")}


def _m(v):
    return ("-" if v < 0 else "") + f"${abs(v):,.0f}"


def report_page():
    rep = lot.build(save=True)
    s = lot.summary(rep)
    errs = "".join(f'<p class="note2" style="margin-bottom:12px">{e(x)}</p>' for x in rep["errors"])
    since = lot._day(rep["since"]) + (" (rebuilt from the board history; from tomorrow it compares saved daily snapshots)" if rep["rebuilt"] else "")
    # part 1: the lot
    bar = "".join(f'<span>{e(k)}<b>{v}</b></span>' for k, v in s["by_stage"].items() if v)
    mv = "".join(f'<li class="{m["kind"]}"><i>{"+" if m["kind"] in ("up", "new") else "&minus;"}</i><b>{e(m["item"]["name"])}</b>'
                 f'<span>{e(m["text"])}</span><small>{e(m["item"]["group"])}</small></li>' for m in rep["moves"])
    mv = mv or '<li><span class="mut">Nothing changed stage since then.</span></li>'
    rows = ""
    for it in sorted(rep["items"].values(), key=lambda i: (i["group"] != "Brand", i.get("priority", 99), i["name"].lower())):
        pct = round(100 * it["passed"] / it["checks"]) if it["checks"] else 0
        moved = next((m for m in rep["moves"] if m["item"]["name"] == it["name"] and m["item"]["group"] == it["group"]), None)
        days = f'<small>{it["days"]} days in this milestone</small>' if it.get("days") is not None else ""
        link = '/board' if it["group"] == "Brand" else f'/buyers#p-{e(it.get("id", ""))}'
        rows += (f'<tr><td><a href="{link}"><b>{e(it["name"])}</b></a><small>{e(it["group"])}{(" &middot; " + e(it["sub"])) if it.get("sub") else ""}</small></td>'
                 f'<td><b>{e(it["stage"])}</b>{days}</td>'
                 f'<td>{it["passed"]} of {it["checks"]} {"checks" if it["group"] == "Brand" else "steps"}<div class="meter"><b style="width:{pct}%"></b></div></td>'
                 f'<td>{e(it.get("next") or "Nothing left")}</td><td>{e(moved["text"]) if moved else "<span class=mut>No change</span>"}</td></tr>')
    # part 2: affiliates
    arows = ""
    for a in rep["aff"]:
        cls, lab = AFF[a["status"]]
        camps = "".join(f'<small>{e(c["name"])}{(" &middot; " + e(c["buyer"])) if c.get("buyer") else ""}</small>' for c in a["campaigns"][:4])
        arows += (f'<tr><td><b>{e(a["publisher"])}</b>{camps}</td><td><span class="chip2 {cls}">{lab}</span></td>'
                  f'<td class="num">{a["calls_y"]:,}<small>{a["calls_t"]:,} today</small></td><td class="num">{a["clicks_y"]:,}<small>{a["clicks_t"]:,} today</small></td>'
                  f'<td class="num">{a["calls30"]:,}</td><td class="num">{a["clicks30"]:,}</td><td class="num">{a["conv30"]:,}</td>'
                  f'<td class="num">{_m(a["rev30"])}</td><td class="num">{_m(a["payout30"])}</td><td class="num{" neg" if a["profit30"] < 0 else ""}">{_m(a["profit30"])}</td></tr>')
    arows = arows or '<tr><td colspan="10"><div class="empty">No publishers found. Check Everflow and Ringba on the Integrations page.</div></td></tr>'
    amv = f'<p class="pbnote">Changes since the last report: {e("; ".join(rep["aff_moves"]))}</p>' if rep["aff_moves"] else ""
    text = lot.as_text(rep)
    body = (f'<div class="pagehead"><div><h1>Daily report</h1><p>{e(lot._day(rep["day"]))}. Part 1 is the lot: every brand and partner we are preparing, its stage, and what moved since {e(since)}. '
            f'Part 2 is the affiliate campaigns: who is signed, who is live, calls, revenue and profit. Copy the text version at the bottom to post it.</p></div>'
            f'<div><button class="btn" id="rpcopy" type="button">{ico("copy")}Copy report</button></div></div>{errs}'
            f'<div class="rpsum"><div><b>{s["brands"]}</b><span>Brands on the lot, {s["by_stage"]["Live"]} live</span></div><div><b>{s["partners"]}</b><span>Partners in onboarding</span></div>'
            f'<div><b>{s["forward"]}</b><span>Moved forward or new since {e(lot._day(rep["since"]))}</span></div><div><b>{s["moves"] - s["forward"]}</b><span>Moved back or left</span></div></div>'
            f'<div class="rph"><h2>1. The lot</h2><span>Stage of prep for every item</span></div><div class="stagebar">{bar}</div>'
            f'<p class="bysec">Movement since {e(lot._day(rep["since"]))}</p><ul class="mv">{mv}</ul>'
            f'<section class="panel rpwrap" style="margin-top:14px"><table class="tbl rpt"><thead><tr><th>Item</th><th>Stage</th><th>Prep</th><th>Next step</th><th>Since last day</th></tr></thead><tbody>{rows}</tbody></table></section>'
            f'<div class="rph"><h2>2. Affiliate campaigns</h2><span>Everflow clicks and Ringba calls, updated {e(rep["refreshed"][5:16])}</span></div>'
            f'<div class="rpsum"><div><b>{s["signed"]}</b><span>Signed publishers</span></div><div><b>{s["live"]}</b><span>Live today or yesterday</span></div>'
            f'<div><b>{s["calls30"]:,}</b><span>Calls, last 30 days ({s["calls_y"]:,} yesterday)</span></div>'
            f'<div><b class="{"neg" if s["profit30"] < 0 else "pos"}">{_m(s["profit30"])}</b><span>Profit 30d: {_m(s["rev30"])} revenue less {_m(s["payout30"])} payout</span></div></div>'
            f'<section class="panel rpwrap"><table class="tbl rpt"><thead><tr><th>Publisher and campaigns</th><th>Status</th><th class="num">Calls<br>yesterday</th><th class="num">Clicks<br>yesterday</th>'
            f'<th class="num">Calls<br>30d</th><th class="num">Clicks<br>30d</th><th class="num">Converted<br>30d</th><th class="num">Revenue<br>30d</th><th class="num">Payout<br>30d</th><th class="num">Profit<br>30d</th></tr></thead>'
            f'<tbody>{arows}</tbody></table></section>{amv}'
            f'<p class="pbnote">Revenue is what buyers paid us (Everflow revenue, Ringba conversion amount). Payout is what we paid the publisher. Profit is revenue less payout. '
            f'Ringba cannot report calls by day beyond today and yesterday, so money is shown for 30 days.</p>'
            f'<div class="rph"><h2>Text version</h2><span>Paste into Basecamp or chat</span></div><textarea class="rptxt" id="rptxt" readonly>{e(text)}</textarea>')
    js = """<script>(function(){var b=document.getElementById('rpcopy');b.onclick=function(){var t=document.getElementById('rptxt');t.select();
(navigator.clipboard?navigator.clipboard.writeText(t.value):Promise.reject()).then(function(){toast('Report copied',true);},function(){document.execCommand('copy');toast('Report copied',true);});};})();</script>"""
    return shell("Daily report", body, "report", "<b>Daily report</b>", js)
