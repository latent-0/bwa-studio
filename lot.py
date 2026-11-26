"""Daily report data (action items 35 and 36).

The lot: every brand on the priority board and every partner in onboarding, the stage of prep each one is in, and what moved since the last
working day. Affiliate campaigns: every publisher, whether they are signed and live, their traffic and calls, and revenue, payout and profit.

Each time the report is built (page view, the daily cron) it saves a snapshot for today (US Eastern), keeping the latest one per day. Movement is
today compared with the most recent earlier snapshot. When there is no earlier snapshot yet, yesterday's stages are rebuilt from the board history
and the partners' step dates, so the first report already shows movement."""
import datetime as dt
import json

import store

KEY = "lot_snapshots"
KEEP_DAYS = 60
ET = dt.timezone(dt.timedelta(hours=-5))
BRAND_STAGES = ["Draft", "Generated", "Legal review", "Ready to test", "Ready to launch", "Live", "Paused"]


def _get(key, default):
    r = store.q("select value from meta where key=?", (key,))
    try:
        return json.loads(r[0]["value"]) if r else default
    except Exception:
        return default


def _set(key, obj):
    store.x("insert or replace into meta(key,value) values(?,?)", (key, json.dumps(obj)))


def today():
    return dt.datetime.now(ET).date()


def _working_day_before(d):
    d -= dt.timedelta(days=1)
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return d


def _brands():
    import board
    p = board.payload()
    out = {}
    for c in p["cards"]:
        out["b:" + c["slug"]] = {"group": "Brand", "name": c["name"], "sub": c["vertical"], "stage": c["stage"],
                                 "idx": BRAND_STAGES.index(c["stage"]) if c["stage"] in BRAND_STAGES else 0, "of": len(BRAND_STAGES) - 2,
                                 "passed": c["passed"], "checks": len(c["checks"]), "next": c["next"], "priority": c["priority"], "slug": c["slug"]}
    return out


def _partners():
    import buyers
    out = {}
    for b in buyers.all_buyers():
        sg = buyers.stages(b)
        i = next((n for n, s in enumerate(sg) if s["state"] == "current"), len(sg) - 1)
        live = all(s["state"] == "done" for s in sg)
        p = buyers.progress(b)
        out["p:" + b["id"]] = {"group": buyers.KINDS[buyers.kind_of(b)], "name": b.get("company") or "Partner", "sub": b.get("vertical") or "",
                               "stage": "Live & earning" if live else sg[i]["label"], "idx": len(sg) if live else i, "of": len(sg),
                               "passed": p["done"], "checks": p["total"], "next": "" if live else p["next"],
                               "days": None if live else sg[i]["days"], "id": b["id"]}
    return out


def _affiliates():
    """One row per publisher: signed (set up in Everflow or Ringba), live (traffic today or yesterday), traffic, calls and money for 30 days."""
    import publishers
    b = publishers.board()
    out = {}
    for r in b.get("rows", []):
        a = out.setdefault(r["publisher"], {"publisher": r["publisher"], "campaigns": [], "live": False, "this_week": False, "pending": False,
                                            "clicks_y": 0, "clicks_t": 0, "clicks30": 0, "calls_y": 0, "calls_t": 0, "calls30": 0, "conv30": 0,
                                            "rev30": 0.0, "payout30": 0.0, "start": ""})
        if r.get("campaign"):
            a["campaigns"].append({"name": r["campaign"], "buyer": r.get("buyer", ""), "status": r["status"], "unit": r.get("unit", r["source"]),
                                   "yesterday": r.get("yesterday", 0), "d30": r.get("d30", 0), "rev30": r.get("rev30", 0.0), "payout30": r.get("payout30", 0.0)})
        unit = "calls" if r["source"] == "calls" else "clicks"
        a[unit + "_y"] += r.get("yesterday", 0)
        a[unit + "_t"] += r.get("today", 0)
        a[unit + "30"] += r.get("d30", 0)
        a["conv30"] += r.get("conv30", 0)
        a["rev30"] = round(a["rev30"] + (r.get("rev30") or 0), 2)
        a["payout30"] = round(a["payout30"] + (r.get("payout30") or 0), 2)
        a["live"] = a["live"] or r["status"] == "live"
        a["this_week"] = a["this_week"] or r["status"] in ("live", "this_week")
        a["pending"] = a["pending"] or r["status"] == "pending"
        if r.get("start") and (not a["start"] or r["start"] < a["start"]):
            a["start"] = r["start"]
    for a in out.values():
        a["profit30"] = round(a["rev30"] - a["payout30"], 2)
        a["status"] = "live" if a["live"] else "this_week" if a["this_week"] else "pending" if a["pending"] else "signed"
    return sorted(out.values(), key=lambda a: ({"live": 0, "this_week": 1, "signed": 2, "pending": 3}[a["status"]], -a["rev30"], -a["calls30"] - a["clicks30"], a["publisher"].lower())), b


def _rebuild_yesterday(items, cutoff):
    """Best estimate of each item's stage at the end of the given day, from the board history and partner step dates."""
    import board
    import buyers
    prev = {}
    hist = board.history(limit=600)  # newest first
    for k, it in items.items():
        if k.startswith("b:"):
            later = [h for h in hist if h["slug"] == it["slug"] and h["type"] == "stage" and h["ts"][:10] > cutoff]
            if later and later[-1].get("from"):
                st = later[-1]["from"]
                prev[k] = dict(it, stage=st, idx=BRAND_STAGES.index(st) if st in BRAND_STAGES else 0, passed=None)
            else:
                prev[k] = dict(it, passed=None)
        else:
            b = buyers.get(it["id"])
            if not b or (b.get("created", "")[:10] > cutoff):
                continue  # added after that day: shows as new
            sg = buyers.stages(b)
            i = next((n for n, s in enumerate(sg) if not (s["state"] == "done" and s["done_at"][:10] <= cutoff)), len(sg))
            prev[k] = dict(it, stage="Live & earning" if i >= len(sg) else sg[i]["label"], idx=i, passed=None)
    return prev


def build(save=True):
    d = today()
    items = {}
    errors = []
    try:
        items.update(_brands())
    except Exception as ex:
        errors.append(f"Brands could not load: {str(ex)[:140]}")
    try:
        items.update(_partners())
    except Exception as ex:
        errors.append(f"Partners could not load: {str(ex)[:140]}")
    try:
        affs, pb = _affiliates()
        errors += pb.get("errors", [])
    except Exception as ex:
        affs, pb = [], {}
        errors.append(f"Publishers could not load: {str(ex)[:140]}")
    snaps = _get(KEY, {})
    earlier = sorted(k for k in snaps if k < d.isoformat())
    if earlier:
        base_day = earlier[-1]
        prev, prev_aff, rebuilt = snaps[base_day]["items"], snaps[base_day].get("aff", {}), False
    else:
        base_day = _working_day_before(d).isoformat()
        prev, prev_aff, rebuilt = _rebuild_yesterday(items, base_day), {}, True
    moves = []
    for k, it in items.items():
        p = prev.get(k)
        if not p:
            moves.append({"kind": "new", "key": k, "item": it, "text": f"New on the lot, in {it['stage']}"})
        elif it["idx"] > p["idx"]:
            moves.append({"kind": "up", "key": k, "item": it, "text": f"{p['stage']} to {it['stage']}"})
        elif it["idx"] < p["idx"]:
            moves.append({"kind": "down", "key": k, "item": it, "text": f"Back from {p['stage']} to {it['stage']}"})
        elif p.get("passed") is not None and it["passed"] != p["passed"]:
            moves.append({"kind": "up" if it["passed"] > p["passed"] else "down", "key": k, "item": it,
                          "text": f"Still {it['stage']}, {it['passed']} of {it['checks']} {'checks' if k.startswith('b:') else 'steps'} done (was {p['passed']})"})
    for k, p in prev.items():
        if k not in items:
            moves.append({"kind": "gone", "key": k, "item": p, "text": f"Off the lot (was {p['stage']})"})
    order = {"up": 0, "new": 1, "down": 2, "gone": 3}
    moves.sort(key=lambda m: (order[m["kind"]], m["item"]["group"], m["item"]["name"].lower()))
    aff_moves = []
    for a in affs:
        was = prev_aff.get(a["publisher"])
        if was is None and prev_aff:
            aff_moves.append(f"{a['publisher']}: new publisher ({a['status'].replace('_', ' ')})")
        elif was and was != a["status"]:
            aff_moves.append(f"{a['publisher']}: {was.replace('_', ' ')} to {a['status'].replace('_', ' ')}")
    rep = {"day": d.isoformat(), "since": base_day, "rebuilt": rebuilt, "items": items, "moves": moves, "aff": affs, "aff_moves": aff_moves,
           "errors": errors, "refreshed": pb.get("refreshed", ""), "made": store.now()}
    if save and items:
        snaps[d.isoformat()] = {"t": store.now(), "items": items, "aff": {a["publisher"]: a["status"] for a in affs}}
        keep = sorted(snaps)[-KEEP_DAYS:]
        _set(KEY, {k: snaps[k] for k in keep})
    return rep


def _day(iso):
    try:
        return dt.date.fromisoformat(iso).strftime("%a %d %b")
    except Exception:
        return iso


def _money(v):
    return ("-" if v < 0 else "") + f"${abs(v):,.0f}"


def summary(rep):
    items = list(rep["items"].values())
    brands = [i for i in items if i["group"] == "Brand"]
    partners = [i for i in items if i["group"] != "Brand"]
    by = {s: sum(1 for b in brands if b["stage"] == s) for s in BRAND_STAGES}
    affs = rep["aff"]
    signed = len(affs)
    live = sum(1 for a in affs if a["status"] == "live")
    return {"brands": len(brands), "partners": len(partners), "by_stage": by, "moves": len(rep["moves"]),
            "forward": sum(1 for m in rep["moves"] if m["kind"] in ("up", "new")), "signed": signed, "live": live,
            "calls30": sum(a["calls30"] for a in affs), "calls_y": sum(a["calls_y"] for a in affs), "clicks_y": sum(a["clicks_y"] for a in affs),
            "rev30": round(sum(a["rev30"] for a in affs), 2), "payout30": round(sum(a["payout30"] for a in affs), 2),
            "profit30": round(sum(a["profit30"] for a in affs), 2)}


def as_text(rep):
    """Plain text for posting the report in Basecamp or chat."""
    s = summary(rep)
    lines = [f"DAILY REPORT, {_day(rep['day'])}", "", "1. THE LOT",
             f"On the lot: {s['brands']} brands and {s['partners']} partners in onboarding.",
             "Brands by stage: " + ", ".join(f"{k} {v}" for k, v in s["by_stage"].items() if v) + ".",
             f"Movement since {_day(rep['since'])}{' (rebuilt from the board history)' if rep['rebuilt'] else ''}:"]
    if rep["moves"]:
        for m in rep["moves"]:
            sign = {"up": "+", "new": "+", "down": "-", "gone": "-"}[m["kind"]]
            lines.append(f"  {sign} {m['item']['name']} ({m['item']['group']}): {m['text']}")
    else:
        lines.append("  No stage changes.")
    lines.append("Stage of prep, by priority:")
    for it in sorted(rep["items"].values(), key=lambda i: (i["group"] != "Brand", i.get("priority", 99), i["name"].lower())):
        nxt = f". Next: {it['next']}" if it.get("next") else ""
        unit = "checks" if it["group"] == "Brand" else "steps"
        lines.append(f"  {it['name']} ({it['group']}): {it['stage']}, {it['passed']}/{it['checks']} {unit}{nxt}")
    lines += ["", "2. AFFILIATE CAMPAIGNS",
              f"Signed publishers: {s['signed']}. Live today or yesterday: {s['live']}.",
              f"Yesterday: {s['calls_y']:,} calls, {s['clicks_y']:,} clicks.",
              f"Last 30 days: {s['calls30']:,} calls, revenue {_money(s['rev30'])}, publisher payout {_money(s['payout30'])}, profit {_money(s['profit30'])}."]
    for a in rep["aff"]:
        if a["status"] in ("live", "this_week") or a["rev30"]:
            lines.append(f"  {a['publisher']} ({a['status'].replace('_', ' ')}): yesterday {a['calls_y']} calls / {a['clicks_y']:,} clicks; "
                         f"30d {a['calls30']:,} calls, revenue {_money(a['rev30'])}, profit {_money(a['profit30'])}")
    waiting = [a["publisher"] for a in rep["aff"] if a["status"] in ("signed", "pending")]
    if waiting:
        lines.append("  Signed, no traffic in the last 7 days: " + ", ".join(waiting))
    if rep["aff_moves"]:
        lines.append("Changes since the last report: " + "; ".join(rep["aff_moves"]))
    return "\n".join(lines)
