"""Publisher go-live board: on the dashboard (top) and as its own page (/golive)."""
import golive
import ui
from ui import e, ico, shell

ui.CSS = ui.CSS + """
.glw{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:20px}
.glw h2{margin:0;font:600 18px var(--fd)}.glw .glh{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:12px}.glw .glh span{color:var(--mut);font-size:12.5px}
.glw .glh a{margin-left:auto;font-size:12.5px}
.gltbl{width:100%;border-collapse:collapse}.gltbl th{font:600 11px var(--fb);letter-spacing:.05em;text-transform:uppercase;color:var(--mut);text-align:left;padding:0 6px 8px}
.gltbl td{padding:10px 6px;border-top:1px solid var(--line);vertical-align:top;font-size:13px}.gltbl td small{display:block;color:var(--mut);font-size:11.5px;line-height:1.35}
.glst{display:flex;gap:4px}.glst i{width:26px;height:26px;border-radius:50%;display:grid;place-items:center;font:700 11px var(--fb);font-style:normal;background:var(--surface2);color:var(--faint)}
.glst i.ok{background:color-mix(in srgb,var(--ok) 18%,transparent);color:var(--ok)}.glst i.stop{background:color-mix(in srgb,var(--bad) 16%,transparent);color:var(--bad);outline:2px solid color-mix(in srgb,var(--bad) 40%,transparent)}
.glact b{display:block;color:var(--bad);font-size:12px;margin-bottom:2px}.glact.done b{color:var(--ok)}
.glsum{display:flex;gap:16px;flex-wrap:wrap;margin:0 0 12px;font-size:13px;color:var(--mut)}.glsum b{color:var(--ink);font:600 20px var(--fd);margin-right:4px}
.glwrap{overflow-x:auto}
"""


def section(full=False):
    b = golive.board()
    rows = b.get("rows", [])
    names = dict(golive.STEPS)
    live = sum(1 for r in rows if r["blocker"] is None)
    pubs = len({r["publisher"] for r in rows})
    trs = ""
    for r in rows:
        dots = "".join(f'<i class="{"ok" if r["checks"][k]["ok"] else ("stop" if k == r["blocker"] else "")}" title="{e(lab)}: {e(r["checks"][k]["detail"])}">{n + 1}</i>'
                       for n, (k, lab) in enumerate(golive.STEPS))
        why = r["checks"][r["blocker"]]["detail"] if r["blocker"] else ""
        trs += (f'<tr><td><b>{e(r["publisher"])}</b><small>{r["clicks90"]:,} clicks 90d &middot; {r["conv30"]} paid calls 30d</small></td>'
                f'<td>{e(r["brand"])}<small>Offer {e(r["offer_id"])}: {e(r["offer"])}</small><small>Lands on {e(r["landing"])}</small></td>'
                f'<td><div class="glst">{dots}</div><small style="margin-top:5px">{r["done"]} of {len(golive.STEPS)} steps</small></td>'
                f'<td class="glact{" done" if not r["blocker"] else ""}"><b>{e(names[r["blocker"]] if r["blocker"] else "Live")}{": " + e(why) if full and why else ""}</b>{e(r["action"])}</td></tr>')
    if not trs:
        trs = '<tr><td colspan="4"><div class="empty">No signed publishers on our offers yet, or Everflow is not connected.</div></td></tr>'
    errs = "".join(f'<p class="note2">{e(x)}</p>' for x in b.get("errors", []))
    legend = " &middot; ".join(f"{n + 1} {lab}" for n, (_, lab) in enumerate(golive.STEPS))
    link = '' if full else f'<a href="/golive">Details and the test-call runbook{ico("arrow")}</a>'
    return (f'<section class="glw"><div class="glh"><h2>Signed publishers: road to live</h2><span>Traffic in, a call out, we get paid, they get paid. '
            f'Checked live from Everflow, Ringba and the landing pages, {e(b.get("made", "")[5:16])}.</span>{link}</div>{errs}'
            f'<div class="glsum"><span><b>{pubs}</b>signed publishers</span><span><b>{len(rows)}</b>publisher offers</span><span><b>{live}</b>live</span>'
            f'<span><b>{len(rows) - live}</b>blocked</span></div>'
            f'<div class="glwrap"><table class="gltbl"><thead><tr><th>Publisher</th><th>Offer</th><th>Steps</th><th>Blocker and next action</th></tr></thead><tbody>{trs}</tbody></table></div>'
            f'<p class="pbnote" style="margin-top:8px">Steps: {legend}. Red marks the step that blocks the publisher; hover a dot for the detail.</p></section>')


RUNBOOK = """<section class="panel" style="padding:18px 20px"><h2 style="margin:0 0 10px;font:600 18px var(--fd)">Test-call runbook: one publisher, start to finish</h2>
<p class="mut" style="margin:0 0 10px">Do this on one call with the team, pretending to be the publisher. When every step passes, the publisher is clear to send traffic.</p>
<ol style="margin:0;padding-left:20px;line-height:1.7;font-size:13.5px">
<li><b>Paperwork.</b> Publisher agreement signed, W-9 in, payout agreed. Track it in Partner onboarding.</li>
<li><b>Everflow.</b> Publisher account active, offer visible to them. Copy their tracking link from Everflow (Offers, the offer, Tracking link, pick the publisher).</li>
<li><b>Landing page.</b> The offer's destination must be a page with the brand's Ringba tag (the lp. pages have it), and the link must carry <code>everflow_transaction_id={transaction_id}</code> and <code>everflow_source_id={affiliate_id}</code>.</li>
<li><b>Click.</b> Open the tracking link in a private window. The page should show a pool number (not the main number). Everflow shows the click within a minute.</li>
<li><b>Call.</b> Call the number on the page from a phone, and stay on past the buyer's minimum duration. Ringba shows the call with the everflow_transaction_id tag.</li>
<li><b>Paid.</b> Ringba marks the call converted and fires the Everflow pixel. Everflow shows a conversion for the publisher. This board moves to step 6.</li>
<li><b>Go.</b> Tell the publisher they are live. Ravi checks traffic and rejects daily (item 3).</li>
</ol></section>"""


def golive_page():
    body = (f'<div class="pagehead"><div><h1>Publisher go-live</h1><p>Every signed publisher on one of our offers, checked step by step from signed to live, '
            f'with the one thing blocking each.</p></div><div><button class="btn" id="glr" type="button">{ico("clock")}Check again</button></div></div>'
            f'{section(full=True)}{RUNBOOK}')
    js = """<script>(function(){var r=document.getElementById('glr');r.onclick=function(){r.disabled=true;fetch('/api/golive/refresh',{method:'POST',body:'{}'}).then(function(x){return x.json();}).then(function(j){if(j.ok){location.reload();}else{toast(j.error||'Check failed',false);r.disabled=false;}}).catch(function(){toast('Check failed',false);r.disabled=false;});};})();</script>"""
    return shell("Publisher go-live", body, "golive", "<b>Publisher go-live</b>", js)
