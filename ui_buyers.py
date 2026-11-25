"""Buyer onboarding screens: the team's tracker (/buyers) and the private page each buyer opens (/onboard/<id>)."""
import json

import buyers
import core
import ui
from ui import e, ico, shell

ui.CSS = ui.CSS + """
.byform{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.byform label{display:grid;gap:5px;font:500 12px var(--fb);color:var(--mut)}
.byform label.w2{grid-column:span 2}.byform label.w4{grid-column:1/-1}
.byform input,.byform select,.byform textarea{height:36px;padding:0 10px;font-size:13.5px}.byform textarea{height:64px;padding:8px 10px;resize:vertical}
.byact{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:14px}
.bylist{display:grid;gap:12px}
.bycard{background:var(--surface);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.bycard>summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:14px;align-items:center;padding:16px 18px}
.bycard>summary::-webkit-details-marker{display:none}
.bycard[open]>summary{border-bottom:1px solid var(--line)}
.byname{font:600 15px var(--fb);letter-spacing:-.01em}.bymeta{font-size:12.5px;color:var(--mut);margin-top:3px}
.byright{display:flex;align-items:center;gap:12px;flex-wrap:wrap;justify-content:flex-end}
.bybar{width:120px;height:6px;border-radius:99px;background:var(--surface2);overflow:hidden}.bybar i{display:block;height:100%;background:var(--accent);border-radius:99px}
.bybody{padding:18px;display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:22px}
.bysec{font:600 11px var(--fb);letter-spacing:.09em;text-transform:uppercase;color:var(--mut);margin:0 0 10px}
.steps2{display:grid;gap:6px}
.st2{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:center;padding:9px 11px;border-radius:10px;border:1px solid var(--line);background:var(--surface)}
.st2.done{background:color-mix(in srgb,var(--ok) 7%,var(--surface));border-color:color-mix(in srgb,var(--ok) 30%,var(--line))}
.st2.sent{background:color-mix(in srgb,var(--warn) 7%,var(--surface));border-color:color-mix(in srgb,var(--warn) 30%,var(--line))}
.st2 b{font-weight:600;font-size:13px}.st2 small{display:block;color:var(--mut);font-size:11.5px;margin-top:2px;line-height:1.4}
.seg{display:inline-flex;border:1px solid var(--line2);border-radius:8px;overflow:hidden}.seg button{border:0;background:var(--surface);height:28px;padding:0 9px;font:500 11.5px var(--fb);color:var(--mut);cursor:pointer}
.seg button+button{border-left:1px solid var(--line2)}.seg button.on{background:var(--accent)!important;color:#fff!important}
.st2.done .seg button.on{background:var(--ok)!important}.st2.sent .seg button.on{background:var(--warn)!important}
.seg button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.olink{display:flex;gap:8px;align-items:center;margin:0 0 14px}.olink input{flex:1;height:34px;font:500 12px var(--fm)}
.tech{border:1px dashed var(--line2);border-radius:10px;padding:10px 12px;font-size:12.5px;line-height:1.55;margin-top:12px}.tech dt{color:var(--mut);font-size:11.5px}.tech dd{margin:0 0 6px}
.readyb{padding:10px 12px;border-radius:10px;background:color-mix(in srgb,var(--ok) 10%,transparent);color:var(--ok);font:600 12.5px var(--fb);margin-bottom:12px}
@media(max-width:1100px){.bybody{grid-template-columns:1fr}.byform{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.byform{grid-template-columns:1fr}.byform label.w2{grid-column:auto}.bycard>summary{grid-template-columns:1fr}.byright{justify-content:flex-start}}
"""


def _opts(pairs, cur):
    return "".join(f'<option value="{e(v)}"{" selected" if v == cur else ""}>{e(t)}</option>' for v, t in pairs)


def _form(b, brands, prefix):
    b = b or {}
    brand_opts = [("", "No brand yet")] + [(x["slug"], x["name"]) for x in brands]
    f = lambda k: e(b.get(k, "") or "")
    return (f'<div class="byform" data-form="{prefix}">'
            f'<label class="w2">Company<input name="company" value="{f("company")}" maxlength="160" placeholder="Click Thesis" required></label>'
            f'<label>Vertical<input name="vertical" value="{f("vertical")}" maxlength="160" placeholder="Home Services - Pest Control"></label>'
            f'<label>IO number<input name="io_number" value="{f("io_number")}" maxlength="40" placeholder="242"></label>'
            f'<label>Contact name<input name="contact_name" value="{f("contact_name")}" maxlength="160"></label>'
            f'<label>Contact email<input name="contact_email" type="email" value="{f("contact_email")}" maxlength="160"></label>'
            f'<label>Buys<select name="product">{_opts(list(buyers.PRODUCTS.items()), b.get("product", "calls"))}</select></label>'
            f'<label>Brand<select name="brand">{_opts(brand_opts, b.get("brand", ""))}</select></label>'
            f'<label>Payout<input name="payout" value="{f("payout")}" maxlength="80" placeholder="$45 per call over 120s"></label>'
            f'<label>First-lead deposit<input name="deposit_amount" value="{f("deposit_amount")}" maxlength="40" placeholder="$500"></label>'
            f'<label class="w2">MSA link (blank uses the default)<input name="msa_url" value="{f("msa_url")}" placeholder="https://"></label>'
            f'<label class="w2">IO e-sign link (blank uses the default)<input name="io_url" value="{f("io_url")}" placeholder="https://"></label>'
            f'<label class="w2">Deposit payment link (blank uses the default)<input name="deposit_url" value="{f("deposit_url")}" placeholder="https://"></label>'
            f'<label class="w4">Notes<textarea name="notes" maxlength="2000">{f("notes")}</textarea></label></div>')


def _steps(b):
    st = b.get("steps", {})
    rows = ""
    for k, lab, desc in buyers.STEPS:
        s = st.get(k, {})
        state = s.get("state", "todo")
        who = f' &middot; {e(s.get("by", ""))}, {e(buyers.stamp(s.get("ts", "")))}' if s.get("ts") else ""
        note = f' &middot; {e(s["note"])}' if s.get("note") else ""
        seg = "".join(f'<button type="button" data-step="{k}" data-state="{v}" class="{"on" if v == state else ""}" aria-pressed="{"true" if v == state else "false"}">{lab2}</button>'
                      for v, lab2 in (("todo", "To do"), ("sent", "Sent"), ("done", "Done")))
        rows += f'<div class="st2 {state if state != "todo" else ""}"><div><b>{e(lab)}</b><small>{e(desc)}{who}{note}</small></div><div class="seg" role="group" aria-label="{e(lab)}">{seg}</div></div>'
    return rows


def _tech(b):
    t = b.get("tech") or {}
    if not t:
        return '<p class="tech mut">The buyer has not sent technical details yet. They send them from their onboarding link.</p>'
    labels = dict(buyers.TECH.get(b.get("product", "calls"), []))
    items = "".join(f'<dt>{e(labels.get(k, k))}</dt><dd>{e(v)}</dd>' for k, v in t.items() if k != "submitted")
    return f'<dl class="tech"><dt>Sent by the buyer on {e(buyers.stamp(t.get("submitted", "")))}</dt><dd></dd>{items}</dl>'


def buyers_page(host=""):
    brands = core.load_brands()
    names = {x["slug"]: x["name"] for x in brands}
    rows = buyers.all_buyers()
    s = buyers.settings()
    cards = ""
    for b in rows:
        p = buyers.progress(b)
        pct = round(100 * p["done"] / p["total"])
        meta = " &middot; ".join(x for x in (e(buyers.PRODUCTS.get(b.get("product"), "")), e(names.get(b.get("brand"), "")), e(b.get("payout", ""))) if x)
        ready = '<span class="chip2 ok">Ready for Ops</span>' if p["ready"] else f'<span class="mut" style="font-size:12px">Next: {e(p["next"])}</span>'
        link = f"{host}/onboard/{b['id']}"
        test_btn = ('<button class="btn" type="button" data-test>' + ico("phone") + 'Check test call</button>') if b.get("product") == "calls" and b.get("brand") else ""
        cards += (f'<details class="bycard" data-id="{e(b["id"])}"><summary><div><div class="byname">{e(buyers.deal_name(b))}</div><div class="bymeta">{meta or "&nbsp;"}</div></div>'
                  f'<div class="byright">{ready}<span class="bybar" title="{p["done"]} of {p["total"]} steps"><i style="width:{pct}%"></i></span><span class="mut" style="font:500 12px var(--fm)">{p["done"]}/{p["total"]}</span></div></summary>'
                  f'<div class="bybody"><div><p class="bysec">Onboarding steps</p>{"<div class=readyb>Paperwork, deposit, tech details and test are done. Hand off to Ops.</div>" if p["ready"] else ""}'
                  f'<div class="steps2">{_steps(b)}</div><div class="byact">{test_btn}</div></div>'
                  f'<div><p class="bysec">Buyer\'s onboarding link</p><div class="olink"><input readonly value="{e(link)}" aria-label="Onboarding link"><button class="btn" type="button" data-copy>{ico("copy")}Copy</button>'
                  f'<a class="btn" href="/onboard/{e(b["id"])}" target="_blank" rel="noopener">{ico("ext")}Open</a></div>'
                  f'<p class="bysec">Details</p>{_form(b, brands, b["id"])}<div class="byact"><button class="btn primary" type="button" data-save>Save details</button>'
                  f'<button class="btn" type="button" data-archive>Archive</button></div><p class="bysec" style="margin-top:18px">Technical details</p>{_tech(b)}</div></div></details>')
    if not cards:
        cards = '<div class="empty">No buyers yet. Add the first one above; each gets its own onboarding link to send.</div>'
    body = (f'<div class="pagehead"><div><h1>Buyer onboarding</h1><p>Blue Wing\'s onboarding SOP as a checklist per buyer: MSA, campaign details, creatives, IO, first-lead deposit, '
            f'tech details and the first test, then the handoff to Ops. Each buyer gets a private link where they sign, add a card for the deposit, read the API specs and send their details. '
            f'Deals are named Business - Vertical IO #number, as the SOP asks.</p></div></div>'
            f'<details class="panel" style="margin-bottom:16px"{"" if rows else " open"}><summary style="cursor:pointer;font-weight:600">Add a buyer</summary><div style="margin-top:14px">{_form(None, brands, "new")}'
            f'<div class="byact"><button class="btn primary" type="button" id="addbuyer">Add buyer</button></div></div></details>'
            f'<details class="panel" style="margin-bottom:16px"><summary style="cursor:pointer;font-weight:600">Default links for every buyer</summary><div style="margin-top:14px">'
            f'<div class="byform" data-form="settings">'
            f'<label class="w2">MSA (document or e-sign link)<input name="msa_url" value="{e(s["msa_url"])}" placeholder="https://"></label>'
            f'<label class="w2">IO e-sign link<input name="io_url" value="{e(s["io_url"])}" placeholder="https://"></label>'
            f'<label class="w2">Deposit payment link (Stripe Payment Link or similar)<input name="deposit_url" value="{e(s["deposit_url"])}" placeholder="https://"></label>'
            f'<label class="w2">Support email shown to buyers<input name="support_email" value="{e(s["support_email"])}" placeholder="partners@..."></label></div>'
            f'<p class="note2" style="margin-top:12px">Card details never reach the studio: the deposit step sends the buyer to your payment provider\'s hosted page.</p>'
            f'<div class="byact"><button class="btn primary" type="button" id="savesettings">Save default links</button></div></div></details>'
            f'<div class="bylist">{cards}</div>')
    js = """<script>(function(){
function data(box){var o={};box.querySelectorAll('input,select,textarea').forEach(function(i){o[i.name]=i.value;});return o;}
function post(url,body,ok){return fetch(url,{method:'POST',body:JSON.stringify(body)}).then(function(r){return r.json().then(function(j){if(!r.ok||j.ok===false){throw new Error(j.error||'Something went wrong');}return j;});}).then(ok).catch(function(e){toast(e.message,false);});}
var add=document.getElementById('addbuyer');if(add){add.onclick=function(){post('/api/buyers/save',data(document.querySelector('[data-form=new]')),function(){location.reload();});};}
var ss=document.getElementById('savesettings');if(ss){ss.onclick=function(){post('/api/buyers/settings',data(document.querySelector('[data-form=settings]')),function(){toast('Default links saved',true);});};}
document.querySelectorAll('.bycard').forEach(function(c){var id=c.getAttribute('data-id');
 c.querySelectorAll('.seg button').forEach(function(b){b.onclick=function(){post('/api/buyers/step',{id:id,key:b.getAttribute('data-step'),state:b.getAttribute('data-state')},function(){sessionStorage.setItem('byopen',id);location.reload();});};});
 var sv=c.querySelector('[data-save]');if(sv){sv.onclick=function(){var d=data(c.querySelector('.byform'));d.id=id;post('/api/buyers/save',d,function(){sessionStorage.setItem('byopen',id);location.reload();});};}
 var ar=c.querySelector('[data-archive]');if(ar){ar.onclick=function(){post('/api/buyers/save',{id:id,archived:true},function(){location.reload();});};}
 var cp=c.querySelector('[data-copy]');if(cp){cp.onclick=function(){var i=c.querySelector('.olink input');i.select();try{navigator.clipboard.writeText(i.value);}catch(e){document.execCommand('copy');}toast('Onboarding link copied',true);};}
 var tb=c.querySelector('[data-test]');if(tb){tb.onclick=function(){tb.disabled=true;post('/api/buyers/test',{id:id},function(j){toast(j.detail||'Checked',j.ok);if(j.ok){sessionStorage.setItem('byopen',id);location.reload();}}).then(function(){tb.disabled=false;});};}
});
try{var o=sessionStorage.getItem('byopen');if(o){sessionStorage.removeItem('byopen');var el=document.querySelector('.bycard[data-id="'+o+'"]');if(el){el.open=true;el.scrollIntoView({block:'start'});}}}catch(e){}
})();</script>"""
    return shell("Buyer onboarding", body, "buyers", "<b>Buyer onboarding</b>", js)


# ------------------------------------------------------------------ the buyer's own page

PUB_CSS = """:root{--ink:#14171c;--mut:#5d6470;--line:rgba(20,23,28,.12);--bg:#f6f5f1;--card:#fff;--acc:#1d3866;--ok:#1d7a4e;--warn:#9a6410}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:400 15.5px/1.6 Inter,system-ui,"Segoe UI",Arial,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:820px;margin:0 auto;padding:36px 20px 80px}h1{font:600 30px/1.15 Inter,system-ui,sans-serif;letter-spacing:-.02em;margin:6px 0 8px}
.kick{font:600 11.5px/1 Inter,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--acc)}.lead{color:var(--mut);margin:0 0 26px}
.deal{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:0 0 26px}.deal div{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.deal b{display:block;font-size:11.5px;color:var(--mut);font-weight:500;margin-bottom:2px}.deal span{font-weight:600}
.step{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin:0 0 12px;display:grid;grid-template-columns:36px minmax(0,1fr);gap:14px}
.step>div{min-width:0}pre{max-width:100%}.step .n{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;background:#eef1f6;color:var(--acc);font-weight:700}
.step.done .n{background:var(--ok);color:#fff}.step h2{font:600 17px/1.3 Inter,sans-serif;margin:5px 0 4px}.step p{margin:0 0 10px;color:var(--mut)}
.badge{display:inline-block;font:600 11.5px/1 Inter,sans-serif;padding:5px 9px;border-radius:99px;margin-left:8px;vertical-align:middle}.badge.ok{background:#e3f2ea;color:var(--ok)}.badge.wait{background:#f8eedc;color:var(--warn)}
.btn{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 18px;border-radius:10px;background:var(--acc);color:#fff;text-decoration:none;font-weight:600;border:0;cursor:pointer;font-size:15px}
.btn:focus-visible,input:focus-visible,textarea:focus-visible{outline:3px solid #8fb0e8;outline-offset:2px}.btn.off{background:#e9ebef;color:var(--mut);cursor:default}
.spec{background:#fbfbfa;border:1px solid var(--line);border-radius:10px;padding:14px 16px;font-size:14px}.spec h3{font-size:14px;margin:12px 0 6px}.spec h3:first-child{margin-top:0}
.spec ul{margin:0;padding-left:20px}.spec code,pre{font:500 12.5px/1.55 ui-monospace,Menlo,Consolas,monospace}pre{background:#14171c;color:#e8eaee;border-radius:10px;padding:14px;overflow-x:auto;white-space:pre}
form{display:grid;gap:10px;margin-top:6px}label{display:grid;gap:4px;font-size:13px;font-weight:500;color:var(--mut)}
input,textarea{font:inherit;font-size:15px;padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:#fff;color:var(--ink);width:100%}textarea{min-height:70px;resize:vertical}
.msg{font-weight:600;margin-top:4px}.foot{color:var(--mut);font-size:13px;margin-top:30px}
@media(max-width:520px){h1{font-size:25px}.step{grid-template-columns:minmax(0,1fr)}.step .n{width:30px;height:30px}}"""


def _spec(product):
    if product == "leads":
        sample = {"first_name": "Jane", "last_name": "Doe", "phone": "+15555550123", "email": "jane@example.com", "zip": "33062", "state": "FL",
                  "ip_address": "203.0.113.7", "landing_page_url": "https://example-brand.com/", "trustedform_cert_url": "https://cert.trustedform.com/...",
                  "jornaya_leadid": "...", "consent_text": "By submitting, I agree to be contacted...", "consent_timestamp": "2026-11-25T14:03:11Z",
                  "sub_id": "publisher-123", "click_id": "abc123"}
        return ('<div class="spec"><h3>How leads reach you</h3><ul><li>We post each lead to your endpoint in real time as JSON over HTTPS, through our lead distribution platform.</li>'
                '<li>Every lead carries a TrustedForm certificate and the consumer\'s last name, the two fields buyers most often reject pings over.</li>'
                '<li>Answer within 10 seconds with HTTP 200 and a JSON body saying accepted or rejected, with a reason when rejected.</li></ul>'
                f'<h3>Sample lead</h3><pre>{e(json.dumps(sample, indent=2))}</pre>'
                '<h3>Sample response</h3><pre>{"status": "accepted", "lead_id": "YOUR-ID"}\n{"status": "rejected", "reason": "duplicate"}</pre></div>')
    if product == "clicks":
        return ('<div class="spec"><h3>How clicks reach you</h3><ul><li>We send click traffic to your tracking link, with our click ID in the parameter you name.</li>'
                '<li>Conversions come back to us by server-to-server postback carrying that click ID and the payout. We send you our postback URL during setup.</li>'
                '<li>Tell us your caps and accepted geos so we can throttle traffic before you reach them.</li></ul></div>')
    return ('<div class="spec"><h3>How calls reach you</h3><ul><li>Callers dial a tracked number on our page; we forward the live call to the number you give us, with the caller\'s ID passed through.</li>'
            '<li>Every call is logged with its source, so you only pay for calls that meet the billable length we agree.</li>'
            '<li>We respect your hours, concurrency limit and daily cap, and route calls elsewhere when you are closed or full.</li></ul>'
            '<h3>What we need from you</h3><ul><li>The destination number (or SIP address).</li><li>Hours and time zone, most calls at once, daily cap.</li>'
            '<li>Billable call length, accepted states, and who to contact about routing problems.</li></ul></div>')


def onboard_page(bid):
    b = buyers.get(bid)
    if not b or b.get("archived"):
        return None
    st = b.get("steps", {})
    lk = buyers.links(b)
    s = buyers.settings()
    done = lambda k: st.get(k, {}).get("state") == "done"
    badge = lambda k: ('<span class="badge ok">Done</span>' if done(k) else '<span class="badge wait">Waiting on you</span>' if st.get(k, {}).get("state") == "sent" else "")
    def btn(url, text):
        return f'<a class="btn" href="{e(url)}" target="_blank" rel="noopener">{e(text)}</a>' if url else '<span class="btn off">We will email you this link</span>'
    product = b.get("product", "calls")
    fields = "".join(f'<label>{e(lab)}<input name="{k}" value="{e((b.get("tech") or {}).get(k, ""))}" maxlength="500"></label>' for k, lab in buyers.TECH.get(product, []))
    dep = e(b.get("deposit_amount") or "")
    deal = "".join(f'<div><b>{lab}</b><span>{e(v)}</span></div>' for lab, v in (("Campaign", buyers.deal_name(b)), ("You buy", buyers.PRODUCTS.get(product, "")),
                                                                                    ("Payout", b.get("payout", "")), ("First-lead deposit", b.get("deposit_amount", ""))) if v)
    support = f' Questions? Email <a href="mailto:{e(s["support_email"])}">{e(s["support_email"])}</a>.' if s.get("support_email") else ""
    body = (f'<div class="wrap"><span class="kick">Partner onboarding</span><h1>Welcome{", " + e(b.get("contact_name").split()[0]) if b.get("contact_name") else ""}</h1>'
            f'<p class="lead">Five steps to get your campaign live with Blue Wing Ads. This page is private to you; your progress updates as we go.</p><div class="deal">{deal}</div>'
            f'<section class="step{" done" if done("msa") else ""}"><span class="n">1</span><div><h2>Sign the master service agreement {badge("msa")}</h2><p>Our standard terms for working together. Send redlines back by email if you need changes.</p>{btn(lk["msa_url"], "Review and sign the MSA")}</div></section>'
            f'<section class="step{" done" if done("io") else ""}"><span class="n">2</span><div><h2>Sign the insertion order {badge("io")}</h2><p>The specifics of this campaign: payout, caps, hours and geos. Sign it online in a couple of minutes.</p>{btn(lk["io_url"], "Sign the IO")}</div></section>'
            f'<section class="step{" done" if done("deposit") else ""}"><span class="n">3</span><div><h2>Add a card for the first-lead deposit {badge("deposit")}</h2><p>{("A deposit of " + dep + " covers your first leads. ") if dep else ""}You enter your card on our payment provider\'s secure page; we never see or store your card number.</p>{btn(lk["deposit_url"], "Add a card securely")}</div></section>'
            f'<section class="step{" done" if done("tech") else ""}"><span class="n">4</span><div><h2>Technical setup {badge("tech")}</h2><p>How we will send you {e(buyers.PRODUCTS.get(product, "").lower())}, and the details we need from you.</p>{_spec(product)}'
            f'<form id="techf">{fields}<button class="btn" type="submit">Send my details</button><p class="msg" id="techmsg" role="status" aria-live="polite"></p></form></div></section>'
            f'<section class="step{" done" if done("test") else ""}"><span class="n">5</span><div><h2>First test {badge("test")}</h2><p>Once the steps above are done we send a test {"call" if product == "calls" else "lead" if product == "leads" else "click"} and confirm with you that it arrived. Then your campaign goes live.</p></div></section>'
            f'<p class="foot">Blue Wing Ads partner onboarding.{support}</p></div>')
    js = ("<script>(function(){var f=document.getElementById('techf'),m=document.getElementById('techmsg');if(!f){return;}f.onsubmit=function(ev){ev.preventDefault();var o={};"
          "f.querySelectorAll('input').forEach(function(i){o[i.name]=i.value;});m.textContent='Sending...';fetch(location.pathname+'/tech',{method:'POST',body:JSON.stringify(o)})"
          ".then(function(r){return r.json();}).then(function(j){m.textContent=j.ok?'Thanks, we have your details. We will confirm the test with you.':(j.error||'Something went wrong. Please try again.');})"
          ".catch(function(){m.textContent='Something went wrong. Please try again.';});};})();</script>")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="robots" content="noindex,nofollow"><title>Partner onboarding | {e(buyers.deal_name(b))}</title><style>{PUB_CSS}</style></head><body>{body}{js}</body></html>')
