"""The studio's history: every recorded event, described in plain English, filterable and exportable.

Events come from the events table (store.log_event). describe() turns one raw row into a category, a one-line summary, optional details
(before/after wording, notes) and whether it was automatic, so the History page and the CSV export read the same way."""
import csv
import io
import json

import core
import store

CATEGORIES = [
    ("legal", "Legal review", ("legal.",)),
    ("pages", "Pages and publishing", ("page.", "published", "paused", "resumed", "rollback", "publish.")),
    ("board", "Priority board", ("board.",)),
    ("delivery", "Calls, clicks and leads", ("ringba.", "everflow.", "leadprosper.")),
    ("crm", "CRM", ("ghl.",)),
    ("sheet", "Google Sheet", ("tracker",)),
    ("media", "Media and video", ("media.", "video.")),
    ("system", "System", ("refresh.", "sandbox.")),
]
AUTOMATIC = {"ghl.stage", "ghl.sync", "sandbox.traffic", "ringba.pull", "refresh.error", "sandbox.error"}


def category(kind):
    for key, _, prefixes in CATEGORIES:
        if any(kind == p or kind.startswith(p) for p in prefixes):
            return key
    return "system"


def _j(detail):
    if isinstance(detail, (dict, list)):
        return detail
    try:
        v = json.loads(detail or "")
        return v if isinstance(v, (dict, list)) else None
    except Exception:
        return None


def _plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def describe(ev, names=None):
    """{id, ts, slug, brand, kind, category, actor, automatic, tone, summary, note, changes}"""
    k, raw = ev.get("kind") or "", ev.get("detail") or ""
    d = _j(raw)
    actor = ev.get("actor") or "system"
    out = {"id": ev.get("id"), "ts": ev.get("ts"), "slug": ev.get("slug") or "", "brand": (names or {}).get(ev.get("slug") or "", ev.get("slug") or ""),
           "kind": k, "category": category(k), "actor": "system" if actor in ("studio", "") else actor, "tone": "", "note": "", "changes": []}
    out["automatic"] = out["actor"] == "system" or k in AUTOMATIC
    s = None
    if k == "legal.wording_edited":
        if d:
            s = f"Edited {_plural(d.get('count', len(d.get('changes', []))), 'line')} on the {d.get('title', 'page')}"
            out["changes"] = d.get("changes", [])
        else:
            s = f"Edited wording: {raw}"
    elif k == "legal.wording_removed":
        s = f"Removed an edit that no longer matched the {d.get('title', 'page')}" if d else "Removed an unmatched wording edit"
        if d:
            out["note"] = d.get("original", "")
    elif k == "legal.reviewed":
        s, out["tone"] = "Signed off the legal review", "ok"
        if d:
            out["note"] = d.get("note", "")
        elif ":" in raw:
            out["note"] = raw.split(":", 1)[1].strip()
    elif k == "legal.revoked":
        s, out["tone"] = "Revoked the legal sign-off", "warn"
    elif k == "legal.signoff_stale":
        s, out["tone"] = "Legal sign-off needs renewing", "warn"
        out["note"] = (d or {}).get("reason", "")
    elif k in ("legal.claim_cleared", "legal.claim_reopened"):
        verb = "Marked a flagged claim as OK as written" if k.endswith("cleared") else "Reopened a flagged claim"
        if d and d.get("phrase"):
            s = f'{verb}: "{d["phrase"]}"'
            out["note"] = (d.get("category", "") + (": " + d["context"] if d.get("context") else "")).strip(": ")
        else:
            s = verb
    elif k == "legal.claims_cleared_all":
        n = (d or {}).get("count", raw)
        s = f"Cleared all flagged claims ({n})"
    elif k == "page.generated":
        s = "Generated the landing page and legal pages"
        out["note"] = f"Source: {raw}" if raw else ""
    elif k == "published":
        s, out["tone"] = "Published the site", "ok"
        out["note"] = raw
    elif k == "paused":
        s, out["tone"] = "Paused the live site", "warn"
    elif k == "resumed":
        s = "Resumed the live site"
    elif k == "rollback":
        s, out["tone"] = "Rolled back the live site", "warn"
        out["note"] = f"Back to {raw}" if raw else ""
    elif k == "publish.hook":
        s, out["note"] = "Ran the deploy hook", raw
    elif k.startswith("board."):
        d = d or {}
        by = {"checks": " (its checks moved it)", "sheet": " (changed in the Sheet)"}.get(d.get("mode"), "")
        if k == "board.stage":
            s = f'Moved from {d.get("from", "?")} to {d.get("to", "?")}{by}'
        elif k == "board.rank":
            s = f'Priority changed from #{d.get("from", "?")} to #{d.get("to", "?")}{by}'
        else:
            s = f"Board change: {raw}"
        if d.get("mode") in ("checks", "sheet"):
            out["automatic"] = True
    elif k == "ringba.number_assigned":
        s, out["note"] = "Assigned a tracking number", raw
    elif k == "ringba.test_call":
        s, out["note"] = "Recorded a test call", raw
    elif k == "ringba.pull":
        s = f"Pulled calls from Ringba: {raw}"
    elif k in ("leadprosper.test_lead", "leadprosper.lead"):
        s, out["note"] = ("Sent a test lead" if k.endswith("test_lead") else "Sent a lead"), raw
    elif k == "ghl.stage":
        s = f"CRM updated: {raw}"
    elif k == "ghl.sync":
        s = f"CRM sync: {raw}"
    elif k == "tracker":
        s = "Updated the campaign tracker"
        out["note"] = raw
    elif k == "media.used":
        s = raw or "Changed the brand video"
    elif k == "video.rendered":
        s, out["note"] = "Rendered a video", raw
    elif k == "video.failed":
        s, out["tone"], out["note"] = "A video render failed", "bad", raw
    elif k == "sandbox.traffic":
        s = f"Simulated test traffic: {raw}"
    elif k.endswith(".error"):
        system = {"ringba": "Ringba", "everflow": "Everflow", "leadprosper": "LeadProsper", "ghl": "GoHighLevel", "refresh": "Data refresh", "sandbox": "Sandbox"}.get(k.split(".")[0], k)
        s, out["tone"], out["note"] = f"{system} reported an error", "bad", raw
    out["summary"] = s or (k.replace(".", " ").replace("_", " ").capitalize() + (f": {raw}" if raw and not d else ""))
    return out


def _where(f):
    sql, args = [], []
    if f.get("slug"):
        sql.append("slug = ?")
        args.append(f["slug"])
    if f.get("actor"):
        sql.append("actor = ?")
        args.append(f["actor"])
    if f.get("cat"):
        prefixes = next((p for key, _, p in CATEGORIES if key == f["cat"]), ())
        if prefixes:
            sql.append("(" + " or ".join("kind like ?" for _ in prefixes) + ")")
            args += [p + "%" for p in prefixes]
    if f.get("since"):
        sql.append("ts >= ?")
        args.append(f["since"])
    if f.get("before"):
        sql.append("id < ?")
        args.append(int(f["before"]))
    if f.get("q"):
        sql.append("(lower(detail) like ? or lower(kind) like ? or lower(actor) like ? or lower(slug) like ?)")
        args += ["%" + f["q"].lower() + "%"] * 4
    return (" where " + " and ".join(sql)) if sql else "", args


def query(f, limit=80):
    """Filtered, described events, newest first. f: slug, actor, cat, since, before, q, auto ('1' to include automatic)."""
    names = {b["slug"]: b["name"] for b in core.load_brands()}
    where, args = _where(f)
    include_auto = f.get("auto") == "1"
    out, before, scanned = [], None, 0
    # automatic rows are filtered after describing, so read in pages until there are enough
    while len(out) < limit and scanned < 3000:
        w, a = where, list(args)
        if before is not None:
            w = (w + " and " if w else " where ") + "id < ?"
            a.append(before)
        rows = store.q(f"select * from events{w} order by id desc limit ?", tuple(a) + (200,))
        if not rows:
            break
        scanned += len(rows)
        before = rows[-1]["id"]
        for r in rows:
            ev = describe(r, names)
            if include_auto or not ev["automatic"]:
                out.append(ev)
                if len(out) >= limit:
                    break
    return {"events": out, "more": bool(out) and len(out) >= limit, "next": out[-1]["id"] if out else None, "now": store.now()}


def facets():
    names = {b["slug"]: b["name"] for b in core.load_brands()}
    people = sorted({r["actor"] for r in store.q("select distinct actor from events") if r["actor"] and r["actor"] not in ("studio", "system")})
    return {"brands": sorted(([s, n] for s, n in names.items()), key=lambda x: x[1].lower()), "people": people,
            "categories": [[k, label] for k, label, _ in CATEGORIES]}


def to_csv(f):
    data = query(f, limit=5000)["events"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Time (UTC)", "Brand", "Category", "Who", "What happened", "Details", "Changes (before -> after)"])
    labels = {k: label for k, label, _ in CATEGORIES}
    for e in data:
        ch = " | ".join(f'{c.get("from", "")} -> {c.get("to", "")}' for c in e["changes"])
        w.writerow([e["ts"], e["brand"], labels.get(e["category"], e["category"]), e["actor"], e["summary"], e["note"], ch])
    return buf.getvalue()
