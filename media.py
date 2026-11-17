"""Media library: every asset link the Sheet tracks for a brand (final videos, scripts, voiceovers, green screens, revisions, creatives and
video-ads folders, media and offer kits, landing page drafts). Many are hyperlinked text, so the URLs come from the Sheet's xlsx export.
Assets stay in Google Drive until you pick one: only then does the studio download it, into assets/<brand>/media/. Access is checked
on demand because Drive files can be public, private or deleted."""
import io
import json
import re
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

import core
import sheet

import paths  # noqa: E402

ROOT = paths.ROOT
SNAP = ROOT / "data" / "sheet" / "sheet.xlsx"
CATALOG = ROOT / "data" / "sheet" / "media.json"
TTL = 900
MAX_BYTES = 800 * 1024 * 1024

# (tab, column letter, kind, label)
VIDEO_COLS = [("C", "script", "Script"), ("D", "voiceover", "Voiceover"), ("E", "angle", "Alternate angle"), ("F", "greenscreen", "Green screen"),
              ("I", "instructions", "Instructions folder"), ("J", "final", "Final video"), ("N", "revision", "New revision"), ("P", "revision", "Revision 3"),
              ("R", "revision", "Revision 4"), ("S", "folder", "Final video folder"), ("U", "landing", "Landing page draft")]
INV_COLS = [("D", "final", "Final video"), ("L", "kit", "Media kit"), ("P", "kit", "Offer kit"), ("T", "folder", "Creatives folder"), ("U", "folder", "Video ads folder"),
            ("V", "landing", "New landing page"), ("X", "landing", "Landing page review")]
KIND_ORDER = ["final", "revision", "greenscreen", "angle", "voiceover", "script", "instructions", "folder", "kit", "landing"]
KIND_LABEL = {"final": "Final videos", "revision": "Revisions", "greenscreen": "Green screens", "angle": "Alternate angles", "voiceover": "Voiceovers", "script": "Scripts",
              "instructions": "Instruction folders", "folder": "Creative and video folders", "kit": "Media and offer kits", "landing": "Landing pages"}

_mem = {"t": 0.0, "data": None}
_lock = threading.Lock()


def _drive_id(url):
    m = re.search(r"/(?:file|document|presentation|spreadsheets)/d/([\w-]+)", url) or re.search(r"/folders/([\w-]+)", url) or re.search(r"[?&]id=([\w-]+)", url)
    return m.group(1) if m else ""


def _type(url):
    if "/folders/" in url:
        return "folder"
    if "/file/d/" in url:
        return "file"
    if "docs.google.com/document" in url:
        return "doc"
    if "docs.google.com/spreadsheets" in url:
        return "sheet"
    if "docs.google.com/presentation" in url:
        return "slides"
    return "link"


def _download_xlsx():
    u = f"https://docs.google.com/spreadsheets/d/{sheet.SHEET_ID}/export?format=xlsx"
    last = None
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                return r.read()
        except Exception as ex:
            last = ex
            time.sleep(0.8 * (i + 1))
    raise last


def _parse(raw):
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(raw))
    assets = []

    def harvest(tab, cols, brand_col, idea_col, stage_col):
        if tab not in wb.sheetnames:
            return
        ws = wb[tab]
        for row in ws.iter_rows(min_row=2):
            cells = {c.column_letter: c for c in row}
            brand = str(getattr(cells.get(brand_col), "value", "") or "").strip()
            if not brand:
                continue
            idea = str(getattr(cells.get(idea_col), "value", "") or "").strip()
            stage = str(getattr(cells.get(stage_col), "value", "") or "").strip()
            for col, kind, label in cols:
                c = cells.get(col)
                if c is None:
                    continue
                url = (c.hyperlink.target if c.hyperlink and c.hyperlink.target else "")
                if not url and isinstance(c.value, str) and c.value.startswith("http"):
                    url = c.value.strip()
                if not url:
                    continue
                shown = str(c.value or "").strip()
                title = shown if shown and not shown.startswith("http") else (idea or label)
                assets.append({"brand": brand, "kind": kind, "label": label, "title": title[:120], "context": idea[:120], "stage": stage[:40], "url": url,
                               "drive_id": _drive_id(url), "type": _type(url), "tab": tab, "row": row[0].row})

    harvest("HSL_videos", VIDEO_COLS, "A", "B", "H")
    harvest("Inventory Draft", INV_COLS, "A", "B", "C")
    seen, out = set(), []
    for a in assets:  # the same file is often listed on several rows
        k = (a["brand"], a["kind"], a["drive_id"] or a["url"])
        if k not in seen:
            seen.add(k)
            out.append(a)
    return out


def catalog(fresh=False):
    """All assets from the Sheet. Cached in memory and on disk; falls back to the last snapshot if Google is unreachable."""
    with _lock:
        if _mem["data"] is not None and not fresh and time.time() - _mem["t"] < TTL:
            return _mem["data"]
    try:
        data = _parse(_download_xlsx())
        CATALOG.parent.mkdir(parents=True, exist_ok=True)
        CATALOG.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        data = json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.exists() else []
    with _lock:
        _mem.update(t=time.time(), data=data)
    return data


def _squash(text):
    """Comparable form of a brand label: lowercase letters and digits, no plural s, HSL spelled out."""
    t = sheet.norm(text)
    t = "homeservicelive" if t == "hsl" else t
    return t.replace("s", "")


def _names(slug):
    info = core.sheet_info(slug) or {}
    return {_squash(n) for n in (info.get("names") or {}).values()} | {_squash(core.get_brand(slug)["name"])}


def _belongs(asset_brand, names):
    n = _squash(asset_brand)
    return n in names or any(len(x) >= 8 and n.startswith(x) for x in names)  # "First Legal Ozempic" belongs to First Legal


def for_brand(slug):
    """Assets that belong to a brand, grouped by kind, in the order that matters for production."""
    names = _names(slug)
    mine = [dict(a, id=f"{a['tab'][:3].lower()}{a['row']}-{a['kind']}-{i}") for i, a in enumerate(a for a in catalog() if _belongs(a["brand"], names))]
    groups = []
    for kind in KIND_ORDER:
        items = [a for a in mine if a["kind"] == kind]
        if items:
            groups.append({"kind": kind, "label": KIND_LABEL[kind], "items": items})
    return {"total": len(mine), "groups": groups}


def counts():
    """Asset count per brand slug, for the launch board."""
    cat = catalog()
    return {b["slug"]: sum(1 for a in cat if _belongs(a["brand"], _names(b["slug"]))) for b in core.load_brands()}


# ------------------------------------------------------------------ access and download

def _open(url, rng=None):
    h = {"User-Agent": "Mozilla/5.0"}
    if rng:
        h["Range"] = rng
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30)


def check(drive_id, kind="file"):
    """'public', 'private' or 'missing' for one Drive file, reading only the first bytes. Folders and docs are checked on their view page."""
    if not drive_id:
        return {"access": "unknown"}
    try:
        with _open(f"https://drive.usercontent.google.com/download?id={drive_id}&export=download&confirm=t", "bytes=0-1023") as r:
            ct = r.headers.get("content-type", "")
            total = r.headers.get("content-range", "").split("/")[-1] or r.headers.get("content-length", "")
            head = r.read(1024)
            if "html" in ct:
                low = head.decode("utf-8", "ignore").lower()
                if "sign in" in low or "accounts.google.com" in low or "access" in low:
                    return {"access": "private"}
                return {"access": "private"}
            return {"access": "public", "mime": ct.split(";")[0], "size": int(total) if str(total).isdigit() else None}
    except urllib.error.HTTPError as ex:
        if ex.code != 404:
            return {"access": "private", "code": ex.code}
        # the download endpoint answers 404 for restricted files too, so ask the view page: 404 there means removed, 403 means private
        try:
            with _open(f"https://drive.google.com/file/d/{drive_id}/view") as r:
                return {"access": "private", "code": r.status}
        except urllib.error.HTTPError as ex2:
            return {"access": "missing" if ex2.code == 404 else "private", "code": ex2.code}
        except Exception:
            return {"access": "unknown"}
    except Exception as ex:
        return {"access": "unknown", "error": str(ex)[:80]}


_dl = {}


def local_path(slug, asset_id):
    d = core.ASSETS / slug / "media"
    for f in d.glob(f"{asset_id}.*") if d.exists() else []:
        return f
    return None


def download(slug, asset):
    """Start downloading one public Drive file into assets/<slug>/media/. Returns immediately; poll progress(). Refuses files over the size cap."""
    key = (slug, asset["id"])
    if _dl.get(key, {}).get("state") == "running":
        return _dl[key]
    _dl[key] = {"state": "running", "bytes": 0, "total": None, "error": ""}

    def work():
        st = _dl[key]
        try:
            did = asset["drive_id"]
            url = f"https://drive.usercontent.google.com/download?id={did}&export=download&confirm=t"
            with _open(url) as r:
                ct = r.headers.get("content-type", "")
                if "html" in ct:
                    raise ValueError("Drive did not allow the download. The file is private or has been removed.")
                st["total"] = int(r.headers.get("content-length") or 0) or None
                if st["total"] and st["total"] > MAX_BYTES:
                    raise ValueError(f"File is {st['total'] // 1048576} MB, over the {MAX_BYTES // 1048576} MB limit.")
                ext = {"video/mp4": ".mp4", "video/quicktime": ".mov", "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav", "application/pdf": ".pdf",
                       "image/jpeg": ".jpg", "image/png": ".png", "video/webm": ".webm"}.get(ct.split(";")[0], ".bin")
                d = core.ASSETS / slug / "media"
                d.mkdir(parents=True, exist_ok=True)
                tmp = d / f"{asset['id']}.part"
                with open(tmp, "wb") as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        st["bytes"] += len(chunk)
                        if st["bytes"] > MAX_BYTES:
                            raise ValueError("File is over the size limit.")
                        f.write(chunk)
                tmp.rename(d / f"{asset['id']}{ext}")
                (d / f"{asset['id']}.json").write_text(json.dumps({k: asset[k] for k in ("title", "kind", "label", "url", "brand")}), encoding="utf-8")
            st["state"] = "done"
        except Exception as ex:
            st.update(state="failed", error=str(ex)[:200])
            try:
                (core.ASSETS / slug / "media" / f"{asset['id']}.part").unlink()
            except Exception:
                pass

    threading.Thread(target=work, daemon=True).start()
    return _dl[key]


def progress(slug, asset_id):
    st = dict(_dl.get((slug, asset_id), {"state": "idle"}))
    p = local_path(slug, asset_id)
    if p and st.get("state") != "running":
        st.update(state="done", file=p.name, size=p.stat().st_size)
    return st


def library(slug):
    """Files already downloaded for a brand."""
    d = core.ASSETS / slug / "media"
    out = []
    for f in sorted(d.glob("*")) if d.exists() else []:
        if f.suffix not in (".json", ".part"):
            meta = {}
            try:
                meta = json.loads((d / f"{f.stem}.json").read_text(encoding="utf-8"))
            except Exception:
                pass
            out.append({"id": f.stem, "file": f.name, "size": f.stat().st_size, "title": meta.get("title", f.name), "kind": meta.get("kind", "")})
    return out
