"""Connectors, each with a LIVE mode (real API, used when credentials exist) and a SANDBOX mode (local simulation, used when they
do not). Sandbox data is always labeled. Each system has one job:
  Ringba       calls: tracking numbers, call logs, buyers and payouts
  Everflow     clicks: offers, click and conversion reporting, postback tracking
  LeadProsper  lead delivery: leads posted to buyers, accepted, duplicated or failed, with revenue
  GoHighLevel  CRM: brand launch stages and every call or lead as an opportunity (still sandbox until a token is added)
Ringba, Everflow and LeadProsper were verified read-only against the real accounts; GoHighLevel is still unverified.

Credentials: data/integrations.json or env RINGBA_ACCOUNT_ID, RINGBA_API_KEY, EVERFLOW_API_KEY, LEADPROSPER_API_TOKEN, GHL_TOKEN, GHL_LOCATION_ID."""
import datetime as dt
import hashlib
import json
import os
import random
import re
import threading
import time
import urllib.error
import urllib.request

import core
import store

CFG_FILE = core.DATA / "integrations.json"

PIPELINES = {
    "Brand launch": ["Draft", "Generated", "Legal review", "Ready to test", "Ready to launch", "Live", "Paused"],
    "Call leads": ["New call", "Converted", "Follow up", "Closed"],
    "Partner onboarding": ["Campaign identified", "Post call email", "Send or request MSA", "Review MSA redlines", "MSA signatures",
                           "Verify campaign details", "Creatives review", "Send or request IO", "IO signatures", "Ops handoff", "Update folder", "Bench"],
}
REQUIRED = {"ringba": ("account_id", "api_key"), "everflow": ("api_key",), "leadprosper": ("token",), "ghl": ("token", "location_id"), "gemini": ("api_key",)}
ENV = {"ringba": {"account_id": "RINGBA_ACCOUNT_ID", "api_key": "RINGBA_API_KEY"}, "everflow": {"api_key": "EVERFLOW_API_KEY"},
       "leadprosper": {"token": "LEADPROSPER_API_TOKEN"}, "ghl": {"token": "GHL_TOKEN", "location_id": "GHL_LOCATION_ID"}, "gemini": {"api_key": "GEMINI_API_KEY"}}
LABEL = {"ringba": "Ringba", "everflow": "Everflow", "leadprosper": "LeadProsper", "ghl": "GoHighLevel", "gemini": "Gemini"}
ROLE = {"ringba": "Calls", "everflow": "Clicks", "leadprosper": "Lead delivery", "ghl": "CRM", "gemini": "AI"}
SYSTEM_FOR = {"calls": "ringba", "clicks": "everflow", "leads": "leadprosper"}


# ------------------------------------------------------------------ config and mode

def _file():
    return json.loads(CFG_FILE.read_text(encoding="utf-8")) if CFG_FILE.exists() else {}


def creds(name):
    d = dict(_file().get(name, {}))
    for k, env in ENV[name].items():
        if os.environ.get(env):
            d[k] = os.environ[env]
    return d


def mode(name):
    if _file().get("force_sandbox"):
        return "sandbox"
    c = creds(name)
    return "live" if all(c.get(k) for k in REQUIRED[name]) else "sandbox"


def save_cfg(updates):
    if serverless():
        raise ValueError("This deployment takes credentials from its environment variables. Change them in the Vercel project settings.")
    d = _file()
    for name, vals in updates.items():
        if name == "force_sandbox":
            d["force_sandbox"] = bool(vals)
        elif name in REQUIRED:
            d.setdefault(name, {}).update({k: v.strip() for k, v in vals.items() if isinstance(v, str) and v.strip()})
    CFG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CFG_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")


def mask(v):
    return ("*" * 6 + v[-4:]) if v and len(v) > 4 else ("set" if v else "")


def status():
    out = {}
    for n in REQUIRED:
        c = creds(n)
        out[n] = {"label": LABEL[n], "role": ROLE[n], "mode": ("live" if (n == "gemini" and c.get("api_key")) else "off") if n == "gemini" else mode(n), "fields": {k: mask(c.get(k, "")) for k in REQUIRED[n]}}
    out["force_sandbox"] = bool(_file().get("force_sandbox"))
    return out


def any_sandbox():
    return any(mode(n) == "sandbox" for n in ("ringba", "everflow", "leadprosper"))


def _http(method, url, headers=None, body=None, timeout=25):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json", "Accept": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw, code = r.read(), r.status
    except urllib.error.HTTPError as ex:
        raw, code = ex.read(), ex.code
    except Exception as ex:
        return 0, str(ex)
    try:
        return code, json.loads(raw)
    except Exception:
        return code, raw.decode("utf-8", "ignore")[:300]


# ------------------------------------------------------------------ catalogs (live accounts, cached)

_CAT = {}


def _cache_file(key):
    return core.DATA / "cache" / f"catalog_{key}.json"


def _cached(key, fn, ttl=1800):
    """Memory first, then a small file (mirrored to the database on Vercel so cold instances skip the slow vendor calls), then the vendor."""
    hit = _CAT.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    try:
        d = json.loads(_cache_file(key).read_text(encoding="utf-8"))
        if time.time() - d["t"] < ttl:
            _CAT[key] = (d["t"], d["v"])
            return d["v"]
    except Exception:
        pass
    try:
        v = fn()
    except Exception:
        v = hit[1] if hit else []
    _CAT[key] = (time.time(), v)
    if v:
        try:
            f = _cache_file(key)
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps({"t": time.time(), "v": v}), encoding="utf-8")
        except Exception:
            pass
    return v


def clear_catalogs():
    _CAT.clear()
    for f in (core.DATA / "cache").glob("catalog_*.json") if (core.DATA / "cache").exists() else []:
        try:
            f.unlink()
        except Exception:
            pass


def serverless():
    import paths
    return paths.SERVERLESS


def _now_utc():
    return dt.datetime.now(dt.timezone.utc)


def ids(value, resolver):
    """A brand can map to several campaigns, stored comma-separated (ids or exact names). Returns the resolved ids that exist."""
    out = []
    for part in re.split(r"[,;]", value or ""):
        r = resolver(part.strip())
        if r and r not in out:
            out.append(r)
    return out


# ------------------------------------------------------------------ Ringba (calls)

def _rb():
    c = creds("ringba")
    return f"https://api.ringba.com/v2/{c.get('account_id', '')}", {"Authorization": "Token " + c.get("api_key", "")}


def gemini_test():
    key = creds("gemini").get("api_key", "")
    if not key:
        return {"ok": False, "mode": "off", "detail": "No Gemini key set."}
    code, js = _http("GET", "https://generativelanguage.googleapis.com/v1beta/models?pageSize=50", {"x-goog-api-key": key})
    n = len([m for m in js.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]) if isinstance(js, dict) else 0
    return {"ok": code == 200, "mode": "live", "detail": f"HTTP {code}, {n} models available" if code == 200 else f"HTTP {code}: {str(js)[:160]}"}


def ringba_test():
    if mode("ringba") == "sandbox":
        return {"ok": True, "mode": "sandbox", "detail": "Sandbox: no account needed. Add RINGBA_ACCOUNT_ID and RINGBA_API_KEY to go live."}
    base, h = _rb()
    code, js = _http("GET", base + "/campaigns", h)
    n = len(js.get("campaigns", [])) if isinstance(js, dict) else 0
    return {"ok": code == 200, "mode": "live", "detail": f"HTTP {code}, {n} campaigns" if code == 200 else f"HTTP {code}: {str(js)[:160]}"}


def ringba_campaigns():
    """[{id, name}] for every campaign in the Ringba account (live only)."""
    if mode("ringba") != "live":
        return []

    def load():
        base, h = _rb()
        code, js = _http("GET", base + "/campaigns", h)
        items = js.get("campaigns", []) if isinstance(js, dict) else []
        return sorted(({"id": c.get("id", ""), "name": (c.get("name") or "").strip()} for c in items if c.get("id")), key=lambda c: c["name"].lower())
    return _cached("ringba_campaigns", load)


def ringba_numbers():
    """{campaign id: ["(844) 555-0100", ...]} for numbers attached to a campaign."""
    if mode("ringba") != "live":
        return {}

    def load():
        base, h = _rb()
        code, js = _http("GET", base + "/numbers", h)
        out = {}
        for n in (js.get("numbers", []) if isinstance(js, dict) else []):
            if n.get("campaignId") and n.get("enabled", True):
                out.setdefault(n["campaignId"], []).append(n.get("localNumber") or n.get("phoneNumber", ""))
        return out
    return _cached("ringba_numbers", load) or {}


def ringba_campaign_id(value):
    """Accepts a Ringba campaign id or an exact campaign name and returns the id (or empty)."""
    v = (value or "").strip()
    if not v:
        return ""
    if re.fullmatch(r"CA[0-9a-fA-F]{20,}", v):
        return v
    for c in ringba_campaigns():
        if c["name"].lower() == v.lower():
            return c["id"]
    return ""


def provision_number(slug):
    """Sandbox only: assigns a sandbox number. In live mode use assign_number, which takes the number from the Ringba campaign."""
    if mode("ringba") == "live":
        raise ValueError("Live mode: use the number attached to the Ringba campaign.")
    n = int(hashlib.sha1(slug.encode()).hexdigest(), 16) % 9000 + 1000
    num = f"(844) 3{n // 100:02d}-{n % 100:02d}{(n * 7) % 100:02d}"
    core.set_brand_field(slug, "phone", num)
    core.set_brand_field(slug, "ringba_campaign", f"sbx-{slug}")
    store.log_event(slug, "ringba.number_assigned", f"{num} (sandbox)")
    return num


def assign_number(slug):
    """Sandbox: assign a labeled sandbox number. Live: copy the number attached to the brand's Ringba campaign into the brand."""
    if mode("ringba") == "sandbox":
        return provision_number(slug)
    b = core.get_brand(slug)
    cids = ids(b["ringba_campaign"], ringba_campaign_id)
    if not cids:
        raise ValueError("Pick the brand's Ringba campaign first.")
    nums = next((ringba_numbers()[c] for c in cids if ringba_numbers().get(c)), [])
    if not nums:
        raise ValueError("That Ringba campaign has no number attached yet. Attach a number or a pool in Ringba, then try again.")
    core.set_brand_field(slug, "phone", nums[0])
    store.log_event(slug, "ringba.number_assigned", f"{nums[0]} from campaign {cids[0]}")
    return nums[0]


def place_test_call(slug):
    """Sandbox: records a test call. Live: looks for a call you just placed to the brand's campaign in the last hour and marks it as the test call."""
    b = core.get_brand(slug)
    if mode("ringba") == "sandbox":
        cid = f"sbx-test-{slug}-{time.time_ns()}"
        store.x("insert into calls(ts,slug,call_id,click_id,caller,duration,converted,payout,buyer,campaign,is_test,sandbox) values(?,?,?,?,?,?,?,?,?,?,1,1)",
                (store.now(), slug, cid, "test-click", "(555) 010-9999", 47, 0, 0, b["buyer"] or "unassigned", b["ringba_campaign"] or f"sbx-{slug}"))
        store.log_event(slug, "ringba.test_call", "sandbox test call recorded")
        return {"ok": True, "detail": "Sandbox test call recorded."}
    pull_calls(slug)
    cutoff = (dt.datetime.now() - dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    rows = store.q("select call_id from calls where slug=? and ts>=? and is_test=0 and sandbox=0 order by ts desc limit 1", (slug, cutoff))
    if not rows:
        return {"ok": False, "detail": "No call found in the last hour. Call the brand's number, then try again."}
    store.x("update calls set is_test=1 where call_id=?", (rows[0]["call_id"],))
    store.log_event(slug, "ringba.test_call", f"live call {rows[0]['call_id']} marked as the test call")
    return {"ok": True, "detail": "Found your call and marked it as the test call."}


def has_test_call(slug):
    return bool(store.q("select 1 from calls where slug=? and is_test=1 limit 1", (slug,)))


def pull_calls(slug, days=30):
    """Live: fetch recent call logs for the brand's Ringba campaign into the store. Sandbox: no-op (simulated rows are already stored)."""
    if mode("ringba") == "sandbox":
        return {"mode": "sandbox", "new": 0}
    b = core.get_brand(slug)
    cids = ids(b["ringba_campaign"], ringba_campaign_id)
    if not cids:
        return {"mode": "live", "new": 0, "error": "No Ringba campaign picked for this brand."}
    base, h = _rb()
    end = _now_utc()
    new, offset, total = 0, 0, None
    cols = ("callDt", "inboundCallId", "inboundPhoneNumber", "callLengthInSeconds", "hasConverted", "conversionAmount", "buyer", "campaignName")
    while True:
        body = {"reportStart": (end - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ"), "reportEnd": end.strftime("%Y-%m-%dT%H:%M:%SZ"), "size": 200, "offset": offset,
                "valueColumns": [{"column": c} for c in cols],
                "filters": [{"anyConditionToMatch": [{"column": "campaignId", "value": c, "isNegativeMatch": False, "comparisonType": "EQUALS"} for c in cids]}]}
        code, js = _http("POST", base + "/calllogs", h, body)
        if code != 200 or not isinstance(js, dict):
            store.log_event(slug, "ringba.error", f"HTTP {code}: {str(js)[:160]}")
            return {"mode": "live", "new": new, "error": f"HTTP {code}"}
        rep = js.get("report", {})
        recs = rep.get("records", [])
        total = rep.get("totalCount", len(recs))
        for r in recs:
            call_id = str(r.get("inboundCallId") or r.get("callId") or "")
            if not call_id or store.q("select 1 from calls where call_id=?", (call_id,)):
                continue
            raw = str(r.get("callDt") or "")
            if raw.isdigit():  # Ringba returns epoch milliseconds
                ts = dt.datetime.fromtimestamp(int(raw) / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            else:
                ts = (raw[:19].replace("T", " ")) or store.now()
            store.x("insert into calls(ts,slug,call_id,click_id,caller,duration,converted,payout,buyer,campaign,sandbox) values(?,?,?,?,?,?,?,?,?,?,0)",
                    (ts, slug, call_id, "", str(r.get("inboundPhoneNumber", "")), int(r.get("callLengthInSeconds") or 0), 1 if r.get("hasConverted") else 0,
                     float(r.get("conversionAmount") or 0), str(r.get("buyer", "")), str(r.get("campaignName", ""))))
            new += 1
        offset += 200
        if not recs or offset >= (total or 0) or offset > 5000:
            break
    if new:
        store.log_event(slug, "ringba.pull", f"{new} new calls")
    return {"mode": "live", "new": new, "total": total}


# ------------------------------------------------------------------ Everflow (clicks)

EF = "https://api.eflow.team/v1/networks"


def _ef():
    return {"X-Eflow-API-Key": creds("everflow").get("api_key", "")}


def everflow_test():
    if mode("everflow") == "sandbox":
        return {"ok": True, "mode": "sandbox", "detail": "Sandbox: no account needed. Add EVERFLOW_API_KEY to go live."}
    code, js = _http("GET", EF + "/offers?page=1&page_size=1", _ef())
    n = (js.get("paging") or {}).get("total_count") if isinstance(js, dict) else None
    return {"ok": code == 200, "mode": "live", "detail": f"HTTP {code}, {n} offers" if code == 200 else f"HTTP {code}: {str(js)[:160]}"}


def everflow_offers():
    """[{id, name, status}] for every Everflow offer (live only)."""
    if mode("everflow") != "live":
        return []

    def load():
        code, js = _http("GET", EF + "/offers?page=1&page_size=500", _ef())
        items = js.get("offers", []) if isinstance(js, dict) else []
        return [{"id": str(o.get("network_offer_id", "")), "name": (o.get("name") or "").strip(), "status": o.get("offer_status", "")} for o in items if o.get("network_offer_id")]
    return _cached("everflow_offers", load)


def everflow_offer_id(value):
    v = (value or "").strip()
    if not v:
        return ""
    if v.isdigit():
        return v
    for o in everflow_offers():
        if o["name"].lower() == v.lower():
            return o["id"]
    return ""


def pull_everflow(slug, days=30):
    """Live: per-day valid clicks, conversions and revenue for the brand's Everflow offer."""
    if mode("everflow") == "sandbox":
        return {"mode": "sandbox"}
    b = core.get_brand(slug)
    oids = ids(b["everflow_offer"], everflow_offer_id)
    if not oids:
        return {"mode": "live", "error": "No Everflow offer picked for this brand."}
    today = dt.date.today()
    per_day = {}
    for oid in oids:
        body = {"from": (today - dt.timedelta(days=days)).isoformat(), "to": today.isoformat(), "timezone_id": 90, "currency_id": "USD",
                "columns": [{"column": "offer"}, {"column": "date"}], "query": {"filters": [{"resource_type": "offer", "filter_id_value": oid}]}}
        code, js = _http("POST", EF + "/reporting/entity/table", _ef(), body)
        if code != 200 or not isinstance(js, dict):
            store.log_event(slug, "everflow.error", f"offer {oid} HTTP {code}: {str(js)[:160]}")
            return {"mode": "live", "error": f"HTTP {code}"}
        for t in js.get("table", []):
            d = next((c for c in t.get("columns", []) if c.get("column_type") == "date"), None)
            if not d:
                continue
            day = (dt.datetime.fromtimestamp(int(d["id"]), dt.timezone.utc) + dt.timedelta(hours=12)).date().isoformat()
            r = t.get("reporting", {})
            a = per_day.setdefault(day, [0, 0, 0.0])
            a[0] += int(r.get("total_click", 0) or 0)
            a[1] += int(r.get("cv", 0) or 0)
            a[2] += float(r.get("revenue", 0) or 0)
    store.x("delete from traffic_daily where slug=? and sandbox=0 and source='everflow'", (slug,))
    store.xmany("insert or replace into traffic_daily(slug,day,source,clicks,conversions,revenue,sandbox) values(?,?,?,?,?,?,?)",
                [(slug, day, "everflow", a[0], a[1], round(a[2], 2), 0) for day, a in per_day.items()])
    return {"mode": "live", "days": len(per_day), "offers": len(oids)}


def postback_template():
    c = _file().get("everflow", {})
    dom = c.get("tracking_domain", "YOUR-TRACKING-DOMAIN")
    return f"https://{dom}/?nid={c.get('network_id', 'NETWORK_ID')}&transaction_id={{click_id}}&amount={{payout}}"


# ------------------------------------------------------------------ LeadProsper (lead delivery)

LP = "https://api.leadprosper.io/public"
LP_POST = "https://api.leadprosper.io/direct_post"


def _lp():
    return {"Authorization": "Bearer " + creds("leadprosper").get("token", ""), "User-Agent": "BrandStudio/1.0"}


def lp_test():
    if mode("leadprosper") == "sandbox":
        return {"ok": True, "mode": "sandbox", "detail": "Sandbox: no account needed. Add LEADPROSPER_API_TOKEN to go live."}
    code, js = _http("GET", LP + "/v2/campaigns?view=short&limit=100", _lp())
    n = len((js.get("data") or {}).get("campaigns", [])) if isinstance(js, dict) else 0
    return {"ok": code == 200, "mode": "live", "detail": f"HTTP {code}, {n} campaigns" if code == 200 else f"HTTP {code}: {str(js)[:160]}"}


def lp_campaigns():
    """[{id, name, type}] for every LeadProsper campaign (live only)."""
    if mode("leadprosper") != "live":
        return []

    def load():
        out, after = [], None
        for _ in range(20):
            code, js = _http("GET", LP + "/v2/campaigns?view=short&limit=100" + (f"&search_after={after}" if after else ""), _lp())
            data = (js.get("data") or {}) if isinstance(js, dict) else {}
            out += [{"id": str(c["id"]), "name": (c.get("name") or "").strip(), "type": c.get("campaign_type", "")} for c in data.get("campaigns", [])]
            after = data.get("search_after")
            if code != 200 or not after:
                break
        return sorted(out, key=lambda c: c["name"].lower())
    return _cached("lp_campaigns", load)


def lp_campaign_id(value):
    v = (value or "").strip()
    if not v:
        return ""
    if v.isdigit():
        return v
    for c in lp_campaigns():
        if c["name"].lower() == v.lower():
            return c["id"]
    return ""


def lp_posting(slug):
    """Resolve what is needed to post a lead for the brand: campaign id, supplier id, lp_key and the field names. Returns a dict or {'error': ...}."""
    b = core.get_brand(slug)
    cids = ids(b["leadprosper_campaign"], lp_campaign_id)
    if not cids:
        return {"error": "Pick the brand's LeadProsper campaign first."}
    cid = cids[0]  # test leads go to the first mapped campaign
    code, js = _http("GET", f"{LP}/v2/campaigns/{cid}", _lp())
    d = ((js.get("data") or js) if isinstance(js, dict) else {})
    d = d.get("campaign", d) if isinstance(d, dict) else {}
    sups = [s for s in d.get("suppliers", []) if not s.get("paused")]
    want = (b["leadprosper_supplier"] or "").strip()
    sup = next((s for s in sups if str(s.get("id")) == want or (s.get("name") or "").lower() == want.lower()), None) if want else (sups[0] if sups else None)
    if not sup:
        return {"error": "This LeadProsper campaign has no active supplier to post as."}
    specs = sup.get("api_specs_url", "")
    key = ""
    if specs:
        try:
            req = urllib.request.Request(specs, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                html_text = r.read().decode("utf-8", "replace")
            m = re.search(r'data-copy-text="lp_key".{0,6000}?Must be set to:.{0,800}?data-copy-text="([^"]+)"', html_text, re.S)
            key = m.group(1) if m else ""
        except Exception:
            key = ""
    return {"campaign_id": str(cid), "supplier_id": str(sup["id"]), "supplier": sup.get("name", ""), "key": key, "test_mode": bool(sup.get("test_mode")),
            "fields": [f.get("name") for f in d.get("fields", []) if f.get("name")], "type": d.get("campaign_type", "direct_post"), "name": d.get("name", "")}


SAMPLE = {"first_name": "Test", "last_name": "Lead", "email": "test.lead@example.com", "phone": "5555550100", "state": "FL", "zip_code": "33101", "city": "Miami",
          "address": "1 Test Street", "ip_address": "203.0.113.10", "user_agent": "BrandStudio test", "date_of_birth": "1970-01-01", "gender": "male"}


def deliver_lead(slug, lead=None, test=True):
    """Post one lead to the brand's LeadProsper campaign (direct post). test=True flags it as a test lead. Live only: sandbox records a labeled fake."""
    b = core.get_brand(slug)
    if mode("leadprosper") == "sandbox":
        lid = f"sbx-lead-{slug}-{time.time_ns()}"
        store.x("insert into leads(ts,slug,lead_id,campaign,status,revenue,is_test,sandbox,detail) values(?,?,?,?,?,?,?,?,?)",
                (store.now(), slug, lid, b["leadprosper_campaign"] or f"sbx-{slug}", "accepted", 0, 1 if test else 0, 1, "sandbox"))
        store.log_event(slug, "leadprosper.test_lead" if test else "leadprosper.lead", "sandbox lead recorded")
        return {"ok": True, "status": "accepted", "detail": "Sandbox test lead recorded.", "lead_id": lid}
    post = lp_posting(slug)
    if post.get("error"):
        return {"ok": False, "detail": post["error"]}
    if not post["key"]:
        return {"ok": False, "detail": "Could not read the posting key from the supplier's API specs page."}
    payload = {"lp_campaign_id": post["campaign_id"], "lp_supplier_id": post["supplier_id"], "lp_key": post["key"], "landing_page_url": b["current_url"] or "https://example.com"}
    if test:
        payload["lp_action"] = "test"
    payload.update({k: v for k, v in SAMPLE.items() if k in post["fields"]} if lead is None else lead)
    code, js = _http("POST", LP_POST, {"User-Agent": "BrandStudio/1.0"}, payload)
    body = js if isinstance(js, dict) else {"message": str(js)[:200]}
    status = str(body.get("status", "")).lower()
    ok = code == 200 and ("accept" in status)
    lid = str(body.get("lead_id") or body.get("id") or f"lp-{time.time_ns()}")
    msg = body.get("message") or body.get("error") or (body.get("validation_errors") and json.dumps(body["validation_errors"])[:200]) or f"HTTP {code}"
    store.x("insert or replace into leads(ts,slug,lead_id,campaign,status,revenue,is_test,sandbox,detail) values(?,?,?,?,?,?,?,0,?)",
            (store.now(), slug, lid, post["campaign_id"], status or f"http {code}", float(body.get("revenue") or 0), 1 if test else 0, str(msg)[:200]))
    store.log_event(slug, "leadprosper.test_lead" if test else "leadprosper.lead", f"{status or code}: {str(msg)[:120]}")
    return {"ok": ok, "status": status or f"http {code}", "detail": ("Accepted by LeadProsper as a test lead." if ok else f"LeadProsper said: {msg}"), "lead_id": lid}


def place_test_lead(slug):
    return deliver_lead(slug, None, True)


def has_test_lead(slug):
    return bool(store.q("select 1 from leads where slug=? and is_test=1 and status like '%accept%' limit 1", (slug,)))


def pull_leads(slug, days=30):
    """Live: per-day lead volume, accepted, duplicated, failed and revenue for the brand's LeadProsper campaign. Sandbox: no-op."""
    if mode("leadprosper") == "sandbox":
        return {"mode": "sandbox"}
    b = core.get_brand(slug)
    cids = ids(b["leadprosper_campaign"], lp_campaign_id)
    if not cids:
        return {"mode": "live", "error": "No LeadProsper campaign picked for this brand."}
    end = dt.date.today()
    qs = "&".join(f"campaign[]={c}" for c in cids)
    code, js = _http("GET", f"{LP}/v2/stats?start_date={end - dt.timedelta(days=days)}&end_date={end}&group=day&{qs}", _lp())
    if code != 200 or not isinstance(js, list):
        store.log_event(slug, "leadprosper.error", f"HTTP {code}: {str(js)[:160]}")
        return {"mode": "live", "error": f"HTTP {code}"}
    days_map = {}
    for row in js:
        for s in row.get("suppliers", []):
            for d in s.get("breakdown", []):
                a = days_map.setdefault(d["date"], [0, 0, 0, 0, 0.0, 0.0])
                a[0] += d.get("leads_total", 0)
                a[1] += d.get("leads_accepted", 0)
                a[2] += d.get("leads_duplicated", 0)
                a[3] += d.get("leads_failed", 0)
                a[4] += d.get("total_sell", 0) or 0
                a[5] += d.get("total_buy", 0) or 0
    store.x("delete from leads_daily where slug=? and sandbox=0", (slug,))
    store.xmany("insert or replace into leads_daily(slug,day,campaign,leads,accepted,duplicated,failed,revenue,cost,sandbox) values(?,?,?,?,?,?,?,?,?,0)",
                [(slug, day, ",".join(cids), a[0], a[1], a[2], a[3], round(a[4], 2), round(a[5], 2)) for day, a in days_map.items()])
    return {"mode": "live", "days": len(days_map)}


# ------------------------------------------------------------------ mapping suggestions

STOP = {"the", "and", "of", "a", "pro", "live", "center", "centre", "inc", "llc", "com", "co", "campaign", "exclusive"}
ALIAS = {"hsl": "home service live", "ffp": "flight finder pro", "fe": "final expense", "us": "us"}


def _tokens(text):
    t = re.sub("['\u2019]", "", (text or "").lower())
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    for a, full in ALIAS.items():
        t = re.sub(r"\b" + a + r"\b", full, t)
    return [(w[:-1] if len(w) > 4 and w.endswith("s") else w) for w in t.split() if w and w not in STOP]


def _score(brand, cand, vertical_hint=""):
    """Brand-name tokens must all appear in the candidate name; a vertical hint adds a little."""
    bt, ct = _tokens(brand), set(_tokens(cand))
    if not bt:
        return 0.0
    hit = sum(1 for w in bt if w in ct) / len(bt)
    if hit < 1.0:
        return round(hit * 0.4, 2)
    bonus = 0.1 if vertical_hint and any(w in ct for w in _tokens(vertical_hint)) else 0
    return round(0.8 + bonus - min(0.1, 0.01 * max(0, len(ct) - len(bt))), 2)


def _prefix(brand, cand):
    """True when the candidate's name starts with the brand's name, e.g. 'Debt Center - Inbounds' for Debt Center."""
    bn, cn = re.sub(r"[^a-z0-9]", "", brand.lower()), re.sub(r"[^a-z0-9]", "", cand.lower())
    if bn and cn.startswith(bn):
        return True
    bt, ct = _tokens(brand), _tokens(cand)  # looser match only for names with two or more distinctive words
    return len(bt) >= 2 and ct[:len(bt)] == bt


def suggest(slug, top=6):
    """Likely Ringba campaign, Everflow offer and LeadProsper campaign for a brand, by name. Live accounts only."""
    b = core.get_brand(slug)
    hint = b["vertical"]
    out = {}
    for key, items in (("ringba", ringba_campaigns()), ("everflow", everflow_offers()), ("leadprosper", lp_campaigns())):
        scored = sorted(({"id": c["id"], "name": c["name"], "score": _score(b["name"], c["name"], hint)} for c in items), key=lambda c: (-c["score"], c["name"].lower()))
        for c in scored:
            c["confident"] = c["score"] >= 0.8 and _prefix(b["name"], c["name"])
        out[key] = [c for c in scored if c["score"] >= 0.4][:top if top else None]
    return out


FIELD_FOR = {"ringba": "ringba_campaign", "everflow": "everflow_offer", "leadprosper": "leadprosper_campaign"}


def automap(slug=None, apply=True):
    """Map brands to the campaigns whose names start with the brand's name (confident matches only). Local brands.csv only; nothing is changed in the vendors."""
    result = []
    for b in core.load_brands():
        if slug and b["slug"] != slug:
            continue
        s = suggest(b["slug"], top=0)
        row = {"slug": b["slug"], "name": b["name"], "mapped": {}}
        for sys_name, field in FIELD_FOR.items():
            conf = [c for c in s[sys_name] if c["confident"]]
            if conf and not (b[field] or "").strip():
                row["mapped"][sys_name] = [c["name"] for c in conf]
                if apply:
                    core.set_brand_field(b["slug"], field, ",".join(c["id"] for c in conf))
        result.append(row)
    if apply:
        clear_catalogs()
    return result


def catalog():
    return {"ringba": ringba_campaigns(), "everflow": everflow_offers(), "leadprosper": lp_campaigns()}


# ------------------------------------------------------------------ GoHighLevel

GHL = "https://services.leadconnectorhq.com"


def _gh():
    return {"Authorization": "Bearer " + creds("ghl").get("token", ""), "Version": "2021-07-28"}


def ghl_test():
    if mode("ghl") == "sandbox":
        return {"ok": True, "mode": "sandbox", "detail": "Sandbox CRM: no account needed. Add GHL_TOKEN and GHL_LOCATION_ID to go live."}
    code, js = _http("GET", f"{GHL}/locations/{creds('ghl')['location_id']}", _gh())
    return {"ok": code == 200, "mode": "live", "detail": f"HTTP {code}" + ("" if code == 200 else f": {str(js)[:160]}")}


def _live_pipelines():
    code, js = _http("GET", f"{GHL}/opportunities/pipelines?locationId={creds('ghl')['location_id']}", _gh())
    if code != 200 or not isinstance(js, dict):
        raise RuntimeError(f"GoHighLevel pipelines: HTTP {code}")
    return {p["name"]: {"id": p["id"], "stages": {s["name"]: s["id"] for s in p.get("stages", [])}} for p in js.get("pipelines", [])}


def _upsert_contact(slug, phone, name, tags, fields):
    if mode("ghl") == "sandbox":
        existing = store.q("select id from ghl_contacts where slug=? and phone=?", (slug, phone))
        if existing:
            return existing[0]["id"]
        cid = f"sbx-c-{time.time_ns()}"
        store.x("insert into ghl_contacts(id,slug,phone,name,tags,fields,ts) values(?,?,?,?,?,?,?)", (cid, slug, phone, name, json.dumps(tags), json.dumps(fields), store.now()))
        return cid
    code, js = _http("POST", f"{GHL}/contacts/upsert", _gh(), {"locationId": creds("ghl")["location_id"], "phone": phone, "name": name, "tags": tags,
                                                               "customFields": [{"key": k, "field_value": str(v)} for k, v in fields.items()]})
    if code not in (200, 201) or not isinstance(js, dict):
        raise RuntimeError(f"GoHighLevel contact: HTTP {code}: {str(js)[:120]}")
    return (js.get("contact") or {}).get("id", "")


def _set_opp(slug, contact_id, pipeline, stage, name, value=0.0, opp_key=None):
    """Create the opportunity if it does not exist, otherwise move it to `stage`. opp_key identifies it (brand or call)."""
    if mode("ghl") == "sandbox":
        row = store.q("select id from ghl_opps where slug=? and pipeline=? and name=?", (slug, pipeline, name))
        if row:
            store.x("update ghl_opps set stage=?, updated=?, value=? where id=?", (stage, store.now(), value, row[0]["id"]))
            return row[0]["id"], False
        oid = f"sbx-o-{time.time_ns()}"
        store.x("insert into ghl_opps(id,contact_id,slug,pipeline,stage,name,value,ts,updated) values(?,?,?,?,?,?,?,?,?)",
                (oid, contact_id, slug, pipeline, stage, name, value, store.now(), store.now()))
        return oid, True
    pl = _live_pipelines()
    if pipeline not in pl or stage not in pl[pipeline]["stages"]:
        raise RuntimeError(f"Create the pipeline '{pipeline}' with the stage '{stage}' in GoHighLevel first.")
    pid, sid = pl[pipeline]["id"], pl[pipeline]["stages"][stage]
    known = store.q("select id from ghl_opps where slug=? and pipeline=? and name=?", (slug, pipeline, name))
    if known:
        code, js = _http("PUT", f"{GHL}/opportunities/{known[0]['id']}", _gh(), {"pipelineStageId": sid, "monetaryValue": value})
        store.x("update ghl_opps set stage=?, updated=? where id=?", (stage, store.now(), known[0]["id"]))
        return known[0]["id"], False
    code, js = _http("POST", f"{GHL}/opportunities/", _gh(), {"pipelineId": pid, "locationId": creds("ghl")["location_id"], "name": name,
                                                              "pipelineStageId": sid, "status": "open", "contactId": contact_id, "monetaryValue": value})
    if code not in (200, 201) or not isinstance(js, dict):
        raise RuntimeError(f"GoHighLevel opportunity: HTTP {code}: {str(js)[:120]}")
    oid = (js.get("opportunity") or js).get("id", f"live-{time.time_ns()}")
    store.x("insert into ghl_opps(id,contact_id,slug,pipeline,stage,name,value,ts,updated) values(?,?,?,?,?,?,?,?,?)",
            (oid, contact_id, slug, pipeline, stage, name, value, store.now(), store.now()))
    return oid, True


def desired_stage(slug):
    import compliance
    import publish
    ls = publish.live_status(slug)
    if ls["paused"]:
        return "Paused"
    if ls["live"]:
        return "Live"
    if not (core.OUT / slug / "index.html").exists():
        return "Draft"
    cl = core.checklist(slug)
    if cl["ready"]:
        return "Ready to launch"
    items = {i["key"]: i["ok"] for i in cl["items"]}
    if all(ok for key, ok in items.items() if key != "test"):
        return "Ready to test"
    if not compliance.is_approved(slug):
        return "Legal review"
    return "Generated"


def refresh_stage(slug):
    """Move the brand's opportunity in the 'Brand launch' pipeline to match where the brand really is. Never raises."""
    try:
        b = core.get_brand(slug)
        stage = desired_stage(slug)
        cid = _upsert_contact(slug, b["phone"] or "unassigned", b["name"] + " (brand)", ["brand", b["vertical"], slug], {"brand": slug, "vertical": b["vertical"]})
        _, created = _set_opp(slug, cid, "Brand launch", stage, b["name"])
        store.log_event(slug, "ghl.stage", f"Brand launch: {stage}" + (" (created)" if created else ""))
        return {"ok": True, "stage": stage}
    except Exception as ex:
        store.log_event(slug, "ghl.error", str(ex)[:200])
        return {"ok": False, "error": str(ex)}


def sync_calls(slug):
    """Create a GoHighLevel contact and opportunity for every real (non-test) call that has not been synced yet."""
    b = core.get_brand(slug)
    rows = store.q("select * from calls where slug=? and ghl_synced=0 and is_test=0 order by ts limit 500", (slug,))
    done, err = 0, None
    for r in rows:
        try:
            src = (store.q("select source from clicks where click_id=?", (r["click_id"],)) or [{"source": ""}])[0]["source"]
            tags = ["call", b["vertical"], slug] + ([src] if src else [])
            cid = _upsert_contact(slug, r["caller"] or "unknown", f"Caller {r['caller']}", tags,
                                  {"click_id": r["click_id"], "campaign": r["campaign"], "buyer": r["buyer"], "duration": r["duration"], "outcome": "converted" if r["converted"] else "no sale"})
            _set_opp(slug, cid, "Call leads", "Converted" if r["converted"] else "New call", f"{b['name']} call {r['call_id']}", r["payout"] or 0)
            store.x("update calls set ghl_synced=1 where id=?", (r["id"],))
            done += 1
        except Exception as ex:
            err = str(ex)
            break
    if done or err:
        store.log_event(slug, "ghl.sync", f"{done} calls synced" + (f", stopped: {err[:120]}" if err else ""))
    return {"synced": done, "error": err, "pending": store.q("select count(*) n from calls where slug=? and ghl_synced=0 and is_test=0", (slug,))[0]["n"]}


def board():
    out = {}
    for pl, stages in PIPELINES.items():
        opps = store.q("select * from ghl_opps where pipeline=? order by updated desc limit 400", (pl,))
        out[pl] = [{"stage": s, "items": [o for o in opps if o["stage"] == s]} for s in stages]
    return out


# ------------------------------------------------------------------ sandbox traffic

def simulate_traffic(slug, days=14):
    """SANDBOX ONLY: writes believable clicks and calls for the last `days` days so the ops dashboard has something to show."""
    if all(mode(n) == "live" for n in ("everflow", "ringba", "leadprosper")):
        raise ValueError("Live mode is on: real traffic comes from Everflow, Ringba and LeadProsper.")
    b = core.get_brand(slug)
    seed = int(hashlib.sha1(slug.encode()).hexdigest(), 16)
    rnd = random.Random(seed % (2 ** 32))
    base, call_rate, conv_p = rnd.randint(40, 140), rnd.uniform(.06, .12), rnd.uniform(.28, .45)
    anomaly = (seed % 5 == 0)
    store.x("delete from clicks where slug=? and sandbox=1", (slug,))
    store.x("delete from calls where slug=? and sandbox=1 and is_test=0", (slug,))
    store.x("delete from traffic_daily where slug=? and sandbox=1", (slug,))
    sources = ["mgid", "meta", "google", "native"]
    today = dt.date.today()
    clicks, calls, daily = [], [], []
    for back in range(days - 1, -1, -1):
        day = today - dt.timedelta(days=back)
        n = int(base * rnd.uniform(.7, 1.3))
        ids = []
        per = {s: [0, 0, 0.0] for s in sources}
        for k in range(n):
            s = rnd.choice(sources)
            cid = f"sbx-{slug}-{day:%m%d}-{k}"
            ts = f"{day} {rnd.randint(6, 22):02d}:{rnd.randint(0, 59):02d}:{rnd.randint(0, 59):02d}"
            clicks.append((ts, slug, cid, s, f"s{rnd.randint(1, 9)}", f"a{rnd.randint(10, 60)}", 1))
            ids.append((cid, s, ts))
            per[s][0] += 1
        n_calls = 0 if (anomaly and back < 2) else int(round(n * call_rate * rnd.uniform(.7, 1.3)))
        for k in range(n_calls):
            cid, s, ts = rnd.choice(ids)
            dur = rnd.randint(18, 420)
            conv = 1 if (dur > 90 and rnd.random() < conv_p * 1.6) else 0
            pay = round(rnd.uniform(38, 96), 2) if conv else 0.0
            calls.append((ts, slug, f"sbx-call-{slug}-{day:%m%d}-{k}", cid, f"(555) 01{rnd.randint(0, 9)}-{rnd.randint(1000, 9999)}", dur, conv, pay,
                          b["buyer"] or "Sandbox buyer", b["ringba_campaign"] or f"sbx-{slug}", 0, 1))
            per[s][1] += conv
            per[s][2] += pay
        for s, (c, cv, rv) in per.items():
            daily.append((slug, str(day), s, c, cv, round(rv, 2), 1))
    store.xmany("insert or ignore into clicks(ts,slug,click_id,source,sub1,affid,sandbox) values(?,?,?,?,?,?,?)", clicks)
    store.xmany("insert or ignore into calls(ts,slug,call_id,click_id,caller,duration,converted,payout,buyer,campaign,is_test,sandbox) values(?,?,?,?,?,?,?,?,?,?,?,?)", calls)
    store.xmany("insert or replace into traffic_daily(slug,day,source,clicks,conversions,revenue,sandbox) values(?,?,?,?,?,?,?)", daily)
    if "leads" in core.delivery_modes(b) and mode("leadprosper") == "sandbox":
        store.x("delete from leads_daily where slug=? and sandbox=1", (slug,))
        ld = []
        for back in range(days - 1, -1, -1):
            n = int(base * rnd.uniform(.2, .5))
            acc = int(n * rnd.uniform(.55, .85))
            ld.append((slug, str(today - dt.timedelta(days=back)), f"sbx-{slug}", n, acc, int(n * .08), n - acc - int(n * .08), round(acc * rnd.uniform(4, 22), 2), 0, 1))
        store.xmany("insert or replace into leads_daily(slug,day,campaign,leads,accepted,duplicated,failed,revenue,cost,sandbox) values(?,?,?,?,?,?,?,?,?,?)", ld)
    store.log_event(slug, "sandbox.traffic", f"{len(clicks)} clicks, {len(calls)} calls over {days} days (simulated)")
    return {"clicks": len(clicks), "calls": len(calls)}


# ------------------------------------------------------------------ refresh live data

_RUN = {"last": 0.0, "running": False, "summary": {}}
_run_lock = threading.Lock()


def refresh(slug=None, rebuild=False):
    """Pull the latest calls (Ringba), clicks (Everflow) and leads (LeadProsper) for every mapped brand, then sync calls to the CRM.
    Live mode only: in sandbox the simulated data is already stored. Returns a per-brand summary."""
    out = {}
    if rebuild:
        clear_catalogs()
        catalog()
        ringba_numbers()
    for b in core.load_brands():
        if slug and b["slug"] != slug:
            continue
        s = b["slug"]
        r = {}
        try:
            if mode("ringba") == "live" and b["ringba_campaign"]:
                r["ringba"] = pull_calls(s)
            if mode("everflow") == "live" and b["everflow_offer"]:
                r["everflow"] = pull_everflow(s)
            if mode("leadprosper") == "live" and b["leadprosper_campaign"]:
                r["leadprosper"] = pull_leads(s)
            if r:
                r["ghl"] = sync_calls(s)
        except Exception as ex:
            r["error"] = str(ex)[:160]
            store.log_event(s, "refresh.error", r["error"])
        if r:
            out[s] = r
    if not slug:
        _RUN.update(last=time.time(), summary={k: v for k, v in out.items()})
    return out


def refresh_state():
    return {"last": _RUN["last"], "running": _RUN["running"], "age_seconds": int(time.time() - _RUN["last"]) if _RUN["last"] else None}


def start_background(interval=900):
    """Refresh live data now and then every `interval` seconds, in a daemon thread. Safe to call once at startup."""
    def loop():
        while True:
            with _run_lock:
                _RUN["running"] = True
                try:
                    catalog()
                    ringba_numbers()
                    refresh()
                except Exception as ex:
                    store.log_event("", "refresh.error", str(ex)[:160])
                finally:
                    _RUN["running"] = False
            time.sleep(interval)
    if not any(t.name == "bs-refresh" for t in threading.enumerate()):
        threading.Thread(target=loop, name="bs-refresh", daemon=True).start()


def refresh_async():
    def work():
        with _run_lock:
            _RUN["running"] = True
            try:
                refresh()
            finally:
                _RUN["running"] = False
    if not _RUN["running"]:
        threading.Thread(target=work, daemon=True).start()
        return True
    return False


# ------------------------------------------------------------------ ops metrics and alerts

def ops(days=14):
    import publish
    start = (dt.date.today() - dt.timedelta(days=days - 1)).isoformat()
    brands = core.load_brands()
    info = core.sheet_info()
    rows, tot = [], {"clicks": 0, "calls": 0, "converted": 0, "leads": 0, "accepted": 0, "revenue": 0.0}
    day_list = [(dt.date.today() - dt.timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]
    for b in brands:
        s = b["slug"]
        clicks = sum(r["clicks"] for r in store.q("select clicks from traffic_daily where slug=? and day>=?", (s, start)))
        c = store.q("select count(*) n, sum(converted) cv, sum(payout) rev from calls where slug=? and substr(ts,1,10)>=? and is_test=0", (s, start))[0]
        series_calls = {r["d"]: r["n"] for r in store.q("select substr(ts,1,10) d, count(*) n from calls where slug=? and substr(ts,1,10)>=? and is_test=0 group by d", (s, start))}
        L = store.q("select sum(leads) n, sum(accepted) a, sum(revenue) r from leads_daily where slug=? and day>=?", (s, start))[0]
        series_leads = {r["day"]: r["accepted"] for r in store.q("select day, sum(accepted) accepted from leads_daily where slug=? and day>=? group by day", (s, start))}
        ls = publish.live_status(s)
        rev = round((c["rev"] or 0) + (L["r"] or 0), 2)
        sb = info.get(s) or {}
        rows.append({"slug": s, "name": b["name"], "live": ls["live"], "paused": ls["paused"], "clicks": clicks, "calls": c["n"] or 0, "converted": c["cv"] or 0,
                     "leads": L["n"] or 0, "accepted": L["a"] or 0, "revenue": rev, "rpc": round(rev / clicks, 2) if clicks else 0,
                     "series": [series_calls.get(d, 0) + series_leads.get(d, 0) for d in day_list], "stage": desired_stage(s), "color": b["accent_color"] or "#6b8cff",
                     "delivery": core.delivery_modes(b), "priority": sb.get("priority", ""), "mapped": {k: bool((b[f] or "").strip()) for k, f in FIELD_FOR.items()}})
        tot["clicks"] += clicks
        tot["calls"] += c["n"] or 0
        tot["converted"] += c["cv"] or 0
        tot["leads"] += L["n"] or 0
        tot["accepted"] += L["a"] or 0
        tot["revenue"] += rev
    tot["revenue"] = round(tot["revenue"], 2)
    return {"rows": rows, "total": tot, "days": days, "sandbox": any_sandbox(), "alerts": alerts(rows), "refresh": refresh_state()}


def alerts(rows=None):
    import compliance
    import publish
    out = []
    cutoff = (dt.datetime.now() - dt.timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
    two_days = (dt.date.today() - dt.timedelta(days=2)).isoformat()
    week = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    info = core.sheet_info()
    for b in core.load_brands():
        s, name = b["slug"], b["name"]
        gen = (core.OUT / s / "index.html").exists()
        ls = publish.live_status(s)
        modes = core.delivery_modes(b)
        sb = info.get(s) or {}
        if ls["live"]:
            recent_clicks = store.q("select sum(clicks) n from traffic_daily where slug=? and day>=?", (s, two_days))[0]["n"] or 0
            if "calls" in modes and recent_clicks and not store.q("select count(*) n from calls where slug=? and ts>=? and is_test=0", (s, cutoff))[0]["n"]:
                out.append({"level": "bad", "slug": s, "msg": f"{name}: traffic but no calls in 48 hours. Check the number, buyer and routing."})
            if "leads" in modes:
                r = store.q("select sum(leads) n, sum(accepted) a, sum(failed) f from leads_daily where slug=? and day>=?", (s, two_days))[0]
                if recent_clicks and not (r["n"] or 0):
                    out.append({"level": "bad", "slug": s, "msg": f"{name}: traffic but no leads reached LeadProsper in 48 hours. Check the form post."})
                w = store.q("select sum(leads) n, sum(failed) f from leads_daily where slug=? and day>=?", (s, week))[0]
                if (w["n"] or 0) >= 10 and (w["f"] or 0) / w["n"] > 0.5:
                    out.append({"level": "warn", "slug": s, "msg": f"{name}: more than half of leads failed in LeadProsper this week ({w['f']} of {w['n']})."})
            if str(sb.get("site_up", "")).strip().upper() == "N":
                out.append({"level": "warn", "slug": s, "msg": f"{name}: the Sheet marks the website as not up."})
        if gen:
            if not b["buyer"]:
                note = f" The Sheet says: {sb['buyers']}." if sb.get("buyers") else ""
                out.append({"level": "warn", "slug": s, "msg": f"{name}: no confirmed buyer.{note}"})
            st = compliance.status(s)
            if not st["approved"]:
                out.append({"level": "warn", "slug": s, "msg": f"{name}: {st['label'].lower()}."})
            if "calls" in modes and core.is_placeholder_phone(b["phone"]):
                out.append({"level": "warn", "slug": s, "msg": f"{name}: placeholder phone number. Use the Ringba campaign number."})
            for m in modes:
                sysn = SYSTEM_FOR[m]
                if mode(sysn) == "live" and not (b[FIELD_FOR[sysn]] or "").strip():
                    out.append({"level": "warn", "slug": s, "msg": f"{name}: delivers by {m} but no {LABEL[sysn]} campaign is picked."})
    sandbox = [LABEL[n] for n in ("ringba", "everflow", "leadprosper") if mode(n) == "sandbox"]
    if sandbox:
        out.append({"level": "info", "slug": "", "msg": f"{', '.join(sandbox)} in sandbox mode: its numbers are simulated. Add credentials on the Integrations page for real data."})
    return out
