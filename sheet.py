"""Google Sheet as the control panel. Reads each tab straight from the Sheet (link-readable, no login) with retries, a short
in-memory cache and a last-good snapshot on disk so the studio keeps working if Google is unreachable.
The Sheet is read-only from here: studio-owned fields (phone, colors, legal flags) live in brands.csv, Sheet-owned fields win."""
import csv
import io
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

import paths  # noqa: E402

DATA = paths.ROOT / "data" / "sheet"
SHEET_ID = os.environ.get("SHEET_ID", "1fEyGyaHCQC5qyJM-txPreJTAElJW_bauqukxG9kwJyQ")
TTL = int(os.environ.get("SHEET_TTL", "120"))

TABS = {"urls": "URLs/Brands", "ringba": "Ringba", "priority": "Priority List", "inventory": "Inventory Draft", "temp": "Temp Ringba API",
        "videos": "HSL_videos", "video_urls": "Video on URL", "production": "Production List A-Z", "vm": "VM Recordings", "hsl_states": "HSL Video Tracker "}

_cache, _lock, _state = {}, threading.Lock(), {"source": "not loaded", "error": ""}


def _snap(tab):
    return DATA / (re.sub(r"[^A-Za-z0-9]+", "_", tab.strip()).strip("_") + ".csv")


def _fetch(tab):
    u = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&headers=0&sheet=" + urllib.parse.quote(tab)
    last = None
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as r:
                return r.read().decode("utf-8-sig")
        except Exception as ex:
            last = ex
            time.sleep(0.6 * (i + 1))
    raise last


def rows(key, fresh=False):
    """All rows of a tab as lists of strings. Falls back to the on-disk snapshot when Google is unreachable."""
    tab = TABS.get(key, key)
    with _lock:
        hit = _cache.get(tab)
        if hit and not fresh and time.time() - hit[0] < TTL:
            return hit[1]
    try:
        text = _fetch(tab)
        DATA.mkdir(parents=True, exist_ok=True)
        _snap(tab).write_text(text, encoding="utf-8")
        _state.update(source="Google Sheet (live)", error="")
    except Exception as ex:
        f = _snap(tab)
        if not f.exists():
            _state.update(source="unavailable", error=str(ex)[:120])
            return []
        text = f.read_text(encoding="utf-8")
        _state.update(source="Google Sheet (cached, fetch failed)", error=str(ex)[:120])
    data = list(csv.reader(io.StringIO(text)))
    with _lock:
        _cache[tab] = (time.time(), data)
    return data


def records(key, header_row=0, fresh=False):
    """Rows as dicts keyed by the header row. Blank columns are dropped."""
    data = rows(key, fresh)
    if len(data) <= header_row:
        return []
    head = [h.strip() for h in data[header_row]]
    out = []
    for r in data[header_row + 1:]:
        if any(c.strip() for c in r):
            out.append({head[i]: r[i].strip() for i in range(min(len(head), len(r))) if head[i]})
    return out


def status():
    return dict(_state)


def sheet_url():
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"


# ------------------------------------------------------------------ roster

VERTICALS = [("home security", "home-security"), ("final expense", "final-expense"), ("addiction", "addiction"), ("legal", "legal"), ("debt", "debt"), ("flight", "flights"), ("home", "home"),
             ("loan", "loans"), ("refinanc", "loans"), ("mortgage", "loans"), ("medicare", "medicare"), ("insurance", "insurance"), ("aca", "insurance"), ("all verticals", "insurance")]


def vertical_key(text):
    t = (text or "").lower()
    for needle, key in VERTICALS:
        if needle in t:
            return key
    return "insurance"


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")


def norm(name):
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _uniq(text):
    """Drops repeated values in a multi-line cell, keeping order."""
    seen, out = set(), []
    for part in re.split(r"[\n;]", text or ""):
        p = part.strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return "; ".join(out)


def _url(u):
    u = (u or "").strip().split(" and ")[0].strip()
    if not u or " " in u or "." not in u:
        return ""
    return u if u.startswith("http") else "https://" + u


def _host(u):
    u = (u or "").lower()
    u = re.sub(r"^https?://", "", u).split("/")[0]
    return u[4:] if u.startswith("www.") else u


DELIVERY_WORDS = (("inbound call", "calls"), ("transfer", "calls"), ("call", "calls"), ("data lead", "leads"), ("lead", "leads"), ("click", "clicks"))


def delivery_from(text):
    """Map the Sheet's Type column to studio delivery modes (calls, clicks, leads). Empty when the Sheet does not say."""
    found = []
    t = (text or "").lower()
    for word, mode in DELIVERY_WORDS:
        if word in t and mode not in found:
            found.append(mode)
    return ",".join(found)


PRIORITY_MARK = {"*": "High", "done": "Done"}


def _roster(fresh=False):
    """Brands from the Sheet in Priority List order. Merges Priority List, URLs/Brands, Ringba and Inventory Draft; brands that share a
    website are one brand (EZ Loan and Easy Loan Center). Names prefer URLs/Brands, then Ringba, then Priority List."""
    by = {}

    def ent(name, src):
        k = norm(name)
        if k not in by:
            by[k] = {"names": {}, "order": 999, "priority": "", "url": "", "vertical_text": "", "buyers": "", "category": "", "type": "", "note": "",
                     "ghl_subaccount": "", "ghl_website": "", "site_up": "", "campaigns": [], "sources": [], "inv_urls": []}
        by[k]["names"][src] = name.strip()
        if src not in by[k]["sources"]:
            by[k]["sources"].append(src)
        return by[k]

    for i, r in enumerate(rows("priority", fresh)[1:]):
        if r and r[0].strip():
            b = ent(r[0], "Priority List")
            b["order"] = i
            mark = (r[1].strip() if len(r) > 1 else "")
            b["priority"] = PRIORITY_MARK.get(mark.lower(), mark)
    for r in records("urls", fresh=fresh):
        if not r.get("URL"):
            break  # the tab continues with a lookup table below the brand list
        if r.get("Brand"):
            first = "URLs/Brands" not in by.get(norm(r["Brand"]), {}).get("sources", [])
            b = ent(r["Brand"], "URLs/Brands")
            vals = dict(url=_url(r.get("URL")), vertical_text=r.get("Vertical", ""), buyers=_uniq(r.get("Buyers", "")),
                        category=_uniq(r.get("Category", "")), type=_uniq(r.get("Type", "")), note=r.get("Note", ""),
                        ghl_subaccount=r.get("GHL Sub-Account", ""), ghl_website=r.get("GHL Website", ""), site_up=r.get("Website Up?", ""))
            b.update(vals if first else {k: (b[k] or v) for k, v in vals.items()})
    data = rows("ringba", fresh)
    head_i = next((i for i, r in enumerate(data) if "Brand" in [c.strip() for c in r]), None)
    if head_i is not None:
        head = [c.strip() for c in data[head_i]]
        for r in data[head_i + 1:]:
            d = {head[i]: r[i].strip() for i in range(min(len(head), len(r))) if head[i]}
            if d.get("Brand"):
                b = ent(d["Brand"], "Ringba")
                b["url"] = b["url"] or _url(d.get("URL"))
                b["vertical_text"] = b["vertical_text"] or d.get("Vertical", "")
    for r in records("inventory", fresh=fresh):
        name = r.get("Brand", "")
        if not name:
            continue
        b = by.get(norm(name))
        if b is None:
            continue  # inventory-only labels such as "Financial" or "Miscelaneous" are not brands
        b["sources"].append("Inventory Draft") if "Inventory Draft" not in b["sources"] else None
        lp = _url(r.get("Landing Page URL (call-only variant)", ""))
        b["inv_urls"].append(lp)
        b["campaigns"].append({"campaign": r.get("Campaign", ""), "stage": r.get("Production Stages", ""), "video": r.get("Final Video", ""), "landing_page": lp,
                               "pool": r.get("Ringba Number Pool API Setup?", ""), "ready": r.get("Campaign Ready = LP w/VID + Ringba) Y/N", ""),
                               "new_lp": r.get("New Landing Page", ""), "lp_production": r.get("Updated Landing Page Production", ""),
                               "lp_review": r.get("Updated Landing Page Review Link", ""), "feedback": r.get("Jeff landing page feedback", "")})
    for b in by.values():
        b["url"] = b["url"] or next((u for u in b["inv_urls"] if u), "")

    # one brand per website
    merged, by_host = [], {}
    for b in sorted(by.values(), key=lambda b: b["order"]):
        h = _host(b["url"])
        if h and h in by_host:
            t = by_host[h]
            t["names"].update({k: v for k, v in b["names"].items() if k not in t["names"]})
            t["sources"] += [s for s in b["sources"] if s not in t["sources"]]
            t["campaigns"] += b["campaigns"]
            for f in ("buyers", "category", "type", "note", "ghl_subaccount", "ghl_website", "site_up", "vertical_text"):
                t[f] = t[f] or b[f]
            if b["url"] and (not t["url"] or len(b["url"]) < len(t["url"])):
                t["url"] = b["url"]
            t["order"] = min(t["order"], b["order"])
            t["priority"] = t["priority"] or b["priority"]
            continue
        merged.append(b)
        if h:
            by_host[h] = b
    out = []
    for b in merged:
        # the Priority List defines the studio's brands; set SHEET_ALL_BRANDS=1 to also include every other brand that has its own website
        if b["order"] == 999 and not (os.environ.get("SHEET_ALL_BRANDS") and b["url"] and ({"URLs/Brands", "Ringba"} & set(b["sources"]))):
            continue
        name = b["names"].get("URLs/Brands") or b["names"].get("Ringba") or b["names"].get("Priority List") or next(iter(b["names"].values()))
        b["name"], b["slug"] = name, slugify(name)
        b["vertical"] = vertical_key(b["vertical_text"] or b["category"] or name)
        b["delivery"] = delivery_from(b["type"])
        b["buyer_confirmed"] = bool(b["buyers"]) and not re.search(r"pending|confirm|\?", b["buyers"], re.I)
        out.append(b)
    return sorted(out, key=lambda b: (b["order"], b["name"].lower()))


def ringba_pools():
    """Landing page URL -> {campaign, pool} from the Temp Ringba API tab."""
    out = {}
    for r in records("temp"):
        u = r.get("Landing page", "")
        if u:
            out[u.rstrip("/")] = {"campaign": r.get("Campaign Name", ""), "pool": r.get("Ringba pool", "")}
    return out


_roster_cache = [0.0, []]


def roster(fresh=False):
    """Cached for a short time: the studio asks for brands on every page and nav render."""
    if fresh or time.time() - _roster_cache[0] > 30 or not _roster_cache[1]:
        _roster_cache[1] = _roster(fresh)
        _roster_cache[0] = time.time()
    return _roster_cache[1]


def videos(brand_name):
    """Rows of the HSL_videos tab for one brand: idea, stages, final video link and Jeff's notes."""
    data = rows("videos")
    if not data:
        return []
    head = [h.strip() for h in data[0]]
    want = {"idea": "Video Idea", "prep": "Media Preparation Stages", "stage": "Production Stages", "final": "Final Video", "notes": "Notes", "jeff": "Jeff Notes",
            "revision": "New Revision Link", "copyright": "Copyright Submitted", "launched": "internal campaign launched"}
    idx = {k: head.index(v) for k, v in want.items() if v in head}
    out = []
    for r in data[1:]:
        if r and r[0].strip().lower() == brand_name.strip().lower():
            out.append({k: (r[i].strip() if i < len(r) else "") for k, i in idx.items()})
    return out
