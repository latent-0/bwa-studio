"""Priority board data: one card per brand, grouped by stage, ranked by a priority number, with a history of every change.
Stages: the first five are a workflow the team can move cards through (a manual choice is stored as an override). Live and Paused come from the
real publish state and cannot be dragged. A card with no override sits in the stage its checks have earned.
Saved in two places that stay in step: the studio database (meta keys, events) and the Campaign Tracker Google Sheet ("Brand Priority" tab for rank and
stage, "Board History" tab as a log), written through the Sheet bridge. On read the Sheet wins when its tab has values."""
import csv
import io
import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request

import core
import integrations
import lp
import store

STAGES = ["Draft", "Generated", "Legal review", "Ready to test", "Ready to launch", "Live", "Paused"]
MOVABLE = STAGES[:5]
STAGE_HINT = {
    "Draft": "No page yet",
    "Generated": "Page built, legal not cleared",
    "Legal review": "Waiting on counsel sign off",
    "Ready to test": "Everything but the test delivery",
    "Ready to launch": "All seven checks pass",
    "Live": "Published. Set by publishing",
    "Paused": "Taken offline. Set by publishing",
}
K_ORDER, K_STAGE, K_SEEN = "brand_priority", "brand_stage", "brand_stage_seen"
TAB = "Brand Priority"
_lock = threading.Lock()
_cache = {"t": 0, "rows": None}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _get(key, default):
    r = store.q("select value from meta where key=?", (key,))
    try:
        return json.loads(r[0]["value"]) if r else default
    except Exception:
        return default


def _set(key, obj):
    store.x("insert or replace into meta(key,value) values(?,?)", (key, json.dumps(obj)))


def _sheet_rows(fresh=False):
    """Rows of the Brand Priority tab as dicts {name, num, stage}. stage is None when the tab has no Stage column. [] when the tab is missing."""
    if os.environ.get("BOARD_SHEET") == "off":  # local testing without touching the Sheet
        return []
    with _lock:
        if not fresh and _cache["rows"] is not None and time.time() - _cache["t"] < lp.TTL:
            return _cache["rows"]
    out = []
    try:
        u = f"https://docs.google.com/spreadsheets/d/{lp.SOURCES['campaign']['id']}/gviz/tq?tqx=out:csv&headers=0&sheet=" + urllib.parse.quote(TAB)
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=15) as r:
            text = r.read().decode("utf-8-sig")
        data = list(csv.reader(io.StringIO(text)))
        head = [h.strip().lower() for h in data[0]] if data else []
        if head and head[0] == "brand":
            ci = head.index("stage") if "stage" in head else None
            for row in data[1:]:
                if len(row) > 1 and row[0].strip():
                    try:
                        num = float(row[1])
                    except ValueError:
                        continue
                    out.append({"name": row[0].strip(), "num": num, "stage": (row[ci].strip() if ci is not None and len(row) > ci else None)})
    except Exception:
        out = []
    with _lock:
        _cache.update(t=time.time(), rows=out)
    return out


def order(brands, fresh=False, srows=None):
    """Slugs from highest priority to lowest. Sheet numbers first, then the saved order, then the roster order for anything new."""
    slugs = [b["slug"] for b in brands]
    name = {_norm(b["name"]): b["slug"] for b in brands}
    ranked = []
    for r in (srows if srows is not None else _sheet_rows(fresh)):
        s = name.get(_norm(r["name"]))
        if s:
            ranked.append((r["num"], s))
    out = [s for _, s in sorted(ranked, key=lambda x: x[0])] if ranked else [s for s in _get(K_ORDER, []) if s in slugs]
    for s in slugs:
        if s not in out:
            out.append(s)
    return out


def overrides(brands, srows):
    """{slug: stage} the team placed by hand. The Sheet's Stage column wins when the tab has one, else what the studio saved."""
    slugs = {b["slug"] for b in brands}
    if srows and any(r["stage"] is not None for r in srows):
        name = {_norm(b["name"]): b["slug"] for b in brands}
        return {name[_norm(r["name"])]: r["stage"] for r in srows if _norm(r["name"]) in name and r["stage"] in MOVABLE}
    return {s: v for s, v in _get(K_STAGE, {}).items() if s in slugs and v in MOVABLE}


def effective(derived, ov):
    return derived if derived not in MOVABLE else (ov or derived)


def _history_rows(limit=500):
    return store.q("select ts,slug,kind,actor,detail from events where kind like 'board.%' order by id desc limit ?", (limit,))


def _entry(r, names):
    try:
        d = json.loads(r["detail"])
    except Exception:
        d = {}
    return {"ts": r["ts"], "slug": r["slug"], "name": names.get(r["slug"], r["slug"]), "type": r["kind"].split(".", 1)[1], "from": d.get("from"), "to": d.get("to"),
            "mode": d.get("mode", "manual"), "by": r["actor"]}


def history(slug=None, limit=80):
    names = {b["slug"]: b["name"] for b in core.load_brands()}
    rows = [r for r in _history_rows(600) if not slug or r["slug"] == slug]
    return [_entry(r, names) for r in rows[:limit]]


def _log(slug, kind, frm, to, actor, mode="manual"):
    store.log_event(slug, "board." + kind, {"from": frm, "to": to, "mode": mode}, actor)


def _bridge(order_slugs, brands, ov, actor, entries):
    name = {b["slug"]: b["name"] for b in brands}
    try:
        lp._call({"action": "priority", "rows": [[name[s], i + 1, ov.get(s, "")] for i, s in enumerate(order_slugs)], "by": actor})
        if entries:
            lp._call({"action": "log", "rows": entries})
        return True
    except RuntimeError as ex:
        return str(ex)
    except Exception:
        return "the Sheet could not be reached, so the change is saved here only"


def save(new_order, brands, actor="studio", move=None):
    """Store a new priority order and optionally a stage move {slug, to}. Returns {order, sheet: True or the error text}."""
    slugs = [b["slug"] for b in brands]
    if sorted(new_order) != sorted(slugs):
        raise ValueError("The board changed while you were dragging. Refresh and try again.")
    name = {b["slug"]: b["name"] for b in brands}
    srows = _sheet_rows(True)
    old_order = order(brands, srows=srows)
    ov = overrides(brands, srows)
    entries = []
    now = store.now()
    slug = (move or {}).get("slug")
    if move:
        to = move.get("to")
        if slug not in slugs or to not in STAGES:
            raise ValueError("Unknown card or column.")
        derived = integrations.desired_stage(slug)
        before = effective(derived, ov.get(slug))
        if to != before:
            if to not in MOVABLE:
                raise ValueError("That column is set by publishing and cannot be dragged to.")
            if derived not in MOVABLE:
                raise ValueError(f"{name[slug]} is {derived.lower()}. Use publish or pause to change that.")
            if to == derived:
                ov.pop(slug, None)
            else:
                ov[slug] = to
        if to != before:
            _log(slug, "stage", before, to, actor)
            entries.append([now, name[slug], "Stage", before, to, actor])
    if slug:
        old_rank, new_rank = old_order.index(slug) + 1, new_order.index(slug) + 1
        if old_rank != new_rank:
            _log(slug, "rank", old_rank, new_rank, actor)
            entries.append([now, name[slug], "Priority", f"#{old_rank}", f"#{new_rank}", actor])
    elif old_order != new_order:  # reorder only (keyboard): log the card that moved most
        moved = max(slugs, key=lambda s: abs(old_order.index(s) - new_order.index(s)))
        if old_order.index(moved) != new_order.index(moved):
            _log(moved, "rank", old_order.index(moved) + 1, new_order.index(moved) + 1, actor)
            entries.append([now, name[moved], "Priority", f"#{old_order.index(moved) + 1}", f"#{new_order.index(moved) + 1}", actor])
    _set(K_ORDER, new_order)
    _set(K_STAGE, ov)
    if slug and move:
        seen = _get(K_SEEN, {})
        seen[slug] = move["to"]
        _set(K_SEEN, seen)
    res = _bridge(new_order, brands, ov, actor, entries)
    with _lock:
        _cache.update(t=0, rows=None)
    return {"order": new_order, "sheet": res}


def _track_changes(brands, stages, derived, ov, hist):
    """Log a history line when a card's stage changed without a drag: its checks moved it, or someone edited the Sheet. Skips duplicates."""
    seen = _get(K_SEEN, {})
    changed = False
    last = {}
    for r in hist:
        if r["kind"] == "board.stage" and r["slug"] not in last:
            last[r["slug"]] = r
    for b in brands:
        s, now_stage = b["slug"], stages[b["slug"]]
        if s in seen and seen[s] != now_stage:
            dup = False
            if s in last:
                try:
                    d = json.loads(last[s]["detail"])
                    dup = d.get("to") == now_stage and d.get("from") == seen[s]
                except Exception:
                    pass
            if not dup:
                by_sheet = ov.get(s) == now_stage and derived[s] != now_stage
                _log(s, "stage", seen[s], now_stage, "the Sheet" if by_sheet else "its checks", "sheet" if by_sheet else "checks")
        if seen.get(s) != now_stage:
            seen[s] = now_stage
            changed = True
    if changed:
        _set(K_SEEN, seen)


def payload(fresh=False):
    brands = core.load_brands()
    srows = _sheet_rows(fresh)
    rank = {s: i + 1 for i, s in enumerate(order(brands, srows=srows))}
    ov = overrides(brands, srows)
    derived = {b["slug"]: integrations.desired_stage(b["slug"]) for b in brands}
    stages = {s: effective(derived[s], ov.get(s)) for s in derived}
    hist = _history_rows(600)
    try:
        _track_changes(brands, stages, derived, ov, hist)
        hist = _history_rows(600)
    except Exception:
        pass
    names = {b["slug"]: b["name"] for b in brands}
    last = {}
    for r in hist:
        if r["kind"] == "board.stage" and r["slug"] not in last:
            last[r["slug"]] = _entry(r, names)
    cards, total_ok, total = [], 0, 0
    for b in brands:
        s = b["slug"]
        cl = core.checklist(s)
        checks = [{"label": i["label"], "ok": i["ok"], "detail": i["detail"]} for i in cl["items"]]
        ok = sum(1 for c in checks if c["ok"])
        total_ok, total = total_ok + ok, total + len(checks)
        nxt = next((c for c in checks if not c["ok"]), None)
        lm = last.get(s)
        cards.append({"slug": s, "name": b["name"], "vertical": (b["vertical"] or "").replace("-", " "), "delivery": cl["delivery"], "stage": stages[s],
                      "derived": derived[s], "manual": stages[s] != derived[s], "locked": derived[s] not in MOVABLE, "priority": rank[s], "checks": checks, "passed": ok,
                      "next": (nxt["label"] + ": " + nxt["detail"]) if nxt else "Ready to go live",
                      "moved": ({"ts": lm["ts"], "from": lm["from"], "to": lm["to"], "by": lm["by"]} if lm else None)})
    cards.sort(key=lambda c: c["priority"])
    by = {st: sum(1 for c in cards if c["stage"] == st) for st in STAGES}
    k = {"brands": len(cards), "ready": by["Ready to launch"], "live": by["Live"], "review": by["Legal review"] + by["Ready to test"],
         "draft": by["Draft"] + by["Generated"], "checks_pct": round(100 * total_ok / total) if total else 0, "checks_ok": total_ok, "checks_total": total}
    return {"ok": True, "stages": STAGES, "movable": MOVABLE, "hints": STAGE_HINT, "cards": cards, "kpis": k, "bridge": lp.bridge_ready(), "sheet_tab": lp.sheet_url(),
            "now": store.now(), "fetched": time.strftime("%H:%M:%S")}
