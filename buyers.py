"""Partner onboarding for buyers and publishers: Blue Wing's onboarding SOP (Sydney, Sep 2026) as a tracked checklist per partner, shown to the
partner as a six-stage roadmap on a private link, with a branded welcome email, a named partner-success contact and booking link, a named
technical contact, one shared onboarding thread and a branded signature.

Records live in the meta table (key "buyers"), so they persist on Vercel through the database like the rest of the studio.
Card details never touch the studio: the deposit step links to a hosted payment page (for example a Stripe Payment Link)."""
import json
import re
import secrets
import time

import store

KINDS = {"buyer": "Buyer", "publisher": "Publisher"}

# (key, label, what it means) per partner type. Buyer steps follow the SOP; publisher steps follow the same shape for traffic partners.
STEPS_BY_KIND = {
    "buyer": [
        ("campaign", "Campaign identified", "One specific campaign picked out of everything discussed (SOP 1)."),
        ("email", "Welcome email sent", "Branded welcome email with the roadmap and next steps; names whose paperwork is used (SOP 2)."),
        ("verify", "Campaign details verified", "Payout, hours, caps, geos and qualification rules confirmed (SOP 6)."),
        ("creatives", "Creatives approved", "Landing page, scripts and ads the buyer must approve (SOP 7)."),
        ("msa", "MSA signed", "MSA sent or requested, redlines handled, signed by both sides (SOP 3 to 5)."),
        ("io", "IO signed", "Insertion order sent by e-sign and signed (SOP 8 and 9)."),
        ("deposit", "First-lead deposit received", "Card added on the payment page for the first-lead deposit."),
        ("tech", "Tech details received", "Destination number or lead endpoint received from the partner's onboarding page."),
        ("test", "First test passed", "A test call or test lead reached the buyer and they confirmed it."),
        ("handoff", "Live: Ops handoff", "Ready-to-test signal sent to Ops; Ops confirms the campaign is live (SOP 10)."),
        ("folder", "Folder updated", "Signed paperwork and approved creatives filed (SOP 11)."),
    ],
    "publisher": [
        ("campaign", "Offer picked", "One specific offer agreed for this publisher to run."),
        ("email", "Welcome email sent", "Branded welcome email with the roadmap and next steps."),
        ("kit", "Offer kit sent", "Approved creatives, payout, allowed traffic sources and compliance rules sent."),
        ("links", "Tracking link issued", "The publisher's own Everflow tracking link created and shared."),
        ("agreement", "Publisher agreement signed", "Publisher agreement or IO signed."),
        ("tax", "W-9 received", "Tax form received for payouts."),
        ("payment", "Payment details set", "How and when the publisher gets paid is set up."),
        ("tech", "Postback and details received", "Traffic sources, sub ID and postback details received from the onboarding page."),
        ("test", "Test conversion passed", "A test click and conversion tracked end to end and confirmed."),
        ("live", "Live: traffic flowing", "First real traffic seen on the publisher board."),
        ("folder", "Folder updated", "Signed paperwork and offer kit filed."),
    ],
}
# the six roadmap stages the partner sees, and which steps finish each one
STAGES = [
    ("match", "We're a match", "We picked the right campaign together and sent your welcome kit.", {"buyer": ("campaign", "email"), "publisher": ("campaign", "email")}),
    ("kit", "Your playbook", "Everything about the campaign in one place: payout, rules, creatives.", {"buyer": ("verify", "creatives"), "publisher": ("kit", "links")}),
    ("paper", "Sign & sorted", "The paperwork, done online in a few minutes.", {"buyer": ("msa", "io", "deposit"), "publisher": ("agreement", "tax", "payment")}),
    ("tech", "Tech handshake", "Our tech meets your tech, so every call, lead or click lands where it should.", {"buyer": ("tech",), "publisher": ("tech",)}),
    ("test", "First test run", "We send a test, you confirm it arrived. No surprises on launch day.", {"buyer": ("test",), "publisher": ("test",)}),
    ("live", "Live & earning", "Your campaign is open for business.", {"buyer": ("handoff",), "publisher": ("live",)}),
]
STATES = ("todo", "sent", "done")
READY = {"buyer": ("msa", "io", "deposit", "tech", "test"), "publisher": ("agreement", "tax", "tech", "test")}
PRODUCTS = {"calls": "Calls", "leads": "Leads", "clicks": "Clicks"}
FIELDS = ("kind", "company", "contact_name", "contact_email", "vertical", "brand", "product", "payout", "io_number", "msa_url", "io_url", "deposit_url",
          "deposit_amount", "agreement_url", "w9_url", "payment_url", "tracking_link", "notes", "archived")
LINK_FIELDS = ("msa_url", "io_url", "deposit_url", "agreement_url", "w9_url", "payment_url", "tracking_link")
TECH = {  # what the partner sends back from the onboarding page
    "calls": [("destination", "Number to send calls to (or SIP address)"), ("hours", "Hours you take calls, with time zone"), ("concurrency", "Most calls at once"),
              ("daily_cap", "Daily call cap"), ("billable", "Billable call length in seconds"), ("geos", "States you accept"), ("contact", "Who to call about routing problems")],
    "leads": [("endpoint", "Lead endpoint URL"), ("auth", "How to authenticate (API key header, basic auth, none)"), ("required", "Fields you require beyond ours"),
              ("response", "What your success and rejection responses look like"), ("daily_cap", "Daily lead cap"), ("geos", "States you accept"), ("contact", "Technical contact")],
    "clicks": [("tracking_url", "Your tracking link, with where the click ID goes"), ("postback", "Will you fire our postback, or should we fire yours?"),
               ("daily_cap", "Daily click cap"), ("geos", "Geos you accept"), ("contact", "Technical contact")],
    "publisher": [("sources", "Where your traffic comes from (sites, apps, networks)"), ("sub_id", "The parameter you pass your sub ID in"),
                  ("postback", "Your postback URL, if you want conversions fired back to you"), ("daily_cap", "Daily volume you expect"),
                  ("geos", "Geos you will send"), ("contact", "Technical contact")],
}
SETTINGS = ("company", "website", "success_name", "success_title", "success_email", "booking_url", "tech_name", "tech_title", "tech_email", "thread_email",
            "msa_url", "io_url", "deposit_url", "agreement_url", "w9_url", "payment_url", "support_email")
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
    out = {k: s.get(k, "") for k in SETTINGS}
    out["company"] = out["company"] or "Blue Wing Ads"
    out["thread_email"] = out["thread_email"] or out["support_email"]
    return out


def save_settings(d, actor):
    s = settings()
    for k in SETTINGS:
        if k in d:
            if k.endswith("_url") or k == "website":
                s[k] = _clean_url(d[k])
            elif k.endswith("_email"):
                s[k] = _clean_email(d[k])
            else:
                s[k] = _clean(d[k], 120)
    _set(SETTINGS_KEY, s)
    store.log_event("buyers", "buyer.settings", "Partner onboarding team, links and thread updated", actor)
    return s


def _clean(v, n=300):
    return re.sub(r"[\x00-\x1f\x7f]", " ", str(v or "")).strip()[:n]


def _clean_url(v):
    v = _clean(v, 500)
    if v and not re.match(r"^https://\S+$", v):
        raise ValueError("Links must start with https://")
    return v


def _clean_email(v):
    v = _clean(v, 160)
    if v and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
        raise ValueError(f"{v} does not look like an email address.")
    return v


def kind_of(b):
    return b.get("kind") if b.get("kind") in KINDS else "buyer"


def steps_for(b):
    return STEPS_BY_KIND[kind_of(b)]


def all_buyers(include_archived=False):
    d = _get(KEY, {})
    rows = [b for b in d.values() if include_archived or not b.get("archived")]
    return sorted(rows, key=lambda b: b.get("updated", ""), reverse=True)


def get(bid):
    return _get(KEY, {}).get(bid)


def deal_name(b):
    """SOP naming: [Business Name] - [Vertical] IO #[IO Number]"""
    name = b.get("company") or "New partner"
    if b.get("vertical"):
        name += f" - {b['vertical']}"
    if b.get("io_number"):
        name += f" IO #{b['io_number']}"
    return name


def links(b):
    """The partner's own link if set, otherwise the team default from settings."""
    s = settings()
    return {k: b.get(k) or s.get(k, "") for k in LINK_FIELDS}


def stages(b):
    """The six roadmap stages with done / current / upcoming, for the partner page, the email and the team screen."""
    st = b.get("steps", {})
    k = kind_of(b)
    out, current_found = [], False
    entered = b.get("created", "")  # a milestone's clock starts when the previous one was reached
    for key, label, blurb, by_kind in STAGES:
        keys = by_kind[k]
        done = all(st.get(x, {}).get("state") == "done" for x in keys)
        started = any(st.get(x, {}).get("state") in ("sent", "done") for x in keys)
        state = "done" if done else ("current" if not current_found else "upcoming")
        if not done and not current_found:
            current_found = True
        done_at = max((st[x].get("ts", "") for x in keys if x in st), default="") if done else ""
        out.append({"key": key, "label": label, "blurb": blurb, "state": state, "started": started, "steps": keys,
                    "entered_at": entered if state in ("done", "current") else "", "done_at": done_at,
                    "days": _days(entered, done_at) if done else (_days(entered, "") if state == "current" else None)})
        if done:
            entered = max(entered, done_at)
    return out


def _days(start, end):
    """Whole days between two 'YYYY-MM-DD HH:MM:SS' stamps (end blank = now)."""
    try:
        a = time.mktime(time.strptime(start[:19], "%Y-%m-%d %H:%M:%S"))
        z = time.mktime(time.strptime(end[:19], "%Y-%m-%d %H:%M:%S")) if end else time.time()
        return max(0, int((z - a) // 86400))
    except Exception:
        return None


STUCK_DAYS = 7  # a partner sitting in one milestone longer than this is flagged on the board


def complete_stage(bid, stage_key, actor):
    """Tick every step of one milestone at once."""
    b = get(bid)
    if not b:
        raise ValueError("That partner is no longer here. Refresh the page.")
    by_kind = next((x[3] for x in STAGES if x[0] == stage_key), None)
    if not by_kind:
        raise ValueError("Unknown milestone.")
    for k in by_kind[kind_of(b)]:
        if b.get("steps", {}).get(k, {}).get("state") != "done":
            b = set_step(bid, k, "done", actor, "milestone ticked")
    return b


def progress(b):
    st = b.get("steps", {})
    keys = [k for k, _, _ in steps_for(b)]
    done = sum(1 for k in keys if st.get(k, {}).get("state") == "done")
    ready = all(st.get(k, {}).get("state") == "done" for k in READY[kind_of(b)])
    sg = stages(b)
    stage_no = next((i + 1 for i, s in enumerate(sg) if s["state"] == "current"), len(sg))
    return {"done": done, "total": len(keys), "ready": ready, "next": next((lab for k, lab, _ in steps_for(b) if st.get(k, {}).get("state") != "done"), ""),
            "stage": stage_no, "stages_done": sum(1 for s in sg if s["state"] == "done"), "stage_label": sg[stage_no - 1]["label"]}


def save(d, actor):
    db = _get(KEY, {})
    bid = d.get("id") or ""
    b = db.get(bid) if bid else None
    if not b:
        if not _clean(d.get("company")):
            raise ValueError("Add the partner's company name.")
        bid = secrets.token_urlsafe(16)  # also the private part of the partner's onboarding link
        b = {"id": bid, "created": store.now(), "steps": {}, "tech": {}}
    for f in FIELDS:
        if f not in d:
            continue
        if f in LINK_FIELDS:
            b[f] = _clean_url(d[f])
        elif f == "contact_email":
            b[f] = _clean_email(d[f])
        elif f == "product":
            b[f] = d[f] if d[f] in PRODUCTS else "calls"
        elif f == "kind":
            b[f] = d[f] if d[f] in KINDS else "buyer"
        elif f == "archived":
            b[f] = bool(d[f])
        else:
            b[f] = _clean(d[f], 2000 if f == "notes" else 160)
    b.setdefault("product", "calls")
    b.setdefault("kind", "buyer")
    b["updated"] = store.now()
    new = bid not in db
    db[bid] = b
    _set(KEY, db)
    store.log_event(b.get("brand") or "buyers", "buyer.added" if new else "buyer.updated", f"{KINDS[kind_of(b)]}: {deal_name(b)}", actor)
    return b


def set_step(bid, key, state, actor, note=""):
    db = _get(KEY, {})
    b = db.get(bid)
    if not b:
        raise ValueError("That partner is no longer here. Refresh the page.")
    labels = {k: lab for k, lab, _ in steps_for(b)}
    if key not in labels or state not in STATES:
        raise ValueError("Unknown step or state.")
    was_ready, was_stages = progress(b)["ready"], progress(b)["stages_done"]
    b.setdefault("steps", {})[key] = {"state": state, "ts": store.now(), "by": actor, "note": _clean(note, 200)}
    b["updated"] = store.now()
    db[bid] = b
    _set(KEY, db)
    store.log_event(b.get("brand") or "buyers", "buyer.step", f"{deal_name(b)}: {labels[key]} = {state}", actor)
    p = progress(b)
    if p["stages_done"] > was_stages:
        store.log_event(b.get("brand") or "buyers", "buyer.stage", f"{deal_name(b)} reached stage {p['stages_done']} of 6", actor)
    if p["ready"] and not was_ready:
        store.log_event(b.get("brand") or "buyers", "buyer.ready_for_ops", f"{deal_name(b)} is ready for Ops: paperwork, tech details and test are done", actor)
    return b


def submit_tech(bid, d):
    """Called from the partner's own onboarding page (no sign-in: the unguessable link is the key)."""
    db = _get(KEY, {})
    b = db.get(bid)
    if not b or b.get("archived"):
        raise ValueError("This onboarding link is no longer active.")
    fields = tech_fields(b)
    tech = {k: _clean(d.get(k), 500) for k, _ in fields if _clean(d.get(k), 500)}
    if not tech:
        raise ValueError("Fill in at least one field.")
    tech["submitted"] = store.now()
    b["tech"] = tech
    st = b.setdefault("steps", {})
    if st.get("tech", {}).get("state") != "done":
        st["tech"] = {"state": "sent", "ts": store.now(), "by": "partner", "note": "Submitted from the onboarding page; check and mark done"}
    b["updated"] = store.now()
    db[bid] = b
    _set(KEY, db)
    store.log_event(b.get("brand") or "buyers", "buyer.tech_submitted", f"{deal_name(b)} sent their technical details", "partner")
    return b


def tech_fields(b):
    return TECH["publisher"] if kind_of(b) == "publisher" else TECH.get(b.get("product", "calls"), [])


def run_test(bid, actor):
    """Call buyers: finds the test call placed to the brand's Ringba campaign in the last hour and marks the step done."""
    b = get(bid)
    if not b:
        raise ValueError("That partner is no longer here. Refresh the page.")
    if kind_of(b) != "buyer" or b.get("product") != "calls" or not b.get("brand"):
        raise ValueError("Automatic test check works for call buyers linked to a brand. Mark other tests done by hand once the partner confirms.")
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
