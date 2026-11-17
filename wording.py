"""Legal wording review: reviewers edit the visible text of a brand's landing page and its compliance pages inside the studio.

Edits are stored per brand in data/wording/<slug>.json as {original text -> new text}: landing page edits under "edits", compliance page edits
under "pages" -> page key. The page as the generator built it is kept in data/wording/<slug>.base.html (landing page) or
data/wording/<slug>.<page>.base.html, and the served file is always base + edits. After every regenerate the edits are applied again, so a reviewer's
wording survives rebuilds. An edit whose original text no longer appears on the page (the generator wrote something new) is kept and reported
as unmatched, so nothing a reviewer wrote is silently lost."""
import hashlib
import html
import json
import re
import time

import core

DIR = core.DATA / "wording"
_TEXT = re.compile(r">([^<]+)<")
_SKIP = re.compile(r"(?is)<(script|style|svg|head|noscript|template|title)\b[^>]*>.*?</\1\s*>|<p class=\"draft\">.*?</p>")  # the draft notice is the studio's, not copy
_TAG = re.compile(r"<\s*(/?)\s*([a-zA-Z0-9]+)")
LABELS = {"h1": "Headline", "h2": "Heading", "h3": "Heading", "h4": "Heading", "p": "Paragraph", "li": "List item", "a": "Link or button",
          "button": "Button", "summary": "FAQ question", "dt": "Term", "dd": "Answer", "label": "Label", "small": "Small print", "strong": "Emphasis",
          "b": "Emphasis", "em": "Emphasis", "blockquote": "Quote", "figcaption": "Caption", "td": "Table cell", "th": "Table heading"}


def _norm(t):
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def _id(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def _file(slug):
    return DIR / f"{slug}.json"


def pages():
    """Reviewable pages as (key, title, file name). "index" is the landing page."""
    return [("index", "Landing page", "index.html")] + [(k, t, f"{k}.html") for k, t in core.COMPLIANCE_PAGES.items()]


def _check(page):
    if page not in {k for k, _, _ in pages()}:
        raise ValueError("Unknown page.")
    return page


def _base_file(slug, page="index"):
    return DIR / (f"{slug}.base.html" if page == "index" else f"{slug}.{page}.base.html")


def _page_file(slug, page="index"):
    return core.OUT / slug / ("index.html" if page == "index" else f"{page}.html")


def edits_for(d, page="index"):
    """The {original -> edit} map for one page of a loaded record."""
    if page == "index":
        return d["edits"]
    return d.setdefault("pages", {}).setdefault(page, {})


def fingerprint(slug):
    """A short hash of every wording edit on every page. Sign-off stores it; any later edit makes the sign-off stale."""
    d = load(slug)
    body = {"index": {k: v["text"] for k, v in d["edits"].items()}}
    for pg, ed in d.get("pages", {}).items():
        if ed:
            body[pg] = {k: v["text"] for k, v in ed.items()}
    return hashlib.sha1(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


def total_edits(d):
    return len(d["edits"]) + sum(len(v) for v in d.get("pages", {}).values())


def load(slug):
    f = _file(slug)
    try:
        d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except Exception:
        d = {}
    d.setdefault("edits", {})
    return d


def _save(slug, d):
    DIR.mkdir(parents=True, exist_ok=True)
    _file(slug).write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")


_WORDS = re.compile(r'(?:<span class="w" style="--i:\d+">(?:<em>)?[^<]*(?:</em>)?</span>\s*)+')
_WORD = re.compile(r'<span class="w" style="--i:\d+">(<em>)?([^<]*)(?:</em>)?</span>')
_ARIA = re.compile(r'aria-label="([^"]*)"([^>]*)>\s*$')


def _words_html(text, n_em, trail):
    ws = text.split()
    n = min(n_em, len(ws))
    return " ".join(f'<span class="w" style="--i:{k}">' + (f"<em>{html.escape(w, quote=False)}</em>" if n and k >= len(ws) - n else html.escape(w, quote=False)) + "</span>"
                    for k, w in enumerate(ws)) + trail


def _segments(page):
    """Editable units of the page body in page order, as (start, end, text, tag, render). render(new_text) returns what replaces page[start:end].
    Animated headlines (one <span class="w"> per word) are one unit; every other visible text node is its own unit."""
    skip = [(m.start(), m.end()) for m in _SKIP.finditer(page)]
    units = []
    for m in _WORDS.finditer(page):
        ws = _WORD.findall(m.group(0))
        text = _norm(" ".join(w for _, w in ws))
        if not re.search(r"[A-Za-z]{2}", text):
            continue
        n_em = sum(1 for em, _ in ws if em)
        trail = m.group(0)[len(m.group(0).rstrip()):]
        start, end = m.start(), m.end()
        ar = _ARIA.search(page, max(0, start - 600), start)
        if ar:
            # take the attribute too, so screen readers hear the new headline
            a0, a1 = ar.start(1), ar.end(1)
            mid = page[a1:start]
            units.append((a0, end, text, _block_tag(page, start), lambda t, n=n_em, tr=trail, mid=mid: html.escape(t, quote=True) + mid + _words_html(t, n, tr)))
        else:
            units.append((start, end, text, _block_tag(page, start), lambda t, n=n_em, tr=trail: _words_html(t, n, tr)))
    covered = [(u[0], u[1]) for u in units]
    for m in _TEXT.finditer(page):
        st, en = m.start(1), m.end(1)
        if any(a <= st < b for a, b in skip) or any(a <= st < b for a, b in covered):
            continue
        raw = m.group(1)
        if not re.search(r"[A-Za-z]{2}", _norm(raw)):
            continue
        lead = raw[:len(raw) - len(raw.lstrip())]
        trail = raw[len(raw.rstrip()):]
        units.append((st, en, _norm(raw), _block_tag(page, st), lambda t, lead=lead, trail=trail: lead + html.escape(t, quote=False) + trail))
    units.sort(key=lambda u: u[0])
    return units


_INLINE = {"span", "br", "em", "strong", "b", "i", "u", "small", "mark", "sup", "sub", "abbr", "time", "img", "wbr", "s"}


def _block_tag(page, s):
    """The nearest enclosing block element of the text at s, skipping inline wrappers like <span>."""
    lo = max(0, s - 1500)
    tags = list(_TAG.finditer(page, lo, s))
    for t in reversed(tags):
        name = t.group(2).lower()
        if name in _INLINE:
            continue
        if t.group(1):
            return ""
        return name
    return ""


def apply(page, edits):
    if not edits:
        return page
    out, last = [], 0
    for st, en, text, _, render in _segments(page):
        new = edits.get(text)
        if new is None or st < last:
            continue
        out.append(page[last:st])
        out.append(render(new["text"] if isinstance(new, dict) else new))
        last = en
    out.append(page[last:])
    return "".join(out)


def base(slug, page="index"):
    b = _base_file(slug, page)
    if b.exists():
        return b.read_text(encoding="utf-8")
    p = _page_file(slug, page)
    return p.read_text(encoding="utf-8") if p.exists() else None


def after_build(slug, page="index"):
    """Called right after the generator writes a page: keep that as the base, then re-apply the reviewers' edits."""
    p = _page_file(slug, page)
    if not p.exists():
        return
    html_ = p.read_text(encoding="utf-8")
    DIR.mkdir(parents=True, exist_ok=True)
    _base_file(slug, page).write_text(html_, encoding="utf-8")
    edits = edits_for(load(slug), page)
    if edits:
        p.write_text(apply(html_, edits), encoding="utf-8")


def blocks(slug, page="index"):
    html_ = base(slug, _check(page))
    if html_ is None:
        return [], []
    edits = edits_for(load(slug), page)
    seen, out = set(), []
    for _, _, t, tag, _ in _segments(html_):
        if t in seen:
            continue
        seen.add(t)
        ed = edits.get(t)
        out.append({"id": _id(t), "kind": LABELS.get(tag, "Text"), "original": t, "text": ed["text"] if ed else t, "edited": bool(ed),
                    "by": ed.get("by") if ed else None, "ts": ed.get("ts") if ed else None})
    unmatched = [{"original": k, "text": v["text"], "by": v.get("by"), "ts": v.get("ts")} for k, v in edits.items() if k not in seen]
    return out, unmatched


def save(slug, changes, by, page="index"):
    """changes: [{original, text}]. A text equal to the original removes the edit. Returns how many edits changed."""
    html_ = base(slug, _check(page))
    if html_ is None:
        raise ValueError("Generate the page first.")
    d = load(slug)
    edits = edits_for(d, page)
    n, log = 0, []
    for c in changes:
        orig = _norm(c.get("original", ""))
        text = re.sub(r"[ \t]+", " ", str(c.get("text", ""))).strip()
        if not orig:
            continue
        if not text:
            raise ValueError(f'Text cannot be empty: "{orig[:60]}"')
        before = edits.get(orig, {}).get("text", orig)
        if text == orig:
            if orig in edits:
                del edits[orig]
                n += 1
                log.append({"from": before[:600], "to": orig[:600], "restored": True})
        elif before != text:
            edits[orig] = {"text": text, "by": by, "ts": time.strftime("%Y-%m-%d %H:%M")}
            n += 1
            log.append({"from": before[:600], "to": text[:600]})
    if not n:
        return 0
    if not _base_file(slug, page).exists():
        DIR.mkdir(parents=True, exist_ok=True)
        _base_file(slug, page).write_text(html_, encoding="utf-8")
    _save(slug, d)
    _page_file(slug, page).write_text(apply(html_, edits), encoding="utf-8")
    import store
    title = dict((k, t) for k, t, _ in pages())[page]
    store.log_event(slug, "legal.wording_edited", {"page": page, "title": title, "changes": log[:40], "count": n}, by)
    return n


def forget(slug, original, by, page="index"):
    """Drop an unmatched edit."""
    d = load(slug)
    if edits_for(d, _check(page)).pop(_norm(original), None) is not None:
        _save(slug, d)
        import store
        title = dict((k, t) for k, t, _ in pages())[page]
        store.log_event(slug, "legal.wording_removed", {"page": page, "title": title, "original": original[:600]}, by)


def flags_by_block(slug, blks):
    """Attach the compliance scanner's flagged claims to the text blocks they come from."""
    import compliance
    hits = compliance.scan(slug)
    used = set()
    for b in blks:
        low = b["text"].lower()
        b["flags"] = []
        for h in hits:
            ctx = h["context"].lower()
            if h["phrase"].lower() in low and (low in ctx or ctx in low or low[:60] in ctx or ctx[:60] in low):
                b["flags"].append(h)
                used.add(h["id"])
    return [h for h in hits if h["id"] not in used]
