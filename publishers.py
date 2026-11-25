"""Publisher status board: every publisher sending traffic, per campaign, with start date and the traffic seen.

Clicks come from Everflow (affiliate x offer x day, so start dates are exact). Calls come from Ringba's insights report (publisher x campaign);
Ringba cannot group by day, so a call publisher's start date is the earliest window it shows up in (today, yesterday, 7, 30 or 90 days),
marked approximate, and the board remembers the exact day for anyone it sees start from then on.
Everflow publishers with no traffic yet are listed too, so new publishers show up the day they are set up.
The result is cached in the meta table and refreshed on demand or when it is more than REFRESH_MIN minutes old."""
import datetime as dt
import json
import time

import store

KEY, FIRST_KEY = "publisher_board", "publisher_first_seen"
REFRESH_MIN = 30


def _get(key, default):
    r = store.q("select value from meta where key=?", (key,))
    try:
        return json.loads(r[0]["value"]) if r else default
    except Exception:
        return default


def _set(key, obj):
    store.x("insert or replace into meta(key,value) values(?,?)", (key, json.dumps(obj)))


def _everflow(today):
    import integrations as I
    if I.mode("everflow") != "live":
        return [], [], "Everflow is not connected."
    code, js = I._http("GET", I.EF + "/affiliates?page=1&page_size=500", I._ef())
    affs = js.get("affiliates", []) if code == 200 and isinstance(js, dict) else []
    body = {"from": (today - dt.timedelta(days=90)).isoformat(), "to": today.isoformat(), "timezone_id": 90, "currency_id": "USD",
            "columns": [{"column": "affiliate"}, {"column": "offer"}, {"column": "date"}], "query": {"filters": []}}
    code, js = I._http("POST", I.EF + "/reporting/entity/table", I._ef(), body)
    if code != 200 or not isinstance(js, dict):
        return [], affs, f"Everflow report: HTTP {code}"
    pairs = {}
    for t in js.get("table", []):
        cols = {c.get("column_type"): c for c in t.get("columns", [])}
        if "affiliate" not in cols or "offer" not in cols or "date" not in cols:
            continue
        day = (dt.datetime.fromtimestamp(int(cols["date"]["id"]), dt.timezone.utc) + dt.timedelta(hours=12)).date()
        r = t.get("reporting", {})
        clicks = int(r.get("total_click", 0) or 0)
        k = (cols["affiliate"]["label"], cols["offer"]["label"])
        p = pairs.setdefault(k, {"source": "clicks", "publisher": k[0], "publisher_id": cols["affiliate"].get("id"), "campaign": k[1],
                                 "buyer": (cols.get("advertiser") or {}).get("label", ""), "days": {}, "conv30": 0, "rej30": 0, "payout30": 0.0, "rev30": 0.0})
        if clicks:
            p["days"][day.isoformat()] = p["days"].get(day.isoformat(), 0) + clicks
        if (today - day).days < 30:
            p["conv30"] += int(r.get("cv", 0) or 0)
            p["rej30"] += int(r.get("invalid_click", 0) or 0) + int(r.get("duplicate_click", 0) or 0)
            p["payout30"] += float(r.get("payout", 0) or 0)
            p["rev30"] += float(r.get("revenue", 0) or 0)
    rows = []
    for p in pairs.values():
        days = p.pop("days")
        seen = sorted(days)
        sm = lambda n: sum(v for d, v in days.items() if (today - dt.date.fromisoformat(d)).days < n)
        p.update({"start": seen[0] if seen else "", "start_exact": True, "last": seen[-1] if seen else "",
                  "today": days.get(today.isoformat(), 0), "yesterday": days.get((today - dt.timedelta(days=1)).isoformat(), 0), "d7": sm(7), "d30": sm(30), "d90": sum(days.values()),
                  "unit": "clicks", "payout30": round(p["payout30"], 2), "rev30": round(p["rev30"], 2)})
        rows.append(p)
    return rows, affs, ""


def _ringba(now):
    import integrations as I
    if I.mode("ringba") != "live":
        return [], "Ringba is not connected."
    base, h = I._rb()
    windows = [("today", 0), ("yesterday", 1), ("d7", 7), ("d30", 30), ("d90", 90)]
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    out = {}

    def fetch(name, n):
        if name == "today":
            start, end = midnight, now
        elif name == "yesterday":
            start, end = midnight - dt.timedelta(days=1), midnight
        else:
            start, end = now - dt.timedelta(days=n), now
        cols = [{"column": "callCount"}] + ([{"column": c} for c in ("convertedCalls", "duplicateCalls", "payoutAmount", "conversionAmount")] if name == "d30" else [])
        body = {"reportStart": start.strftime("%Y-%m-%dT%H:%M:%SZ"), "reportEnd": end.strftime("%Y-%m-%dT%H:%M:%SZ"), "groupByColumns": [{"column": "publisherName"}, {"column": "campaignName"}],
                "valueColumns": cols, "orderByColumns": [{"column": "callCount", "direction": "desc"}], "maxResultsPerGroup": 1000}
        code, js = I._http("POST", base + "/insights", h, body)
        return name, code, js

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda w: fetch(*w), windows))
    for name, code, js in results:
        if code != 200 or not isinstance(js, dict):
            return [], f"Ringba insights: HTTP {code}"
        for r in (js.get("report") or {}).get("records", []):
            k = ((r.get("publisherName") or "No publisher").strip(), (r.get("campaignName") or "").strip())
            p = out.setdefault(k, {"source": "calls", "publisher": k[0], "campaign": k[1], "buyer": "", "unit": "calls",
                                   "today": 0, "yesterday": 0, "d7": 0, "d30": 0, "d90": 0, "conv30": 0, "rej30": 0, "payout30": 0.0, "rev30": 0.0})
            p[name] = int(r.get("callCount", 0) or 0)
            if name == "d30":
                p["conv30"] = int(r.get("convertedCalls", 0) or 0)
                p["rej30"] = int(r.get("duplicateCalls", 0) or 0)
                p["payout30"] = round(float(r.get("payoutAmount", 0) or 0), 2)
                p["rev30"] = round(float(r.get("conversionAmount", 0) or 0), 2)
    today = now.date()
    for p in out.values():
        # earliest window the pair appears in; "last" is the most recent window with calls
        if p["d90"] and not p["d30"]:
            p["start"], p["last"] = (today - dt.timedelta(days=90)).isoformat(), ""
        elif p["d30"] and not p["d7"]:
            p["start"], p["last"] = (today - dt.timedelta(days=30)).isoformat(), ""
        elif p["d7"] and not (p["today"] or p["yesterday"]):
            p["start"], p["last"] = (today - dt.timedelta(days=7)).isoformat(), ""
        else:
            p["start"] = (today - dt.timedelta(days=1)).isoformat() if p["yesterday"] else today.isoformat()
            p["last"] = today.isoformat() if p["today"] else (today - dt.timedelta(days=1)).isoformat()
        p["start_exact"] = False
    return list(out.values()), ""


def status_of(r, today):
    if r.get("pending"):
        return "pending"
    if not r.get("d90"):
        return "not_started"
    if r.get("today") or r.get("yesterday"):
        return "live"
    if r.get("d7"):
        return "this_week"
    return "quiet"


def refresh():
    t0 = time.time()
    now = dt.datetime.now(dt.timezone.utc)
    today = dt.date.today()
    first = _get(FIRST_KEY, {})
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:  # the two systems load side by side
        ef_f, rb_f = pool.submit(_everflow, today), pool.submit(_ringba, now)
        ef_rows, affs, ef_err = ef_f.result()
        rb_rows, rb_err = rb_f.result()
    rows = ef_rows + rb_rows
    # remember the first day the board saw each pair: exact for anyone starting from now on, and it never moves later
    for r in rows:
        k = f"{r['source']}|{r['publisher']}|{r['campaign']}"
        if not r.get("start"):
            continue
        known = first.get(k)
        if not known or (r["start_exact"] and (not known.get("x") or r["start"] < known["d"])):
            first[k] = {"d": r["start"], "x": r["start_exact"]}  # first sighting, or an exact date replacing an estimate
        elif known["d"] < r["start"]:
            r["start"], r["start_exact"] = known["d"], known.get("x", False)  # the board saw it earlier than the current window shows
    # Everflow publishers that exist but have sent nothing in 90 days
    with_traffic = {r["publisher"] for r in ef_rows}  # any campaign row at all, even one with only rejected clicks
    for a in affs:
        name = (a.get("name") or "").strip()
        if not name or name in with_traffic or a.get("account_status") not in ("active", "pending"):
            continue
        created = dt.datetime.fromtimestamp(a.get("time_created", 0), dt.timezone.utc).date().isoformat() if a.get("time_created") else ""
        rows.append({"source": "clicks", "publisher": name, "campaign": "", "buyer": "", "unit": "clicks", "today": 0, "yesterday": 0, "d7": 0, "d30": 0, "d90": 0,
                     "conv30": 0, "rej30": 0, "payout30": 0.0, "rev30": 0.0, "start": "", "start_exact": True, "last": "", "added": created,
                     "pending": a.get("account_status") == "pending"})
    for r in rows:
        r["status"] = status_of(r, today)
    _set(FIRST_KEY, first)
    board = {"refreshed": store.now(), "rows": rows, "errors": [x for x in (ef_err, rb_err) if x], "seconds": round(time.time() - t0, 1)}
    _set(KEY, board)
    return board


def board(max_age_min=REFRESH_MIN):
    b = _get(KEY, None)
    if b:
        try:
            age = (dt.datetime.now() - dt.datetime.strptime(b["refreshed"], "%Y-%m-%d %H:%M:%S")).total_seconds() / 60
        except Exception:
            age = 1e9
        if age <= max_age_min:
            return b
    try:
        return refresh()
    except Exception as ex:
        return b or {"refreshed": "", "rows": [], "errors": [f"Could not load publishers: {str(ex)[:160]}"], "seconds": 0}
