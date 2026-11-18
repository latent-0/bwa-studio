"""The Campaign Tracker as a live two way view of the Google Sheet.
Read: the tracker is link readable, so every tab is fetched straight from the Sheet (short cache, last good snapshot on disk).
Write: an edit in the studio goes to a small Apps Script web app bound to the Sheet (the bridge), which finds the row by its key and writes the
cells. Nothing is stored here as the source of truth: the Sheet is. Config: env LP_BRIDGE_URL and LP_BRIDGE_TOKEN, or data/integrations.json
under "sheets": {"bridge_url": ..., "bridge_token": ...}."""
import csv
import datetime as dt
import io
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

import paths
import store

DATA = paths.ROOT / "data" / "sheet"
TTL = int(os.environ.get("LP_TTL", "15"))

# The Campaign Tracker is the only Sheet the studio connects to. (The older Landing Page Tracker was a duplicate and is no longer used.)
SOURCES = {
    "campaign": {"id": "19lMPfp3oW5W_zARZImYuQ21rslYHZM1j", "gid": "2063836095", "label": "Campaign Tracker"},
}
DEFAULT = "campaign"

# (field, column position in the Sheet, header in the Sheet). Columns are found by header text; the position is only a fallback.
COLS = {
    "campaign": [("brand", 0, "Brand"), ("campaign", 1, "Campaign"), ("stage", 2, "Production Stages"), ("page_url", 5, "Landing Page URL (call-only variant)"),
                 ("review_link", 23, "Reference Landing Page Draft Link"), ("feedback", 24, "Landing page Draft feedback"), ("variant", 25, "LP variant"),
                 ("build_owner", 26, "Build owner"), ("build_date", 27, "Build date"), ("approval", 28, "Jeff approval"), ("deploy_owner", 30, "Deploy owner"),
                 ("deploy_status", 31, "Deploy status"), ("live_url", 32, "Live URL For Feedback"), ("deploy_date", 33, "Deploy date"),
                 ("jeff_notes", None, "Notes from Jeff"), ("team_notes", None, "Notes from Tina/Ryan"),
                 ("notes", 39, "Missing items and review notes"), ("golive", 40, "Go-live check")],
}

# Fields the studio may write. Everything else (Jeff approval, calculated cells, links Jeff owns) stays read only here.
EDITABLE = {
    "campaign": {"variant": "LP variant", "build_owner": "Build owner", "build_date": "Build date", "deploy_owner": "Deploy owner",
                 "deploy_status": "Deploy status", "live_url": "Live URL For Feedback", "deploy_date": "Deploy date", "notes": "Missing items and review notes"},
}
OPTIONS = {
    "variant": ["A: With video", "B: Without video"],
    "build_owner": ["Kunal", "Lekha"], "deploy_owner": ["Kunal", "Lekha"],
    "build_status": ["Not started", "In progress", "Built", "Blocked"],
    "deploy_status": ["Not started", "Deployed", "Blocked"],
}
DATE_FIELDS = {"build_date", "deploy_date"}

_cache, _lock = {}, threading.Lock()
_state = {"error": "", "source": "not loaded"}


# ------------------------------------------------------------------ bridge config

def _cfg():
    c = {}
    f = paths.ROOT / "data" / "integrations.json"
    if f.exists():
        try:
            c = dict(json.loads(f.read_text(encoding="utf-8")).get("sheets", {}))
        except Exception:
            c = {}
    return {"url": os.environ.get("LP_BRIDGE_URL") or c.get("bridge_url", ""), "token": os.environ.get("LP_BRIDGE_TOKEN") or c.get("bridge_token", "")}


def bridge_ready():
    c = _cfg()
    return bool(c["url"] and c["token"])


# ------------------------------------------------------------------ read

def _snap(src):
    return DATA / f"tracker_{src}.csv"


def _fetch(src):
    s = SOURCES[src]
    u = f"https://docs.google.com/spreadsheets/d/{s['id']}/gviz/tq?tqx=out:csv&headers=0&gid={s['gid']}"
    last = None
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as r:
                return r.read().decode("utf-8-sig")
        except Exception as ex:
            last = ex
            time.sleep(0.5 * (i + 1))
    raise last


def _colmap(src, head):
    """Column index for every field, found by header text so the studio keeps working when someone inserts a column in the Sheet.
    Falls back to the template position only when a header is missing."""
    names = [h.strip() for h in head]
    return {f: (names.index(h) if h in names else pos) for f, pos, h in COLS[src]}


def _parse(src, text):
    data = list(csv.reader(io.StringIO(text)))
    cols = COLS[src]
    out, seen = [], {}
    started = False
    cmap = None
    for i, r in enumerate(data):
        r = [c.strip() for c in r] + [""] * 45
        if not started:
            started = r[0] == "Brand" and r[1] == "Campaign"
            if started:
                cmap = _colmap(src, r)
            continue
        if not (r[0] and r[1]):
            continue
        rec = {f: (r[cmap[f]] if cmap[f] is not None and cmap[f] >= 0 else "") for f, _, _ in cols}
        k = (r[0], r[1])
        seen[k] = seen.get(k, 0) + 1
        rec["key"] = {"Brand": r[0], "Campaign": r[1], "n": seen[k]}
        rec["rid"] = f"{r[0]}|{r[1]}|{seen[k]}"
        out.append(rec)
    return out


def rows(src, fresh=False):
    with _lock:
        hit = _cache.get(src)
        if hit and not fresh and time.time() - hit[0] < TTL:
            return hit[1]
    try:
        text = _fetch(src)
        DATA.mkdir(parents=True, exist_ok=True)
        _snap(src).write_text(text, encoding="utf-8")
        _state.update(error="", source="Google Sheet (live)")
    except Exception as ex:
        f = _snap(src)
        if not f.exists():
            _state.update(error=str(ex)[:120], source="unavailable")
            return []
        text = f.read_text(encoding="utf-8")
        _state.update(error=str(ex)[:120], source="Google Sheet (cached, fetch failed)")
    recs = _parse(src, text)
    with _lock:
        _cache[src] = (time.time(), recs)
    return recs


def status():
    return {"source": _state["source"], "error": _state["error"], "bridge": bridge_ready(),
            "sheets": {k: f"https://docs.google.com/spreadsheets/d/{v['id']}/edit#gid={v['gid']}" for k, v in SOURCES.items()}, "sheet": sheet_url()}


# ------------------------------------------------------------------ write

def _norm_date(v):
    v = (v or "").strip()
    if not v:
        return ""
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(v, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    raise ValueError("Dates look like 2026-11-05.")


def _display_date(iso):
    return dt.datetime.strptime(iso, "%Y-%m-%d").strftime("%d %b %Y") if iso else ""


def _call(payload):
    c = _cfg()
    if not (c["url"] and c["token"]):
        raise RuntimeError("Write-back to the Sheet is not connected yet. Add LP_BRIDGE_URL and LP_BRIDGE_TOKEN.")
    body = json.dumps({**payload, "token": c["token"]}).encode()
    req = urllib.request.Request(c["url"], data=body, method="POST", headers={"Content-Type": "text/plain;charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = r.read().decode("utf-8")
    except urllib.error.HTTPError as ex:
        raise RuntimeError(f"The Sheet bridge answered {ex.code}.")
    try:
        res = json.loads(txt)
    except ValueError:
        raise RuntimeError("The Sheet bridge did not answer with data. Check that it is deployed for anyone with the link.")
    if not res.get("ok"):
        raise RuntimeError(res.get("error", "The Sheet rejected the change."))
    return res


def find(src, rid):
    for r in rows(src):
        if r["rid"] == rid:
            return r
    return None


def update(src, rid, changes, actor="studio"):
    """Validate, write to the Sheet through the bridge, then patch the cached row so the page shows it at once. Returns the new row."""
    if src not in SOURCES:
        raise ValueError("Unknown tracker.")
    rec = find(src, rid)
    if not rec:
        raise ValueError("That row is no longer in the Sheet. Refresh the page.")
    allowed = EDITABLE[src]
    send, new = {}, {}
    for f, v in changes.items():
        if f not in allowed:
            raise ValueError(f"{f} is not editable from the studio.")
        v = (v or "").strip()
        if f in DATE_FIELDS:
            iso = _norm_date(v)
            send[allowed[f]], new[f] = iso, _display_date(iso)
            continue
        if f in OPTIONS and v and v not in OPTIONS[f]:
            raise ValueError(f"{v} is not an option for {allowed[f]}.")
        if f == "live_url" and v and not re.match(r"^https?://\S+$", v):
            raise ValueError("The live URL must start with http:// or https://.")
        send[allowed[f]], new[f] = v, v
    if not send:
        return rec
    _call({"action": "update", "sheet": src, "key": rec["key"], "set": send})
    with _lock:
        hit = _cache.get(src)
        if hit:
            for r in hit[1]:
                if r["rid"] == rid:
                    r.update(new)
    brand = rec.get("brand", "")
    slug = re.sub(r"[^a-z0-9]+", "-", brand.lower()).strip("-") or "trackers"
    label = rec.get("id") or rec.get("campaign", "")
    store.log_event(slug, "tracker", f"{SOURCES[src]['label']} {label}: " + ", ".join(f"{allowed[f]} = {v or 'blank'}" for f, v in new.items()), actor)
    return find(src, rid) or rec


def log_deploy(brand, variant, live_url, notes=None, build_date=None, owner="Kunal"):
    """Called by the deploy script so every page it ships lands in the Campaign Tracker without a manual edit.
    The tracker has one row per campaign, so a brand page is logged on the brand's row that already carries variant A (else its first row).
    A variant B page has no row of its own: its address is added to that row's review notes."""
    today = build_date or dt.date.today().isoformat()
    brand_rows = [r for r in rows("campaign", fresh=True) if r["brand"].lower() == brand.lower()]
    if not brand_rows:
        raise ValueError(f"No {brand} rows in the Campaign Tracker.")
    row = next((r for r in brand_rows if r["variant"].upper().startswith("A")), brand_rows[0])
    if variant.upper().startswith("B"):
        line = f"B without video: {live_url}"
        if live_url in row["notes"]:
            return row
        return update("campaign", row["rid"], {"notes": (row["notes"] + " " + line).strip()}, "deploy script")
    ch = {"variant": "A: With video", "build_owner": owner, "build_date": today, "deploy_owner": owner, "deploy_status": "Deployed", "live_url": live_url,
          "deploy_date": today}
    if notes is not None:
        ch["notes"] = notes
    return update("campaign", row["rid"], ch, "deploy script")


def sheet_url():
    s = SOURCES[DEFAULT]
    return f"https://docs.google.com/spreadsheets/d/{s['id']}/edit#gid={s['gid']}"


# ------------------------------------------------------------------ page data

def payload(src, fresh=False):
    recs = rows(src, fresh)
    return {"ok": True, "src": src, "label": SOURCES[src]["label"], "editable": sorted(EDITABLE[src]), "options": OPTIONS, "rows": recs, "status": status(),
            "fetched": time.strftime("%H:%M:%S")}
