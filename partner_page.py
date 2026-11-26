"""The partner's private onboarding page (/onboard/<id>) and the branded welcome email: Blue Wing Ads identity, a six-stage roadmap with
progress, the next step up front, named partner-success and technical contacts, one shared onboarding thread and a branded signature."""
import html
import json
import re
import urllib.parse

import buyers

e = html.escape

WING = ('<svg viewBox="0 0 48 32" aria-hidden="true" class="wing"><path d="M2 26C10 25 18 21 24 14c4-5 7-9 22-12-6 5-9 10-13 15-6 7-15 12-31 9Z" fill="currentColor" opacity=".95"/>'
        '<path d="M8 30c8 0 16-3 22-8 3-3 6-6 14-9-4 5-8 9-12 12-6 4-14 6-24 5Z" fill="currentColor" opacity=".55"/></svg>')
ICONS = {  # simple line icons, one per stage
    "match": '<path d="M7 12l3 3 7-7"/><circle cx="12" cy="12" r="9"/>',
    "kit": '<path d="M4 7h16v12H4z"/><path d="M9 7V5h6v2"/><path d="M4 12h16"/>',
    "paper": '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5"/><path d="M9 14l2 2 4-4"/>',
    "tech": '<path d="M9 7V3M15 7V3"/><path d="M6 7h12v4a6 6 0 0 1-12 0z"/><path d="M12 17v4"/>',
    "test": '<path d="M9 3h6"/><path d="M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/><path d="M7.5 15h9"/>',
    "live": '<path d="M5 15c0-6 4-11 7-12 3 1 7 6 7 12l-3 3H8z"/><circle cx="12" cy="10" r="2"/><path d="M9 21l1-3M15 21l-1-3"/>',
    "check": '<path d="M5 12l4 4 10-10"/>',
}


WING_BIG = WING.replace('class="wing"', 'class="wing big"')


def icon(name, cls="ic"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'


def initials(name):
    parts = [p for p in (name or "").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "BW"


def thread_mailto(b, s):
    if not s.get("thread_email"):
        return ""
    subj = f"[Onboarding] {buyers.deal_name(b)}"
    return "mailto:" + s["thread_email"] + "?" + urllib.parse.urlencode({"subject": subj}, quote_via=urllib.parse.quote)


CSS = """:root{--navy:#0b1f44;--navy2:#13306a;--blue:#1d6fe8;--sky:#eaf2ff;--sun:#ffb21e;--mint:#12a37a;--ink:#101828;--mut:#5a6476;--line:#e3e8f1;--bg:#f5f7fb;--card:#fff;--r:18px}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:400 15.5px/1.6 "Plus Jakarta Sans",Inter,system-ui,"Segoe UI",Arial,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--blue)}.wrap{max-width:980px;margin:0 auto;padding:0 20px}
.top{position:sticky;top:0;z-index:20;background:rgba(245,247,251,.86);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;align-items:center;gap:12px;height:64px}.logo{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--navy);font-weight:800;letter-spacing:-.02em;font-size:17px}
.logo .wing{width:34px;height:24px;color:var(--blue)}.pill{font:600 12px/1 inherit;padding:7px 11px;border-radius:99px;background:var(--sky);color:var(--blue)}.top .grow{flex:1}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;padding:0 20px;border-radius:12px;background:var(--blue);color:#fff;text-decoration:none;font-weight:700;font-size:15px;border:0;cursor:pointer;transition:transform .2s,box-shadow .2s,background .2s}
.btn:hover{transform:translateY(-2px);box-shadow:0 10px 24px -10px rgba(29,111,232,.7)}.btn.ghost{background:#fff;color:var(--navy);box-shadow:inset 0 0 0 1.5px var(--line)}.btn.ghost:hover{box-shadow:inset 0 0 0 1.5px var(--blue)}
.btn.sun{background:var(--sun);color:var(--navy)}.btn.off{background:#eef1f6;color:var(--mut);cursor:default;transform:none;box-shadow:none}
.btn:focus-visible,a:focus-visible,input:focus-visible,button:focus-visible{outline:3px solid #8ab8ff;outline-offset:2px}
.hero{position:relative;overflow:hidden;margin:26px 0 22px;border-radius:26px;background:linear-gradient(135deg,var(--navy) 0%,var(--navy2) 55%,var(--blue) 120%);color:#fff;padding:34px 34px 30px}
.hero:before,.hero:after{content:"";position:absolute;border-radius:50%;filter:blur(2px);opacity:.22}.hero:before{width:340px;height:340px;right:-90px;top:-150px;background:radial-gradient(circle,#4f9bff,transparent 65%)}
.hero:after{width:260px;height:260px;left:-90px;bottom:-140px;background:radial-gradient(circle,var(--sun),transparent 65%)}
.hero .wing.big{position:absolute;right:26px;bottom:18px;width:150px;height:100px;color:#fff;opacity:.08}
.hgrid{position:relative;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:24px;align-items:center}
.kick{font:700 12px/1 inherit;letter-spacing:.16em;text-transform:uppercase;color:#a9c8ff}.hero h1{font-size:clamp(28px,4.6vw,42px);line-height:1.08;letter-spacing:-.03em;margin:10px 0 10px;font-weight:800}
.hero p{margin:0 0 16px;color:#d6e3ff;max-width:34em}.chips{display:flex;flex-wrap:wrap;gap:8px}.chips span{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);padding:6px 11px;border-radius:99px;font-size:13px;font-weight:600}
.ring{--p:0;width:132px;height:132px;border-radius:50%;background:conic-gradient(var(--sun) calc(var(--p)*1%),rgba(255,255,255,.14) 0);display:grid;place-items:center;transition:--p 1s}
.ring div{width:104px;height:104px;border-radius:50%;background:var(--navy);display:grid;place-items:center;text-align:center;line-height:1.1}.ring b{font-size:30px;font-weight:800}.ring span{font-size:11.5px;color:#a9c8ff;font-weight:600}
.road{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:26px 22px 22px;margin-bottom:22px}
.road h2,.sec h2{font-size:20px;letter-spacing:-.02em;margin:0 0 4px}.sub{color:var(--mut);margin:0 0 18px;font-size:14.5px}
.track{position:relative;display:grid;grid-template-columns:repeat(6,1fr);gap:6px;padding-top:4px}
.track:before{content:"";position:absolute;left:8%;right:8%;top:30px;height:6px;border-radius:9px;background:#edf1f7}
.track .fill{position:absolute;left:8%;top:30px;height:6px;border-radius:9px;background:linear-gradient(90deg,var(--mint),var(--blue));width:0;transition:width 1.4s cubic-bezier(.2,.7,.2,1)}
.stop{position:relative;text-align:center;text-decoration:none;color:inherit}.dot{position:relative;z-index:1;width:60px;height:60px;margin:0 auto 10px;border-radius:50%;display:grid;place-items:center;background:#fff;border:2px solid var(--line);color:#9aa5b8;transition:transform .3s}
.stop:hover .dot{transform:translateY(-3px)}.dot .ic{width:26px;height:26px}.stop b{display:block;font-size:13.5px;line-height:1.25}.stop small{display:block;color:var(--mut);font-size:11.5px;margin-top:3px;font-weight:600}
.stop.done .dot{background:var(--mint);border-color:var(--mint);color:#fff}.stop.current .dot{background:var(--sun);border-color:var(--sun);color:var(--navy);animation:pulse 2.2s ease-out infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(255,178,30,.55)}70%{box-shadow:0 0 0 14px rgba(255,178,30,0)}100%{box-shadow:0 0 0 0 rgba(255,178,30,0)}}
.next{display:grid;grid-template-columns:auto minmax(0,1fr);gap:18px;align-items:center;background:linear-gradient(120deg,#fff7e6,#fff);border:1.5px solid #ffd98a;border-radius:var(--r);padding:20px 22px;margin-bottom:22px}
.next .badge2{width:54px;height:54px;border-radius:16px;background:var(--sun);color:var(--navy);display:grid;place-items:center}.next .badge2 .ic{width:28px;height:28px}
.next h3{margin:0 0 2px;font-size:18px}.next p{margin:0 0 12px;color:var(--mut)}.acts{display:flex;flex-wrap:wrap;gap:10px}
.sec{background:var(--card);border:1px solid var(--line);border-radius:var(--r);margin-bottom:14px;overflow:hidden}
.sec>summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:44px minmax(0,1fr) auto;gap:14px;align-items:center;padding:16px 20px}
.sec>summary::-webkit-details-marker{display:none}.sec .n{width:44px;height:44px;border-radius:14px;display:grid;place-items:center;background:var(--sky);color:var(--blue);font-weight:800}
.sec.done .n{background:var(--mint);color:#fff}.sec.current .n{background:var(--sun);color:var(--navy)}.sec summary h2{font-size:17px;margin:0}.sec summary p{margin:2px 0 0;color:var(--mut);font-size:13.5px}
.tag{font:700 11.5px/1 inherit;padding:6px 10px;border-radius:99px;white-space:nowrap}.tag.done{background:#e3f5ee;color:var(--mint)}.tag.current{background:#fff1d6;color:#9a5d00}.tag.upcoming{background:#f0f3f8;color:var(--mut)}
.body{padding:0 20px 20px 78px}.items{display:grid;gap:10px}
.item{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:12px;align-items:center;padding:12px 14px;border:1px solid var(--line);border-radius:14px;background:#fbfcfe}
.item .st{width:26px;height:26px;border-radius:50%;border:2px solid #cfd7e4;display:grid;place-items:center;color:#fff}.item.done .st{background:var(--mint);border-color:var(--mint)}.item.done .st .ic{width:15px;height:15px}
.item.sent .st{border-color:var(--sun);background:#fff4dc}.item b{display:block;font-size:14.5px}.item em{font:700 11px/1 inherit;font-style:normal;padding:4px 8px;border-radius:99px;margin-left:6px;vertical-align:1px}.item em.wait{background:#fff1d6;color:#9a5d00}.item em.ok{background:#e3f5ee;color:var(--mint)}.item span.d{display:block;color:var(--mut);font-size:13px}
.spec{background:#f8fafd;border:1px solid var(--line);border-radius:14px;padding:16px 18px;font-size:14px;margin:12px 0}.spec h3{font-size:14px;margin:12px 0 6px}.spec h3:first-child{margin-top:0}
.spec ul{margin:0;padding-left:20px}pre{font:500 12.5px/1.55 ui-monospace,Menlo,Consolas,monospace;background:var(--navy);color:#e6edf9;border-radius:12px;padding:14px;overflow-x:auto;white-space:pre;max-width:100%}
form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px}label{display:grid;gap:5px;font-size:13px;font-weight:600;color:var(--mut)}label.w{grid-column:1/-1}
input{font:inherit;font-size:15px;padding:11px 13px;border:1.5px solid var(--line);border-radius:12px;background:#fff;color:var(--ink);width:100%}input:focus{border-color:var(--blue);outline:none}
.msg{grid-column:1/-1;font-weight:700;margin:0;color:var(--mint)}.copy{display:flex;gap:8px;align-items:center}.copy input{font:500 13px ui-monospace,Menlo,Consolas,monospace}
.team{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:26px 0 14px}
.person{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:20px;display:grid;grid-template-columns:auto minmax(0,1fr);gap:14px;align-items:start}
.av{width:54px;height:54px;border-radius:18px;display:grid;place-items:center;font-weight:800;font-size:18px;color:#fff;background:linear-gradient(135deg,var(--blue),#5aa0ff)}.av.t{background:linear-gradient(135deg,var(--navy2),#3d5fa8)}
.person .role{font:700 11px/1 inherit;letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}.person h3{margin:6px 0 2px;font-size:17px}.person p{margin:0 0 12px;color:var(--mut);font-size:14px}
.thread{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:16px;align-items:center;background:var(--sky);border-radius:var(--r);padding:18px 20px;margin-bottom:26px}
.thread .ic{width:30px;height:30px;color:var(--blue)}.thread b{display:block}.thread span{color:var(--mut);font-size:14px}
.sig{border-top:1px solid var(--line);padding:22px 0 50px;display:flex;gap:14px;align-items:center;color:var(--mut);font-size:13.5px}.sig .wing{width:40px;height:28px;color:var(--blue)}.sig b{color:var(--navy)}
.party{position:fixed;inset:0;pointer-events:none;z-index:50;overflow:hidden}.party i{position:absolute;top:-12px;width:9px;height:14px;border-radius:2px;animation:fall 2.8s linear forwards}
@keyframes fall{to{transform:translateY(110vh) rotate(720deg)}}
@media(max-width:760px){.logo{white-space:nowrap}.top .pill{display:none}.top .btn{min-height:38px!important;padding:0 14px;font-size:14px}.hero{padding:26px 22px;border-radius:22px}.hgrid{grid-template-columns:1fr}.ring{width:112px;height:112px}.ring div{width:88px;height:88px}
.track{grid-template-columns:1fr;gap:0}.track:before,.track .fill{display:none}.stop{display:grid;grid-template-columns:52px minmax(0,1fr);gap:12px;align-items:center;text-align:left;padding:8px 0;position:relative}
.stop:not(:last-of-type):after{content:"";position:absolute;left:25px;top:52px;bottom:-8px;width:3px;background:#edf1f7;border-radius:3px}.stop.done:not(:last-of-type):after{background:var(--mint)}
.dot{width:52px;height:52px;margin:0}.team{grid-template-columns:1fr}.body{padding:0 16px 18px}.sec>summary{grid-template-columns:40px minmax(0,1fr);padding:14px 16px}.sec summary .tag{grid-column:2;justify-self:start}
.next{grid-template-columns:1fr}.thread{grid-template-columns:auto minmax(0,1fr)}.thread .btn{grid-column:1/-1}form{grid-template-columns:1fr}.item{grid-template-columns:auto minmax(0,1fr)}.item .btn{grid-column:2;justify-self:start}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}html{scroll-behavior:auto}}"""


def _spec(b):
    if buyers.kind_of(b) == "publisher":
        return ('<div class="spec"><h3>How tracking works</h3><ul><li>Send traffic to your personal tracking link below. It records each click with your sub ID.</li>'
                '<li>When a click turns into a call, lead or sale, Everflow fires a conversion. If you give us your postback URL we fire it back to you in real time.</li>'
                '<li>Only send the traffic sources and geos in your offer kit; we check quality daily and pause sources that do not convert.</li></ul></div>')
    product = b.get("product", "calls")
    if product == "leads":
        sample = {"first_name": "Jane", "last_name": "Doe", "phone": "+15555550123", "email": "jane@example.com", "zip": "33062", "state": "FL",
                  "ip_address": "203.0.113.7", "landing_page_url": "https://example-brand.com/", "trustedform_cert_url": "https://cert.trustedform.com/...",
                  "jornaya_leadid": "...", "consent_text": "By submitting, I agree to be contacted...", "consent_timestamp": "2026-11-25T14:03:11Z",
                  "sub_id": "publisher-123", "click_id": "abc123"}
        return ('<div class="spec"><h3>How leads reach you</h3><ul><li>We post each lead to your endpoint in real time as JSON over HTTPS.</li>'
                '<li>Every lead carries a TrustedForm certificate and the consumer\'s last name, the two fields buyers most often reject pings over.</li>'
                '<li>Answer within 10 seconds with HTTP 200 and a JSON body saying accepted or rejected, with a reason when rejected.</li></ul>'
                f'<h3>Sample lead</h3><pre>{e(json.dumps(sample, indent=2))}</pre>'
                '<h3>Sample response</h3><pre>{"status": "accepted", "lead_id": "YOUR-ID"}\n{"status": "rejected", "reason": "duplicate"}</pre></div>')
    if product == "clicks":
        return ('<div class="spec"><h3>How clicks reach you</h3><ul><li>We send click traffic to your tracking link, with our click ID in the parameter you name.</li>'
                '<li>Conversions come back to us by server-to-server postback carrying that click ID and the payout. We share our postback URL during setup.</li></ul></div>')
    return ('<div class="spec"><h3>How calls reach you</h3><ul><li>Callers dial a tracked number on our page; we forward the live call to your number with the caller\'s ID passed through.</li>'
            '<li>Every call is logged with its source, so you only pay for calls that meet the billable length we agree.</li>'
            '<li>We respect your hours, concurrency limit and daily cap, and route calls elsewhere when you are closed or full.</li></ul></div>')


def _btn(url, text, cls=""):
    return f'<a class="btn {cls}" href="{e(url)}" target="_blank" rel="noopener">{e(text)}</a>' if url else '<span class="btn off">We\'ll email you this link</span>'


def _item(state, title, desc, action=""):
    tick = icon("check") if state == "done" else ""
    if state == "done" and 'class="btn' in action:  # finished: keep the link but make it quiet
        action = action.replace('class="btn ', 'class="btn ghost ', 1).replace('class="btn"', 'class="btn ghost"', 1)
        action = re.sub(r'>([^<]+)</a>$', '>View</a>', action) if action.endswith("</a>") and "off" not in action else ""
    flag = ' <em class="wait">Waiting on you</em>' if state == "sent" else (' <em class="ok">Done</em>' if state == "done" else "")
    return f'<div class="item {state}"><span class="st">{tick}</span><div><b>{e(title)}{flag}</b><span class="d">{e(desc)}</span></div>{action}</div>'


def stage_content(b, key, s, lk):
    """The partner-facing content of one roadmap stage."""
    st = b.get("steps", {})
    state = lambda k: st.get(k, {}).get("state", "todo")
    pub = buyers.kind_of(b) == "publisher"
    if key == "match":
        book = _btn(s.get("booking_url"), "Book a kickoff call", "ghost") if s.get("booking_url") else ""
        return ('<div class="items">' + _item(state("campaign"), "Campaign picked", buyers.deal_name(b)) +
                _item(state("email"), "Welcome kit sent", "Your welcome email with this roadmap and who to talk to.", book) + '</div>')
    if key == "kit":
        if pub:
            tl = lk.get("tracking_link")
            copy = (f'<div class="copy"><input readonly value="{e(tl)}" aria-label="Your tracking link"><button class="btn ghost" type="button" data-copy>Copy</button></div>' if tl
                    else '<span class="btn off">Your link is on its way</span>')
            return ('<div class="items">' + _item(state("kit"), "Offer kit", f"Payout {b.get('payout') or 'as agreed'}, approved creatives, allowed traffic sources and compliance rules.") +
                    _item(state("links"), "Your tracking link", "Use this link for every click you send us.") + f'</div><div style="margin-top:12px">{copy}</div>')
        return ('<div class="items">' + _item(state("verify"), "Campaign details confirmed", f"Payout {b.get('payout') or 'as agreed'}; hours, caps, geos and qualification rules.") +
                _item(state("creatives"), "Creatives approved", "The landing page, scripts and ads your callers or leads come from.") + '</div>')
    if key == "paper":
        if pub:
            return ('<div class="items">' + _item(state("agreement"), "Publisher agreement", "Our terms for running the offer.", _btn(lk["agreement_url"], "Sign the agreement")) +
                    _item(state("tax"), "W-9", "So we can pay you.", _btn(lk["w9_url"], "Fill in the W-9")) +
                    _item(state("payment"), "Payment details", "Where and how often you get paid.", _btn(lk["payment_url"], "Set up payments")) + '</div>')
        dep = b.get("deposit_amount")
        return ('<div class="items">' + _item(state("msa"), "Master service agreement", "Our standard terms. Reply on the thread with any redlines.", _btn(lk["msa_url"], "Review and sign")) +
                _item(state("io"), "Insertion order", "Payout, caps, hours and geos for this campaign, signed online.", _btn(lk["io_url"], "Sign the IO")) +
                _item(state("deposit"), "First-lead deposit", (f"{dep} covers your first leads. " if dep else "") + "Your card goes on our payment provider's secure page; we never see it.",
                      _btn(lk["deposit_url"], "Add a card securely")) + '</div>')
    if key == "tech":
        fields = "".join(f'<label class="{"w" if i == len(buyers.tech_fields(b)) - 1 and len(buyers.tech_fields(b)) % 2 else ""}">{e(lab)}<input name="{k}" value="{e((b.get("tech") or {}).get(k, ""))}" maxlength="500"></label>'
                         for i, (k, lab) in enumerate(buyers.tech_fields(b)))
        sent = (b.get("tech") or {}).get("submitted")
        return (_spec(b) + f'<form id="techf">{fields}<div class="acts" style="grid-column:1/-1"><button class="btn" type="submit">{"Update my details" if sent else "Send my details"}</button></div>'
                f'<p class="msg" id="techmsg" role="status" aria-live="polite">{"Got your details. Thanks!" if sent else ""}</p></form>')
    if key == "test":
        what = "click and conversion" if pub else ("call" if b.get("product") == "calls" else "lead" if b.get("product") == "leads" else "click")
        return '<div class="items">' + _item(state("test"), f"Test {what}", f"We send a test {what} and you confirm it arrived. We fix anything odd before real traffic flows.") + '</div>'
    done = state("live" if pub else "handoff") == "done"
    return ('<div class="items">' + _item(state("live" if pub else "handoff"), "Open for business" if done else "Launch",
                                          "You're live. We watch traffic and quality every day and keep you posted on the thread." if done else "Once the test passes we switch you on.") + '</div>')


def onboard_page(bid):
    b = buyers.get(bid)
    if not b or b.get("archived"):
        return None
    s = buyers.settings()
    lk = buyers.links(b)
    sg = buyers.stages(b)
    p = buyers.progress(b)
    pub = buyers.kind_of(b) == "publisher"
    first = (b.get("contact_name") or "").split()[0] if b.get("contact_name") else ""
    pct = round(100 * p["stages_done"] / len(sg))
    all_done = p["stages_done"] == len(sg)
    cur = next((x for x in sg if x["state"] == "current"), sg[-1])
    stops = "".join(f'<a class="stop {x["state"]}" href="#s-{x["key"]}"><span class="dot">{icon("check" if x["state"] == "done" else x["key"])}</span>'
                    f'<span><b>{e(x["label"])}</b><small>{("Done " + buyers.stamp(x["done_at"])[:6]) if x["state"] == "done" else "You are here" if x["state"] == "current" else f"Stop {i + 1}"}</small></span></a>'
                    for i, x in enumerate(sg))
    chips = "".join(f"<span>{e(t)}</span>" for t in ((("You send " if pub else "You buy ") + (buyers.PRODUCTS.get(b.get("product"), "") if not pub else "traffic")),
                                                    b.get("payout") and ("Payout " + b["payout"]), b.get("vertical")) if t)
    secs = ""
    for i, x in enumerate(sg):
        tagtxt = {"done": "Done", "current": "In progress" if x["started"] else "Up next", "upcoming": "Coming up"}[x["state"]]
        secs += (f'<details class="sec {x["state"]}" id="s-{x["key"]}"{" open" if x["state"] == "current" else ""}><summary><span class="n">{icon("check") if x["state"] == "done" else i + 1}</span>'
                 f'<div><h2>{e(x["label"])}</h2><p>{e(x["blurb"])}</p></div><span class="tag {x["state"]}">{tagtxt}</span></summary><div class="body">{stage_content(b, x["key"], s, lk)}</div></details>')
    nxt = ("" if all_done else
           f'<div class="next"><div class="badge2">{icon(cur["key"])}</div><div><h3>Up next: {e(cur["label"])}</h3><p>{e(cur["blurb"])}</p>'
           f'<div class="acts"><a class="btn sun" href="#s-{cur["key"]}">Take me there</a>{_btn(s.get("booking_url"), "Book a call with us", "ghost") if s.get("booking_url") else ""}</div></div></div>')
    sname, tname = s.get("success_name") or "Your partner-success team", s.get("tech_name") or "Our tech team"
    team = (f'<div class="team"><div class="person"><div class="av">{e(initials(s.get("success_name")))}</div><div><span class="role">Partner success</span><h3>{e(sname)}</h3>'
            f'<p>{e(s.get("success_title") or "Your main contact from kickoff to launch.")}</p><div class="acts">'
            + (_btn(s["booking_url"], "Book a meeting") if s.get("booking_url") else "")
            + (f'<a class="btn ghost" href="mailto:{e(s["success_email"])}">Email {e(sname.split()[0])}</a>' if s.get("success_email") else "")
            + f'</div></div></div><div class="person"><div class="av t">{e(initials(s.get("tech_name")))}</div><div><span class="role">Technical integration</span><h3>{e(tname)}</h3>'
            f'<p>{e(s.get("tech_title") or "Sets up your tracking, routing and tests.")}</p><div class="acts">'
            + (f'<a class="btn ghost" href="mailto:{e(s["tech_email"])}">Email {e(tname.split()[0])}</a>' if s.get("tech_email") else "")
            + '<a class="btn ghost" href="#s-tech">Integration instructions</a></div></div></div></div>')
    tm = thread_mailto(b, s)
    thread = (f'<div class="thread"><svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
              f'<path d="M4 5h16v11H8l-4 4z"/><path d="M8 9h8M8 12h5"/></svg><div><b>One thread for everything</b><span>Send documents, questions and updates to {e(s["thread_email"])} '
              f'so the whole team sees them in one place.</span></div><a class="btn" href="{e(tm)}">Write on the thread</a></div>') if tm else ""
    sig = (f'<footer class="sig">{WING}<div><b>{e(s["company"])}</b> &middot; Partner onboarding<br>'
           + (f'{e(s["success_name"])}{", " + e(s["success_title"]) if s.get("success_title") else ""} &middot; ' if s.get("success_name") else "")
           + (f'<a href="mailto:{e(s["success_email"])}">{e(s["success_email"])}</a>' if s.get("success_email") else "")
           + (f' &middot; <a href="{e(s["website"])}" target="_blank" rel="noopener">{e(s["website"].replace("https://", ""))}</a>' if s.get("website") else "") + '</div></footer>')
    hello = f"Welcome aboard, {e(first)}." if first else "Welcome aboard."
    lead = ("You're live. Thanks for building this with us." if all_done else
            f"Here's your road to launch for <b>{e(buyers.deal_name(b))}</b>. Six stops, and we're with you at every one.")
    body = (f'<header class="top"><div class="wrap"><a class="logo" href="#">{WING}{e(s["company"])}</a><span class="pill">Partner onboarding</span><span class="grow"></span>'
            + (f'<a class="btn ghost" href="{e(s["booking_url"])}" target="_blank" rel="noopener" style="min-height:40px">Book a call</a>' if s.get("booking_url") else "")
            + f'</div></header><main class="wrap"><section class="hero">{WING_BIG}<div class="hgrid"><div><span class="kick">{"Publisher" if pub else "Buyer"} onboarding</span>'
            f'<h1>{hello}</h1><p>{lead}</p><div class="chips">{chips}</div></div><div class="ring" style="--p:{pct}" role="img" aria-label="{p["stages_done"]} of 6 stages done">'
            f'<div><span><b>{p["stages_done"]}/6</b><br>stages done</span></div></div></div></section>'
            f'<section class="road" aria-label="Your onboarding roadmap"><h2>Your road to launch</h2><p class="sub">Tap any stop to jump to it. Your progress updates as we go.</p>'
            f'<div class="track"><span class="fill" data-w="{max(0, min(84, 84 * (p["stages_done"] / 5 if p["stages_done"] < 6 else 1)))}"></span>{stops}</div></section>'
            f'{nxt}{secs}{team}{thread}{sig}</main>'
            + ('<div class="party" id="party" aria-hidden="true"></div>' if all_done else ""))
    js = ("<script>(function(){var f=document.querySelector('.track .fill');if(f){requestAnimationFrame(function(){f.style.width=f.getAttribute('data-w')+'%';});}"
          "document.querySelectorAll('[data-copy]').forEach(function(b){b.onclick=function(){var i=b.parentNode.querySelector('input');i.select();try{navigator.clipboard.writeText(i.value);}catch(e){document.execCommand('copy');}b.textContent='Copied';setTimeout(function(){b.textContent='Copy';},1800);};});"
          "var tf=document.getElementById('techf'),m=document.getElementById('techmsg');if(tf){tf.onsubmit=function(ev){ev.preventDefault();var o={};tf.querySelectorAll('input').forEach(function(i){o[i.name]=i.value;});"
          "m.style.color='';m.textContent='Sending...';fetch(location.pathname.replace(/\\/$/,'')+'/tech',{method:'POST',body:JSON.stringify(o)}).then(function(r){return r.json();}).then(function(j){if(j.ok){m.textContent='Got your details. Thanks! We\\'ll confirm the test on the thread.';}else{m.style.color='#b42318';m.textContent=j.error||'Something went wrong. Please try again.';}})"
          ".catch(function(){m.style.color='#b42318';m.textContent='Something went wrong. Please try again.';});};}"
          "var pt=document.getElementById('party');if(pt&&!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)){var c=['#ffb21e','#1d6fe8','#12a37a','#ff6b6b','#8ab8ff'];"
          "for(var i=0;i<70;i++){var x=document.createElement('i');x.style.left=Math.random()*100+'%';x.style.background=c[i%c.length];x.style.animationDelay=(Math.random()*1.2)+'s';x.style.transform='rotate('+Math.random()*360+'deg)';pt.appendChild(x);}"
          "setTimeout(function(){pt.remove();},4500);}})();</script>")
    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="robots" content="noindex,nofollow"><title>Welcome aboard | {e(s["company"])} partner onboarding</title>{fonts}<style>{CSS}</style></head><body>{body}{js}</body></html>')


# ------------------------------------------------------------------ the branded welcome email (email-safe HTML: tables and inline styles)

def welcome_email(b, link):
    s = buyers.settings()
    sg = buyers.stages(b)
    pub = buyers.kind_of(b) == "publisher"
    first = (b.get("contact_name") or "").split()[0] if b.get("contact_name") else "there"
    company = s["company"]
    subject = f"Welcome to {company}: your road to launch for {buyers.deal_name(b)}"
    nav, blue, sun, mint, mut = "#0b1f44", "#1d6fe8", "#ffb21e", "#12a37a", "#5a6476"
    font = "font-family:'Plus Jakarta Sans',Segoe UI,Arial,sans-serif"
    rows = ""
    for i, x in enumerate(sg):
        done = x["state"] == "done"
        bg = mint if done else (sun if x["state"] == "current" else "#e3e8f1")
        col = "#ffffff" if done else nav
        rows += (f'<tr><td width="44" valign="top" style="padding:0 0 14px"><div style="width:32px;height:32px;border-radius:16px;background:{bg};color:{col};text-align:center;line-height:32px;font-weight:800;{font};font-size:14px">'
                 f'{"&#10003;" if done else i + 1}</div></td><td valign="top" style="padding:4px 0 14px;{font}"><div style="font-size:15px;font-weight:700;color:{nav}">{e(x["label"])}'
                 f'{" <span style=&quot;color:#9a5d00;font-size:12px;font-weight:700&quot;>&middot; you are here</span>" if x["state"] == "current" else ""}</div>'
                 f'<div style="font-size:13.5px;color:{mut};line-height:1.5">{e(x["blurb"])}</div></td></tr>')
    first_steps = (["Sign the publisher agreement and send your W-9", "Grab your tracking link and send us your postback", "We fire a test conversion together, then you go live"] if pub else
                   ["Sign the MSA and the insertion order online", "Add a card for the first-lead deposit on the secure payment page",
                    "Send your " + ("destination number" if b.get("product") == "calls" else "lead endpoint" if b.get("product") == "leads" else "tracking link") + ", then we run a test"])
    steps_html = "".join(f'<tr><td width="26" valign="top" style="{font};color:{blue};font-weight:800;font-size:15px;padding:0 0 8px">{i + 1}.</td>'
                         f'<td style="{font};font-size:15px;color:{nav};padding:0 0 8px">{e(t)}</td></tr>' for i, t in enumerate(first_steps))
    btn = lambda url, text, bg, fg: (f'<a href="{e(url)}" style="display:inline-block;background:{bg};color:{fg};{font};font-size:15px;font-weight:700;text-decoration:none;'
                                     f'padding:13px 22px;border-radius:12px;margin:0 8px 8px 0">{e(text)}</a>') if url else ""
    contacts = ""
    if s.get("success_name") or s.get("success_email"):
        contacts += (f'<td valign="top" width="50%" style="padding:0 8px 0 0;{font}"><div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:{mut};font-weight:700">Partner success</div>'
                     f'<div style="font-size:15px;font-weight:700;color:{nav};margin-top:4px">{e(s.get("success_name") or "Partner success")}</div>'
                     f'<div style="font-size:13.5px;color:{mut}">{e(s.get("success_email"))}</div>'
                     + (f'<div style="margin-top:8px"><a href="{e(s["booking_url"])}" style="color:{blue};font-weight:700;text-decoration:none;font-size:14px">Book a meeting &rarr;</a></div>' if s.get("booking_url") else "")
                     + '</td>')
    if s.get("tech_name") or s.get("tech_email"):
        contacts += (f'<td valign="top" width="50%" style="padding:0 0 0 8px;{font}"><div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:{mut};font-weight:700">Technical integration</div>'
                     f'<div style="font-size:15px;font-weight:700;color:{nav};margin-top:4px">{e(s.get("tech_name") or "Tech team")}</div>'
                     f'<div style="font-size:13.5px;color:{mut}">{e(s.get("tech_email"))}</div>'
                     f'<div style="margin-top:8px"><a href="{e(link)}#s-tech" style="color:{blue};font-weight:700;text-decoration:none;font-size:14px">Integration instructions &rarr;</a></div></td>')
    thread = (f'<tr><td style="padding:18px 22px;background:#eaf2ff;border-radius:14px;{font};font-size:14px;color:{nav}"><b>One thread for everything.</b> Reply to this email '
              f'(we copy <a href="mailto:{e(s["thread_email"])}" style="color:{blue}">{e(s["thread_email"])}</a>) with documents and questions, so the whole team sees them.</td></tr>'
              f'<tr><td height="22"></td></tr>') if s.get("thread_email") else ""
    sig = (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:6px"><tr><td style="padding-right:12px" valign="middle">'
           f'<div style="width:42px;height:42px;border-radius:12px;background:{nav};color:{sun};text-align:center;line-height:42px;font-weight:800;{font};font-size:15px">BW</div></td>'
           f'<td style="{font};font-size:13.5px;color:{mut};line-height:1.45"><b style="color:{nav};font-size:15px">{e(s.get("success_name") or company + " team")}</b><br>'
           + (f'{e(s["success_title"])}, ' if s.get("success_title") else "") + f'{e(company)}<br>'
           + (f'<a href="mailto:{e(s["success_email"])}" style="color:{blue};text-decoration:none">{e(s["success_email"])}</a>' if s.get("success_email") else "")
           + (f' &middot; <a href="{e(s["website"])}" style="color:{blue};text-decoration:none">{e(s["website"].replace("https://", ""))}</a>' if s.get("website") else "")
           + '</td></tr></table>')
    html_doc = (f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{e(subject)}</title></head>'
                f'<body style="margin:0;background:#f5f7fb"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f7fb"><tr><td align="center" style="padding:28px 12px">'
                f'<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:22px;overflow:hidden">'
                f'<tr><td style="background:{nav};background-image:linear-gradient(135deg,{nav},#13306a 60%,{blue});padding:30px 30px 28px;{font}">'
                f'<div style="color:#a9c8ff;font-size:12px;letter-spacing:.16em;text-transform:uppercase;font-weight:700">{e(company)} &middot; {"Publisher" if pub else "Buyer"} onboarding</div>'
                f'<div style="color:#ffffff;font-size:30px;line-height:1.15;font-weight:800;margin:10px 0 8px;letter-spacing:-.02em">Welcome aboard, {e(first)}.</div>'
                f'<div style="color:#d6e3ff;font-size:15px;line-height:1.55">Great talking with you. Here\'s your road to launch for <b style="color:#fff">{e(buyers.deal_name(b))}</b>: six stops, and we\'re with you at every one.</div></td></tr>'
                f'<tr><td style="padding:28px 30px 6px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
                f'<tr><td style="{font};font-size:18px;font-weight:800;color:{nav};padding-bottom:12px">Your next steps</td></tr>'
                f'<tr><td><table role="presentation" cellpadding="0" cellspacing="0">{steps_html}</table></td></tr>'
                f'<tr><td style="padding:14px 0 22px">{btn(link, "Open my onboarding page", blue, "#ffffff")}{btn(s.get("booking_url"), "Book a kickoff call", sun, nav)}</td></tr>'
                f'<tr><td style="{font};font-size:18px;font-weight:800;color:{nav};padding-bottom:14px">Your road to launch</td></tr>'
                f'<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr><tr><td height="10"></td></tr>'
                + (f'<tr><td style="padding:18px 0;border-top:1px solid #e3e8f1"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{contacts}</tr></table></td></tr><tr><td height="8"></td></tr>' if contacts else "")
                + f'{thread}<tr><td style="{font};font-size:15px;color:{nav};padding-bottom:6px">Talk soon,</td></tr><tr><td style="padding-bottom:28px">{sig}</td></tr></table></td></tr></table>'
                f'<div style="{font};font-size:12px;color:#8a93a3;padding:14px">Sent by {e(company)} partner onboarding.</div></td></tr></table></body></html>')
    text = (f"Welcome aboard, {first}.\n\nGreat talking with you. Here's your road to launch for {buyers.deal_name(b)}.\n\nYour next steps:\n"
            + "".join(f"{i + 1}. {t}\n" for i, t in enumerate(first_steps))
            + f"\nYour onboarding page (paperwork, specs and progress): {link}\n"
            + (f"Book a kickoff call: {s['booking_url']}\n" if s.get("booking_url") else "")
            + "\nYour road to launch:\n" + "".join(f"{i + 1}. {x['label']}{' (done)' if x['state'] == 'done' else ' (you are here)' if x['state'] == 'current' else ''}: {x['blurb']}\n" for i, x in enumerate(sg))
            + (f"\nPartner success: {s.get('success_name', '')} {s.get('success_email', '')}\n" if s.get("success_name") or s.get("success_email") else "")
            + (f"Technical integration: {s.get('tech_name', '')} {s.get('tech_email', '')}\n" if s.get("tech_name") or s.get("tech_email") else "")
            + (f"\nOne thread for everything: reply to this email (we copy {s['thread_email']}) so the whole team sees it.\n" if s.get("thread_email") else "")
            + f"\nTalk soon,\n{s.get('success_name') or company + ' team'}\n" + (f"{s['success_title']}, " if s.get("success_title") else "") + f"{company}\n"
            + (f"{s['success_email']}\n" if s.get("success_email") else "") + (f"{s['website']}\n" if s.get("website") else ""))
    return {"subject": subject, "html": html_doc, "text": text, "to": b.get("contact_email", ""), "cc": s.get("thread_email", "")}
