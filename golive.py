"""Publisher go-live board: every signed publisher on one of our offers, walked down the assembly line from signed to live.

Traffic comes in, a call comes out, we get paid, the publisher gets paid. For each publisher and offer the board checks, from the live systems:
  1 Signed      the publisher is active in Everflow and has the offer
  2 Page        the offer's landing page carries the brand's Ringba number-insertion tag, so a caller from that click is tracked
  3 Postback    the Ringba campaign sends converted calls back to Everflow with the click's transaction ID
  4 Test click  Everflow has seen a click from this publisher on this offer
  5 Test call   Everflow has a conversion (a paid call) from this publisher on this offer
  6 Live        traffic today or yesterday and at least one conversion in 30 days
The first step that fails is the blocker, with the action that clears it. Cached in the meta table for CACHE_MIN minutes."""
import json
import re
import time
import urllib.request

import store

KEY = "golive_board"
CACHE_MIN = 30
STEPS = [("signed", "Signed"), ("page", "Page tracks calls"), ("postback", "Postback to Everflow"), ("click", "Test click"),
         ("call", "Test call paid"), ("live", "Live")]


def _get(key, default):
    r = store.q("select value from meta where key=?", (key,))
    try:
        return json.loads(r[0]["value"]) if r else default
    except Exception:
        return default


def _set(key, obj):
    store.x("insert or replace into meta(key,value) values(?,?)", (key, json.dumps(obj)))


def _offers():
    import integrations as I
    code, js = I._http("GET", I.EF + "/offers?page=1&page_size=500", I._ef())
    return {(o.get("name") or "").strip(): {"id": str(o["network_offer_id"]), "url": o.get("destination_url") or ""}
            for o in (js.get("offers", []) if isinstance(js, dict) else [])}


def _brand_for_offer():
    import core
    out = {}
    for b in core.load_brands():
        for oid in (b.get("everflow_offer") or "").split(","):
            if oid.strip():
                out[oid.strip()] = {"slug": b["slug"], "name": b["name"], "ringba": [c.strip() for c in (b.get("ringba_campaign") or "").split(",") if c.strip()]}
    return out


def _page_check(url, campaigns, cache):
    """Does the landing page carry one of the brand's Ringba insertion tags?"""
    page = re.sub(r"\?.*", "", url)
    if page not in cache:
        try:
            t = urllib.request.urlopen(urllib.request.Request(page, headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read().decode("utf-8", "replace")
            cache[page] = re.findall(r"b-js\.ringba\.com/(CA[0-9a-fA-F]+)", t)
        except Exception as ex:
            cache[page] = "error: " + str(ex)[:80]
    tags = cache[page]
    if isinstance(tags, str):
        return False, f"Could not open {page} ({tags})"
    hit = [c for c in tags if c in campaigns] if campaigns else tags
    if hit:
        return True, f"{page} has the Ringba tag"
    if tags:
        return False, f"{page} has a Ringba tag for another campaign"
    return False, f"{page} shows a fixed number with no Ringba tag, so calls from this traffic cannot be credited"


def _postback_check(campaigns, cache):
    import integrations as I
    base, h = I._rb()
    for c in campaigns:
        if c not in cache:
            code, js = I._http("GET", base + "/campaigns/" + c, h)
            cb = (js.get("campaign", js) if isinstance(js, dict) else {}).get("eventCallBacks") or []
            cache[c] = any("everflow_transaction_id" in (x.get("pixelUrl") or "") and x.get("eventCode") == "converted" for x in cb)
        if cache[c]:
            return True, "Ringba sends converted calls to Everflow"
    return False, "No Ringba pixel sends converted calls to Everflow" if campaigns else "No Ringba campaign set for this brand"


def build():
    import publishers
    t0 = time.time()
    pb = publishers.board()
    offers, by_offer = _offers(), _brand_for_offer()
    our = {name: (o, by_offer[o["id"]]) for name, o in offers.items() if o["id"] in by_offer}
    page_cache, pb_cache, rows = {}, {}, []
    for r in pb.get("rows", []):
        if r["source"] != "clicks" or r.get("campaign", "").strip() not in our:
            continue
        o, brand = our[r["campaign"].strip()]
        checks = {"signed": (not r.get("pending"), "Active in Everflow" if not r.get("pending") else "Account still pending in Everflow")}
        checks["page"] = _page_check(o["url"], brand["ringba"], page_cache)
        checks["postback"] = _postback_check(brand["ringba"], pb_cache)
        checks["click"] = (r.get("d90", 0) > 0, f'{r.get("d90", 0)} clicks in 90 days' if r.get("d90") else "No clicks yet")
        checks["call"] = (r.get("conv30", 0) > 0, f'{r.get("conv30", 0)} paid calls in 30 days' if r.get("conv30") else "No paid call yet")
        live = bool((r.get("today") or r.get("yesterday")) and r.get("conv30"))
        checks["live"] = (live, "Sending traffic and converting" if live else "Not live yet")
        blocker = next((k for k, _ in STEPS if not checks[k][0]), None)
        rows.append({"publisher": r["publisher"], "offer": r["campaign"].strip(), "offer_id": o["id"], "brand": brand["name"], "slug": brand["slug"],
                     "landing": re.sub(r"\?.*", "", o["url"]), "checks": {k: {"ok": v[0], "detail": v[1]} for k, v in checks.items()},
                     "blocker": blocker, "action": action(blocker, r, o, brand), "done": sum(1 for k, _ in STEPS if checks[k][0]),
                     "clicks90": r.get("d90", 0), "conv30": r.get("conv30", 0)})
    rows.sort(key=lambda x: (x["blocker"] is None, x["done"], x["publisher"].lower()))
    board = {"made": store.now(), "rows": rows, "seconds": round(time.time() - t0, 1), "errors": pb.get("errors", [])}
    _set(KEY, board)
    return board


def action(blocker, r, o, brand):
    lp_page = f"https://lp.{_domain(o['url'])}/" if _domain(o["url"]) else "the brand's lp. page"
    return {
        "signed": "Approve the publisher's Everflow account and give them the offer.",
        "page": f"Point offer {o['id']} in Everflow at a page with the Ringba tag ({lp_page}), keeping the everflow_transaction_id and everflow_source_id parameters.",
        "postback": "Add the Everflow pixel on the Ringba campaign (event: converted, with the everflow_transaction_id tag).",
        "click": "Send the publisher their tracking link and ask for one test click.",
        "call": "Place a test call from the publisher's link: click it, call the number on the page, stay on 2+ minutes, then check Everflow for the conversion.",
        "live": "Tell the publisher they are clear to send traffic, and watch the first day of calls.",
        None: "Live. Watch daily calls, rejects and payouts.",
    }[blocker]


def _domain(url):
    m = re.match(r"https?://(?:www\.)?([^/?#]+)", url or "")
    if not m:
        return ""
    host = m.group(1)
    parts = host.split(".")
    return ".".join(parts[-2:])


def board(max_age_min=CACHE_MIN, fresh=False):
    b = _get(KEY, None)
    if b and not fresh:
        try:
            age = (time.time() - time.mktime(time.strptime(b["made"], "%Y-%m-%d %H:%M:%S"))) / 60
        except Exception:
            age = 1e9
        if age <= max_age_min:
            return b
    try:
        return build()
    except Exception as ex:
        return b or {"made": "", "rows": [], "errors": [f"Could not build the go-live board: {str(ex)[:160]}"], "seconds": 0}
