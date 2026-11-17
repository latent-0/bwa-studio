"""Compliance gate: scans a generated page for risky claims, tracks which ones counsel cleared, and records legal review.
A brand is legally approved only when every flagged claim is cleared AND a reviewer has signed off on exactly that set of claims.
If the page is regenerated and the claims change, approval goes stale and the brand drops out of the go-live checklist."""
import hashlib
import html
import json
import re

import core
import store

LEGAL_FILE = core.DATA / "legal.json"

RULES = [
    ("Free or no-cost claim", r"\b(free|no cost|at no cost|no charge|no booking fee|no upfront costs?)\b"),
    ("Guarantee or certainty", r"\b(guarantee[sd]?|always|will win|100\s?%|risk[- ]free)\b"),
    ("Superlative", r"\b(best|lowest|cheapest|top[- ]rated|number one)\b"),
    ("Savings or earnings claim", r"\b(save up to|you could save|half what|\$\d[\d,]*)"),
    ("Authority or credential", r"\b(licensed|certified|accredited|approved|endorsed)\b"),
    ("Who pays claim", r"\b(airlines pay us|airlines compensate|compensate[sd]? travel)\b"),
    ("Urgency or pressure", r"\b(act now|don'?t wait|do not wait|limited time|before it'?s too late)\b"),
]


def _load():
    return json.loads(LEGAL_FILE.read_text(encoding="utf-8")) if LEGAL_FILE.exists() else {}


def _save(d):
    LEGAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    LEGAL_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")


def _visible_text(page_html):
    t = re.sub(r"(?is)<(script|style|svg|head)[^>]*>.*?</\1>", " ", page_html)
    t = re.sub(r"(?is)<br\s*/?>|</(p|li|h\d|div|section|article|button|span)>", ". ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return html.unescape(re.sub(r"\s+", " ", t))


def scan(slug):
    f = core.OUT / slug / "index.html"
    if not f.exists():
        return []
    text = _visible_text(f.read_text(encoding="utf-8"))
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    state = _load().get(slug, {})
    cleared = set(state.get("cleared", []))
    seen, hits = set(), []
    for sent in sentences:
        for cat, rx in RULES:
            for m in re.finditer(rx, sent, re.I):
                hid = hashlib.sha1((cat + "|" + sent.lower()).encode()).hexdigest()[:10]
                if hid in seen:
                    continue
                seen.add(hid)
                hits.append({"id": hid, "category": cat, "phrase": m.group(0), "context": sent[:220], "cleared": hid in cleared})
    return hits


def _hash(hits):
    return hashlib.sha1("|".join(sorted(h["id"] for h in hits)).encode()).hexdigest()[:12]


def status(slug):
    hits = scan(slug)
    if not hits and not (core.OUT / slug / "index.html").exists():
        return {"state": "not_generated", "hits": [], "open": 0, "reviewed": None, "approved": False, "label": "Generate the page first"}
    rev = _load().get(slug, {}).get("reviewed")
    open_n = sum(1 for h in hits if not h["cleared"])
    h = _hash(hits)
    if open_n:
        state, label = "claims_open", f"{open_n} claim{'s' if open_n != 1 else ''} to clear"
    elif not rev:
        state, label = "needs_review", "Needs counsel sign-off"
    elif rev.get("claims_hash") != h:
        state, label = "stale", "Claims changed since review"
    elif rev.get("wording_hash") is not None and rev["wording_hash"] != _wording_fp(slug):
        state, label = "stale", "Wording edited since sign-off"
    else:
        state, label = "approved", f"Approved by {rev['by']} on {rev['date']}"
    return {"state": state, "hits": hits, "open": open_n, "reviewed": rev, "approved": state == "approved", "label": label}


def _wording_fp(slug):
    import wording
    return wording.fingerprint(slug)


def is_approved(slug):
    try:
        return status(slug)["approved"]
    except Exception:
        return False


def clear(slug, hit_id, by="counsel", on=True):
    d = _load()
    s = d.setdefault(slug, {})
    c = set(s.get("cleared", []))
    (c.add if on else c.discard)(hit_id)
    s["cleared"] = sorted(c)
    _save(d)
    hit = next((h for h in scan(slug) if h["id"] == hit_id), {})
    store.log_event(slug, "legal.claim_cleared" if on else "legal.claim_reopened",
                    {"id": hit_id, "phrase": hit.get("phrase", ""), "category": hit.get("category", ""), "context": hit.get("context", "")}, by)


def clear_all(slug, by="counsel"):
    d = _load()
    s = d.setdefault(slug, {})
    s["cleared"] = sorted({h["id"] for h in scan(slug)})
    _save(d)
    store.log_event(slug, "legal.claims_cleared_all", {"count": len(s["cleared"])}, by)


def review(slug, reviewer, note=""):
    reviewer = (reviewer or "").strip()
    if not reviewer:
        raise ValueError("Enter the reviewer's name.")
    st = status(slug)
    if st["state"] == "not_generated":
        raise ValueError("Generate the page first.")
    if st["open"]:
        raise ValueError(f"Clear the {st['open']} flagged claim(s) first.")
    d = _load()
    import wording
    d.setdefault(slug, {})["reviewed"] = {"by": reviewer, "date": core.time.strftime("%Y-%m-%d"), "claims_hash": _hash(st["hits"]), "note": note,
                                          "wording_hash": wording.fingerprint(slug)}
    _save(d)
    core.set_brand_field(slug, "legal_reviewed", "yes")
    core.build_compliance(core.get_brand(slug))
    store.log_event(slug, "legal.reviewed", {"note": note[:500], "claims": len(st["hits"]), "edits": wording.total_edits(wording.load(slug))}, reviewer)
    return status(slug)


def revoke(slug, by="studio"):
    d = _load()
    d.setdefault(slug, {}).pop("reviewed", None)
    _save(d)
    core.set_brand_field(slug, "legal_reviewed", "no")
    core.build_compliance(core.get_brand(slug))
    store.log_event(slug, "legal.revoked", "", by)
