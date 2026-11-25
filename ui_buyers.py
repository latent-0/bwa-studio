"""Partner onboarding, team side (/buyers): one card per buyer or publisher with the six-stage roadmap, the step checklist, the private onboarding
link and the branded welcome email. The partner's own page lives in partner_page.py."""
import buyers
import core
import partner_page
import ui
from ui import e, ico, shell

ui.CSS = ui.CSS + """
.byform{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.byform label{display:grid;gap:5px;font:500 12px var(--fb);color:var(--mut)}
.byform label.w2{grid-column:span 2}.byform label.w4{grid-column:1/-1}.byform .hd{grid-column:1/-1;font:600 11px var(--fb);letter-spacing:.09em;text-transform:uppercase;color:var(--faint);margin-top:6px}
.byform input,.byform select,.byform textarea{height:36px;padding:0 10px;font-size:13.5px}.byform textarea{height:64px;padding:8px 10px;resize:vertical}
.byform .pubonly,.byform .buyonly{display:contents}.byform[data-kind=buyer] .pubonly,.byform[data-kind=publisher] .buyonly{display:none}
.byact{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:14px}
.bylist{display:grid;gap:12px}
.bycard{background:var(--surface);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.bycard>summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:14px;align-items:center;padding:16px 18px}
.bycard>summary::-webkit-details-marker{display:none}.bycard[open]>summary{border-bottom:1px solid var(--line)}
.byname{font:600 15px var(--fb);letter-spacing:-.01em}.bymeta{font-size:12.5px;color:var(--mut);margin-top:3px}
.byright{display:flex;align-items:center;gap:12px;flex-wrap:wrap;justify-content:flex-end}
.road6{display:flex;gap:4px;align-items:center}.road6 i{width:18px;height:8px;border-radius:99px;background:var(--surface2)}.road6 i.done{background:var(--ok)}.road6 i.current{background:#ffb21e}
.bybody{padding:18px;display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:22px}
.bysec{font:600 11px var(--fb);letter-spacing:.09em;text-transform:uppercase;color:var(--mut);margin:0 0 10px}
.stg{margin:0 0 12px}.stg h4{display:flex;align-items:center;gap:8px;margin:0 0 6px;font:600 12.5px var(--fb)}.stg h4 span{font:600 10.5px var(--fb);padding:3px 7px;border-radius:99px;background:var(--surface2);color:var(--mut)}
.stg h4 span.done{background:color-mix(in srgb,var(--ok) 14%,transparent);color:var(--ok)}.stg h4 span.current{background:#fff1d6;color:#9a5d00}
.steps2{display:grid;gap:6px}
.st2{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:center;padding:9px 11px;border-radius:10px;border:1px solid var(--line);background:var(--surface)}
.st2.done{background:color-mix(in srgb,var(--ok) 7%,var(--surface));border-color:color-mix(in srgb,var(--ok) 30%,var(--line))}
.st2.sent{background:color-mix(in srgb,var(--warn) 7%,var(--surface));border-color:color-mix(in srgb,var(--warn) 30%,var(--line))}
.st2 b{font-weight:600;font-size:13px}.st2 small{display:block;color:var(--mut);font-size:11.5px;margin-top:2px;line-height:1.4}
.seg{display:inline-flex;border:1px solid var(--line2);border-radius:8px;overflow:hidden}.seg button{border:0;background:var(--surface);height:28px;padding:0 9px;font:500 11.5px var(--fb);color:var(--mut);cursor:pointer}
.seg button+button{border-left:1px solid var(--line2)}.seg button.on{background:var(--accent)!important;color:#fff!important}
.st2.done .seg button.on{background:var(--ok)!important}.st2.sent .seg button.on{background:var(--warn)!important}
.seg button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.olink{display:flex;gap:8px;align-items:center;margin:0 0 14px;flex-wrap:wrap}.olink input{flex:1 1 200px;height:34px;font:500 12px var(--fm)}
.tech{border:1px dashed var(--line2);border-radius:10px;padding:10px 12px;font-size:12.5px;line-height:1.55;margin-top:12px}.tech dt{color:var(--mut);font-size:11.5px}.tech dd{margin:0 0 6px}
.readyb{padding:10px 12px;border-radius:10px;background:color-mix(in srgb,var(--ok) 10%,transparent);color:var(--ok);font:600 12.5px var(--fb);margin-bottom:12px}
.emdlg{width:min(760px,94vw);max-height:92vh;border:0;border-radius:16px;padding:0;background:var(--surface);color:var(--ink);box-shadow:0 30px 80px rgba(0,0,0,.35)}
.emdlg::backdrop{background:rgba(10,16,30,.55)}.emhd{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:14px 16px;border-bottom:1px solid var(--line)}.emhd b{flex:1;font-size:14px;min-width:200px}
.emdlg iframe{display:block;width:100%;height:min(66vh,720px);border:0;background:#f5f7fb}.emft{display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:12px 16px;border-top:1px solid var(--line)}
.emft .mut{font-size:12px;flex:1;min-width:200px}
@media(max-width:1100px){.bybody{grid-template-columns:1fr}.byform{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.byform{grid-template-columns:1fr}.byform label.w2{grid-column:auto}.bycard>summary{grid-template-columns:1fr}.byright{justify-content:flex-start}}
"""


def _opts(pairs, cur):
    return "".join(f'<option value="{e(v)}"{" selected" if v == cur else ""}>{e(t)}</option>' for v, t in pairs)


def _form(b, brands, prefix):
    b = b or {}
    kind = buyers.kind_of(b) if b else "buyer"
    brand_opts = [("", "No brand yet")] + [(x["slug"], x["name"]) for x in brands]
    f = lambda k: e(b.get(k, "") or "")
    return (f'<div class="byform" data-form="{prefix}" data-kind="{kind}">'
            f'<label>Partner type<select name="kind" data-kindsel>{_opts(list(buyers.KINDS.items()), kind)}</select></label>'
            f'<label>Company<input name="company" value="{f("company")}" maxlength="160" placeholder="Shift44" required></label>'
            f'<label>Vertical<input name="vertical" value="{f("vertical")}" maxlength="160" placeholder="Final Expense"></label>'
            f'<label>IO number<input name="io_number" value="{f("io_number")}" maxlength="40" placeholder="242"></label>'
            f'<label>Contact name<input name="contact_name" value="{f("contact_name")}" maxlength="160"></label>'
            f'<label>Contact email<input name="contact_email" type="email" value="{f("contact_email")}" maxlength="160"></label>'
            f'<label>Brand<select name="brand">{_opts(brand_opts, b.get("brand", ""))}</select></label>'
            f'<label>Payout<input name="payout" value="{f("payout")}" maxlength="80" placeholder="$45 per call over 120s"></label>'
            f'<span class="buyonly"><label>Buys<select name="product">{_opts(list(buyers.PRODUCTS.items()), b.get("product", "calls"))}</select></label>'
            f'<label>First-lead deposit<input name="deposit_amount" value="{f("deposit_amount")}" maxlength="40" placeholder="$500"></label>'
            f'<span class="hd">Links for this buyer (blank uses the team default)</span>'
            f'<label class="w2">MSA<input name="msa_url" value="{f("msa_url")}" placeholder="https://"></label>'
            f'<label class="w2">IO e-sign<input name="io_url" value="{f("io_url")}" placeholder="https://"></label>'
            f'<label class="w2">Deposit payment page<input name="deposit_url" value="{f("deposit_url")}" placeholder="https://"></label></span>'
            f'<span class="pubonly"><span class="hd">Links for this publisher (blank uses the team default)</span>'
            f'<label class="w2">Their tracking link (Everflow)<input name="tracking_link" value="{f("tracking_link")}" placeholder="https://"></label>'
            f'<label class="w2">Publisher agreement<input name="agreement_url" value="{f("agreement_url")}" placeholder="https://"></label>'
            f'<label class="w2">W-9<input name="w9_url" value="{f("w9_url")}" placeholder="https://"></label>'
            f'<label class="w2">Payment setup<input name="payment_url" value="{f("payment_url")}" placeholder="https://"></label></span>'
            f'<label class="w4">Notes<textarea name="notes" maxlength="2000">{f("notes")}</textarea></label></div>')


def _steps(b):
    st = b.get("steps", {})
    labels = {k: (lab, desc) for k, lab, desc in buyers.steps_for(b)}
    out = ""
    for sg in buyers.stages(b):
        rows = ""
        for k in sg["steps"] + (("folder",) if sg["key"] == "live" else ()):
            lab, desc = labels[k]
            s = st.get(k, {})
            state = s.get("state", "todo")
            who = f' &middot; {e(s.get("by", ""))}, {e(buyers.stamp(s.get("ts", "")))}' if s.get("ts") else ""
            note = f' &middot; {e(s["note"])}' if s.get("note") else ""
            seg = "".join(f'<button type="button" data-step="{k}" data-state="{v}" class="{"on" if v == state else ""}" aria-pressed="{"true" if v == state else "false"}">{lab2}</button>'
                          for v, lab2 in (("todo", "To do"), ("sent", "Sent"), ("done", "Done")))
            rows += f'<div class="st2 {state if state != "todo" else ""}"><div><b>{e(lab)}</b><small>{e(desc)}{who}{note}</small></div><div class="seg" role="group" aria-label="{e(lab)}">{seg}</div></div>'
        tag = {"done": "Done", "current": "Current", "upcoming": "Upcoming"}[sg["state"]]
        out += f'<div class="stg"><h4>{e(sg["label"])}<span class="{sg["state"]}">{tag}</span></h4><div class="steps2">{rows}</div></div>'
    return out


def _tech(b):
    t = b.get("tech") or {}
    if not t:
        return '<p class="tech mut">No technical details yet. The partner sends them from their onboarding page.</p>'
    labels = dict(buyers.tech_fields(b))
    items = "".join(f'<dt>{e(labels.get(k, k))}</dt><dd>{e(v)}</dd>' for k, v in t.items() if k != "submitted")
    return f'<dl class="tech"><dt>Sent by the partner on {e(buyers.stamp(t.get("submitted", "")))}</dt><dd></dd>{items}</dl>'


def buyers_page(host=""):
    brands = core.load_brands()
    names = {x["slug"]: x["name"] for x in brands}
    rows = buyers.all_buyers()
    s = buyers.settings()
    cards = ""
    for b in rows:
        p = buyers.progress(b)
        sg = buyers.stages(b)
        dots = "".join(f'<i class="{x["state"]}" title="{e(x["label"])}"></i>' for x in sg)
        meta = " &middot; ".join(x for x in (e(buyers.KINDS[buyers.kind_of(b)]), e(buyers.PRODUCTS.get(b.get("product"), "")) if buyers.kind_of(b) == "buyer" else "",
                                             e(names.get(b.get("brand"), "")), e(b.get("payout", ""))) if x)
        ready = '<span class="chip2 ok">Ready for Ops</span>' if p["ready"] else f'<span class="mut" style="font-size:12px">Stage {p["stage"]}: {e(p["stage_label"])}</span>'
        link = f"{host}/onboard/{b['id']}"
        test_btn = ('<button class="btn" type="button" data-test>' + ico("phone") + 'Check test call</button>') if buyers.kind_of(b) == "buyer" and b.get("product") == "calls" and b.get("brand") else ""
        cards += (f'<details class="bycard" data-id="{e(b["id"])}"><summary><div><div class="byname">{e(buyers.deal_name(b))}</div><div class="bymeta">{meta or "&nbsp;"}</div></div>'
                  f'<div class="byright">{ready}<span class="road6" aria-label="{p["stages_done"]} of 6 stages done">{dots}</span><span class="mut" style="font:500 12px var(--fm)">{p["stages_done"]}/6</span></div></summary>'
                  f'<div class="bybody"><div><p class="bysec">Roadmap and steps</p>{"<div class=readyb>Paperwork, tech details and test are done. Hand off to Ops.</div>" if p["ready"] else ""}'
                  f'{_steps(b)}<div class="byact">{test_btn}</div></div>'
                  f'<div><p class="bysec">Partner\'s onboarding page</p><div class="olink"><input readonly value="{e(link)}" aria-label="Onboarding link"><button class="btn" type="button" data-copy>{ico("copy")}Copy</button>'
                  f'<a class="btn" href="/onboard/{e(b["id"])}" target="_blank" rel="noopener">{ico("ext")}Open</a></div>'
                  f'<div class="byact" style="margin:0 0 16px"><button class="btn primary" type="button" data-email>{ico("spark")}Welcome email</button></div>'
                  f'<p class="bysec">Details</p>{_form(b, brands, b["id"])}<div class="byact"><button class="btn primary" type="button" data-save>Save details</button>'
                  f'<button class="btn" type="button" data-archive>Archive</button></div><p class="bysec" style="margin-top:18px">Technical details</p>{_tech(b)}</div></div></details>')
    if not cards:
        cards = '<div class="empty">No partners yet. Add the first buyer or publisher above; each gets a private onboarding page and a branded welcome email.</div>'
    team_missing = not (s.get("success_name") and s.get("success_email") and s.get("thread_email"))
    body = (f'<div class="pagehead"><div><h1>Partner onboarding</h1><p>Every buyer and publisher gets a private onboarding page with a six-stage road to launch, the paperwork, '
            f'the integration instructions and the people to talk to, plus a branded welcome email. Behind it is Blue Wing\'s onboarding SOP as a checklist, '
            f'and "Ready for Ops" once paperwork, tech details and the test are done.</p></div></div>'
            + ('<p class="note2" style="margin-bottom:16px">Add your partner-success contact, booking link and onboarding thread email under "Team, links and signature" so partners see real names.</p>' if team_missing else "")
            + f'<details class="panel" style="margin-bottom:16px"{"" if rows else " open"}><summary style="cursor:pointer;font-weight:600">Add a partner</summary><div style="margin-top:14px">{_form(None, brands, "new")}'
            f'<div class="byact"><button class="btn primary" type="button" id="addbuyer">Add partner</button></div></div></details>'
            f'<details class="panel" style="margin-bottom:16px"{" open" if team_missing and rows else ""}><summary style="cursor:pointer;font-weight:600">Team, links and signature</summary><div style="margin-top:14px">'
            f'<div class="byform" data-form="settings">'
            f'<span class="hd">Who partners talk to</span>'
            f'<label>Partner-success name<input name="success_name" value="{e(s["success_name"])}" placeholder="Florie K."></label>'
            f'<label>Their title<input name="success_title" value="{e(s["success_title"])}" placeholder="Partner Success Manager"></label>'
            f'<label>Their email<input name="success_email" value="{e(s["success_email"])}" placeholder="name@bluewingads.com"></label>'
            f'<label>Meeting booking link<input name="booking_url" value="{e(s["booking_url"])}" placeholder="https://calendly.com/..."></label>'
            f'<label>Technical contact<input name="tech_name" value="{e(s["tech_name"])}" placeholder="Kunal"></label>'
            f'<label>Their title<input name="tech_title" value="{e(s["tech_title"])}" placeholder="Integrations"></label>'
            f'<label>Their email<input name="tech_email" value="{e(s["tech_email"])}"></label>'
            f'<label>Onboarding thread email<input name="thread_email" value="{e(s["thread_email"])}" placeholder="partners@bluewingads.com"></label>'
            f'<span class="hd">Brand and signature</span>'
            f'<label>Company name<input name="company" value="{e(s["company"])}"></label><label>Website<input name="website" value="{e(s["website"])}" placeholder="https://"></label>'
            f'<span class="hd">Default links for buyers</span>'
            f'<label class="w2">MSA<input name="msa_url" value="{e(s["msa_url"])}" placeholder="https://"></label>'
            f'<label class="w2">IO e-sign<input name="io_url" value="{e(s["io_url"])}" placeholder="https://"></label>'
            f'<label class="w2">Deposit payment page (Stripe Payment Link or similar)<input name="deposit_url" value="{e(s["deposit_url"])}" placeholder="https://"></label>'
            f'<span class="hd">Default links for publishers</span>'
            f'<label class="w2">Publisher agreement<input name="agreement_url" value="{e(s["agreement_url"])}" placeholder="https://"></label>'
            f'<label class="w2">W-9<input name="w9_url" value="{e(s["w9_url"])}" placeholder="https://"></label>'
            f'<label class="w2">Payment setup<input name="payment_url" value="{e(s["payment_url"])}" placeholder="https://"></label></div>'
            f'<p class="note2" style="margin-top:12px">Card details never reach the studio: the deposit step sends the buyer to your payment provider\'s hosted page.</p>'
            f'<div class="byact"><button class="btn primary" type="button" id="savesettings">Save team, links and signature</button></div></div></details>'
            f'<div class="bylist">{cards}</div>'
            f'<dialog class="emdlg" id="emdlg" aria-label="Welcome email"><div class="emhd"><b id="emsubj">Welcome email</b><button class="btn" type="button" id="emclose">Close</button></div>'
            f'<iframe id="emframe" title="Welcome email preview" sandbox=""></iframe><div class="emft"><span class="mut" id="emnote">Copy it into your email (it keeps the design), or open it in your mail app with the plain version. Then mark "Welcome email sent".</span>'
            f'<button class="btn primary" type="button" id="emcopy">{ico("copy")}Copy email</button><a class="btn" id="emmail" href="#">{ico("ext")}Open in mail app</a>'
            f'<button class="btn" type="button" id="emdl">Download .html</button><button class="btn" type="button" id="emsent">{ico("check")}Mark sent</button></div></dialog>')
    js = """<script>(function(){
function data(box){var o={};box.querySelectorAll('input,select,textarea').forEach(function(i){o[i.name]=i.value;});return o;}
function post(url,body,ok){return fetch(url,{method:'POST',body:JSON.stringify(body)}).then(function(r){return r.json().then(function(j){if(!r.ok||j.ok===false){throw new Error(j.error||'Something went wrong');}return j;});}).then(ok).catch(function(e){toast(e.message,false);});}
document.querySelectorAll('[data-kindsel]').forEach(function(s){s.onchange=function(){s.closest('.byform').setAttribute('data-kind',s.value);};});
var add=document.getElementById('addbuyer');if(add){add.onclick=function(){post('/api/buyers/save',data(document.querySelector('[data-form=new]')),function(){location.reload();});};}
var ss=document.getElementById('savesettings');if(ss){ss.onclick=function(){post('/api/buyers/settings',data(document.querySelector('[data-form=settings]')),function(){toast('Team, links and signature saved',true);});};}
var dlg=document.getElementById('emdlg'),cur=null,curId=null;
function openEmail(id){post('/api/buyers/email',{id:id,origin:location.origin},function(j){cur=j;curId=id;document.getElementById('emsubj').textContent=j.subject;document.getElementById('emframe').srcdoc=j.html;
 var q='subject='+encodeURIComponent(j.subject)+(j.cc?'&cc='+encodeURIComponent(j.cc):'')+'&body='+encodeURIComponent(j.text);document.getElementById('emmail').href='mailto:'+encodeURIComponent(j.to||'')+'?'+q;
 if(dlg.showModal){dlg.showModal();}});}
document.getElementById('emclose').onclick=function(){dlg.close();};
document.getElementById('emcopy').onclick=function(){if(!cur){return;}try{var item=new ClipboardItem({'text/html':new Blob([cur.html],{type:'text/html'}),'text/plain':new Blob([cur.text],{type:'text/plain'})});navigator.clipboard.write([item]).then(function(){toast('Email copied. Paste it into a new email.',true);},function(){navigator.clipboard.writeText(cur.text);toast('Copied the plain version',true);});}catch(e){navigator.clipboard.writeText(cur.text);toast('Copied the plain version',true);}};
document.getElementById('emdl').onclick=function(){if(!cur){return;}var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([cur.html],{type:'text/html'}));a.download='welcome-email.html';a.click();};
document.getElementById('emsent').onclick=function(){if(!curId){return;}post('/api/buyers/step',{id:curId,key:'email',state:'done'},function(){sessionStorage.setItem('byopen',curId);location.reload();});};
document.querySelectorAll('.bycard').forEach(function(c){var id=c.getAttribute('data-id');
 c.querySelectorAll('.seg button').forEach(function(b){b.onclick=function(){post('/api/buyers/step',{id:id,key:b.getAttribute('data-step'),state:b.getAttribute('data-state')},function(){sessionStorage.setItem('byopen',id);location.reload();});};});
 var sv=c.querySelector('[data-save]');if(sv){sv.onclick=function(){var d=data(c.querySelector('.byform'));d.id=id;post('/api/buyers/save',d,function(){sessionStorage.setItem('byopen',id);location.reload();});};}
 var ar=c.querySelector('[data-archive]');if(ar){ar.onclick=function(){post('/api/buyers/save',{id:id,archived:true},function(){location.reload();});};}
 var cp=c.querySelector('[data-copy]');if(cp){cp.onclick=function(){var i=c.querySelector('.olink input');i.select();try{navigator.clipboard.writeText(i.value);}catch(e){document.execCommand('copy');}toast('Onboarding link copied',true);};}
 var em=c.querySelector('[data-email]');if(em){em.onclick=function(){openEmail(id);};}
 var tb=c.querySelector('[data-test]');if(tb){tb.onclick=function(){tb.disabled=true;post('/api/buyers/test',{id:id},function(j){toast(j.detail||'Checked',j.ok);if(j.ok){sessionStorage.setItem('byopen',id);location.reload();}}).then(function(){tb.disabled=false;});};}
});
try{var o=sessionStorage.getItem('byopen');if(o){sessionStorage.removeItem('byopen');var el=document.querySelector('.bycard[data-id="'+o+'"]');if(el){el.open=true;el.scrollIntoView({block:'start'});}}}catch(e){}
})();</script>"""
    return shell("Partner onboarding", body, "buyers", "<b>Partner onboarding</b>", js)


def onboard_page(bid):
    return partner_page.onboard_page(bid)
