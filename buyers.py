"""Buyer onboarding: Blue Wing's onboarding SOP (Sydney, Sep 2026) as a tracked checklist per buyer, plus a private link the buyer opens to
sign the MSA and IO, add a card for the first-lead deposit, read the API specs for their product and send their technical details.

Records live in the meta table (key "buyers"), so they persist on Vercel through the database like the rest of the studio.
Card details never touch the studio: the deposit step links to a hosted payment page (for example a Stripe Payment Link)."""
import json
import re
import secrets
import time

import store

STEPS = [  # (key, label, what it means). Order follows the SOP; the to-do adds the deposit, tech and test steps.
    ("campaign", "Campaign identified", "One specific campaign picked out of everything discussed (SOP 1)."),
    ("email", "Post-call email sent", "Thank-you email naming the campaign and whose paperwork will be used (SOP 2)."),
    ("msa", "MSA signed", "MSA sent or requested, redlines handled, signed by both sides (SOP 3 to 5)."),
    ("verify", "Campaign details verified", "Payout, hours, caps, geos and qualification rules confirmed (SOP 6)."),
    ("creatives", "Creatives approved", "Landing page, scripts and ads the buyer must approve (SOP 7)."),
    ("io", "IO signed", "Insertion order sent by e-sign and signed (SOP 8 and 9)."),
    ("deposit", "First-lead deposit received", "Buyer added a card on the payment page for the first-lead deposit."),
    ("tech", "Tech details received", "Destination number or lead endpoint received from the buyer's onboarding page."),
    ("test", "First test passed", "A test call or test lead reached the buyer and they confirmed it."),
    ("handoff", "Ops handoff", "Ready-to-test signal sent to Ops; Ops confirms when the campaign is live (SOP 10)."),
    ("folder", "Folder updated", "Signed paperwork and approved creatives filed (SOP 11)."),
]
STEP_KEYS = [k for k, _, _ in STEPS]
STATES = ("todo", "sent", "done")
READY_FOR_OPS = ("msa", "io", "deposit", "tech", "test")  # everything Ops needs before the campaign can be tested
PRODUCTS = {"calls": "Calls", "leads": "Leads", "clicks": "Clicks"}
FIELDS = ("company", "contact_name", "contact_email", "vertical", "brand", "product", "payout", "io_number", "msa_url", "io_url", "deposit_url",
          "deposit_amount", "notes", "archived")
TECH = {  # what the buyer sends back from the onboarding page, per product
    "calls": [("destination", "Number to send calls to (or SIP address)"), ("hours", "Hours you take calls, with time zone"), ("concurrency", "Most calls at once"),
              ("daily_cap", "Daily call cap"), ("billable", "Billable call length in seconds"), ("geos", "States you accept"), ("contact", "Who to call about routing problems")],
    "leads": [("endpoint", "Lead endpoint URL"), ("auth", "How to authenticate (API key header, basic auth, none)"), ("required", "Fields you require beyond ours"),
              ("response", "What your success and rejection responses look like"), ("daily_cap", "Daily lead cap"), ("geos", "States you accept"), ("contact", "Technical contact")],
    "clicks": [("tracking_url", "Your tracking link, with where the click ID goes"), ("postback", "Will you fire our postback, or should we fire yours?"),
               ("daily_cap", "Daily click cap"), ("geos", "Geos you accept"), ("contact", "Technical contact")],
}
SETTINGS_KEY, KEY = "buyer_settings", "buyers"


def _get(key, default):
    r = store.q("select value from meta where key=?", (key,))
    try:
        return json.loads(r[0]["value"]) if r else default
    except Exception:
        return default


def _set(key, obj):
    store.x("insert or replace into meta(key,value) values(?,?)", (key, json.dumps(obj)))


def settings():
    s = _get(SETTINGS_KEY, {})
    return {"msa_url": s.get("msa_url", ""), "io_url": s.get("io_url", ""), "deposit_url": s.get("deposit_url", ""), "support_email": s.get("support_email", "")}


def save_settings(d, actor):
    s = settings()
    for k in s:
        if k in d:
            s[k] = _clean_url(d[k]) if k.endswith("_url") else _clean(d[k], 120)
    _set(SETTINGS_KEY, s)
    store.log_event("buyers", "buyer.settings", "Default MSA, IO and deposit links updated", actor)
    return s


def _clean(v, n=300):
    return re.sub(r"[\x00-\x1f\x7f]", " ", str(v or "")).strip()[:n]


def _clean_url(v):
    v = _clean(v, 500)
    if v and not re.match(r"^https://\S+$", v):
        raise ValueError("Links must start with https://")
    return v


def all_buyers(include_archived=False):
    d = _get(KEY, {})
    rows = [b for b in d.values() if include_archived or not b.get("archived")]
    return sorted(rows, key=lambda b: b.get("updated", ""), reverse=True)


def get(bid):
    return _get(KEY, {}).get(bid)


def deal_name(b):
    """SOP naming: [Business Name] - [Vertical] IO #[IO Number]"""
    name = b.get("company") or "New buyer"
    if b.get("vertical"):
        name += f" - {b['vertical']}"
    if b.get("io_number"):
        name += f" IO #{b['io_number']}"
    return name


def links(b):
    """The buyer's own link if set, otherwise the team default from settings."""
    s = settings()
    return {k: b.get(k) or s.get(k, "") for k in ("msa_url", "io_url", "deposit_url")}


def progress(b):
    st = b.get("steps", {})
    done = sum(1 for k in STEP_KEYS if st.get(k, {}).get("state") == "done")
    ready = all(st.get(k, {}).get("state") == "done" for k in READY_FOR_OPS)
    return {"done": done, "total": len(STEP_KEYS), "ready": ready, "next": next((lab for k, lab, _ in STEPS if st.get(k, {}).get("state") != "done"), "")}


def save(d, actor):
    db = _get(KEY, {})
    bid = d.get("id") or ""
    b = db.get(bid) if bid else None
    if not b:
        if not _clean(d.get("company")):
            raise ValueError("Add the buyer's company name.")
        bid = secrets.token_urlsafe(16)  # also the private part of the buyer's onboarding link
        b = {"id": bid, "created": store.now(), "steps": {}, "tech": {}}
    for f in FIELDS:
        if f not in d:
            continue
        if f.endswith("_url"):
            b[f] = _clean_url(d[f])
        elif f == "contact_email":
            v = _clean(d[f], 160)
            if v and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
                raise ValueError("That email address does not look right.")
            b[f] = v
        elif f == "product":
            b[f] = d[f] if d[f] in PRODUCTS else "calls"
        elif f == "archived":
            b[f] = bool(d[f])
        else:
            b[f] = _clean(d[f], 2000 if f == "notes" else 160)
    b.setdefault("product", "calls")
    b["updated"] = store.now()
    new = bid not in db
    db[bid] = b
    _set(KEY, db)
    store.log_event(b.get("brand") or "buyers", "buyer.added" if new else "buyer.updated", deal_name(b), actor)
    return b


def set_step(bid, key, state, actor, note=""):
    if key not in STEP_KEYS or state not in STATES:
        raise ValueError("Unknown step or state.")
    db = _get(KEY, {})
    b = db.get(bid)
    if not b:
        raise ValueError("That buyer is no longer here. Refresh the page.")
    was_ready = progress(b)["ready"]
    b.setdefault("steps", {})[key] = {"state": state, "ts": store.now(), "by": actor, "note": _clean(note, 200)}
    b["updated"] = store.now()
    db[bid] = b
    _set(KEY, db)
    label = dict((k, lab) for k, lab, _ in STEPS)[key]
    store.log_event(b.get("brand") or "buyers", "buyer.step", f"{deal_name(b)}: {label} = {state}", actor)
    if progress(b)["ready"] and not was_ready:
        store.log_event(b.get("brand") or "buyers", "buyer.ready_for_ops", f"{deal_name(b)} is ready for Ops: paperwork, deposit, tech details and test are done", actor)
    return b


def submit_tech(bid, d):
    """Called from the buyer's own onboarding page (no sign-in: the unguessable link is the key)."""
    db = _get(KEY, {})
    b = db.get(bid)
    if not b or b.get("archived"):
        raise ValueError("This onboarding link is no longer active.")
    fields = TECH.get(b.get("product", "calls"), [])
    tech = {k: _clean(d.get(k), 500) for k, _ in fields if _clean(d.get(k), 500)}
    if not tech:
        raise ValueError("Fill in at least one field.")
    tech["submitted"] = store.now()
    b["tech"] = tech
    st = b.setdefault("steps", {})
    if st.get("tech", {}).get("state") != "done":
        st["tech"] = {"state": "sent", "ts": store.now(), "by": "buyer", "note": "Submitted from the onboarding page; check and mark done"}
    b["updated"] = store.now()
    db[bid] = b
    _set(KEY, db)
    store.log_event(b.get("brand") or "buyers", "buyer.tech_submitted", f"{deal_name(b)} sent their technical details", "buyer")
    return b


def run_test(bid, actor):
    """Calls: finds the test call placed to the brand's Ringba campaign in the last hour (integrations.place_test_call) and marks the step done."""
    b = get(bid)
    if not b:
        raise ValueError("That buyer is no longer here. Refresh the page.")
    if b.get("product") != "calls" or not b.get("brand"):
        raise ValueError("Automatic test check works for call buyers linked to a brand. Mark leads and clicks tests done by hand once the buyer confirms.")
    import integrations
    r = integrations.place_test_call(b["brand"])
    if r.get("ok"):
        set_step(bid, "test", "done", actor, r.get("detail", ""))
    return r


def stamp(ts):
    try:
        return time.strftime("%d %b %Y", time.strptime(ts[:10], "%Y-%m-%d"))
    except Exception:
        return ts or ""
