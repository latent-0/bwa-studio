"""Pitch-driven landing page: builds a full site from the sales pitch read off a reference image
(data/pitch/<slug>.json). CSS, icon sprite and scripts live in pitch_assets.py."""
import html
import re
import time
import urllib.parse

from pitch_assets import CSS, SCRIPT_JS, SPRITE
from template import FONTS

e = html.escape
ICONS_REASON = ["person", "plane", "search", "dollar", "clock", "share", "check"]
# who the brand connects people with, for the footer; the page template started life as a flights page, so anything flight-specific is gated on the vertical
PARTNERS = {"flights": "licensed travel professionals and partners", "insurance": "licensed insurance agents and partners", "final-expense": "licensed insurance agents and partners",
            "medicare": "licensed insurance agents and partners", "debt": "debt relief providers and partners", "legal": "law firms and partners", "loans": "lenders and partners",
            "home": "home service providers and partners", "home-security": "home security providers and partners", "pest": "home service providers and partners",
            "addiction": "treatment providers and partners"}
ICONS_STEP = ["chat", "search", "list", "cal", "heart"]
EXTRA_CSS = (".hours{display:flex;align-items:center;gap:10px;margin:22px 0 0;color:var(--mut);font-size:15px}"
             ".hours .i{font-size:18px;color:var(--a)}"
             # hero upgrade: branded still with a slow push-in (variant B), floating branded image card, watch-the-video button and player
             ".still{position:absolute;inset:0;overflow:hidden}.still img{width:100%;height:100%;object-fit:cover;display:block;transform-origin:60% 45%;animation:kb 18s ease-in-out infinite alternate}"
             "@keyframes kb{from{transform:scale(1.02)}to{transform:scale(1.14) translate(-1.5%,-1%)}}"
             ".vid:after{content:\"\";position:absolute;inset:0;pointer-events:none;background:linear-gradient(180deg,transparent 55%,rgba(7,12,24,.32));z-index:1}"
             ".ovl{position:absolute;z-index:5;right:-26px;bottom:-34px;width:36%;max-width:230px;margin:0;border-radius:16px;overflow:hidden;border:4px solid #fff;"
             "box-shadow:0 24px 50px rgba(7,23,63,.3);animation:float 7s ease-in-out infinite;animation-delay:-1.5s;aspect-ratio:4/3.1;background:var(--canvas2)}"
             ".ovl img{width:100%;height:100%;object-fit:cover;display:block}"
             ".watch{position:absolute;z-index:6;left:22px;top:22px;display:inline-flex;align-items:center;gap:10px;min-height:44px;padding:0 18px 0 14px;border:0;border-radius:999px;"
             "background:rgba(10,14,24,.62);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);color:#fff;font:500 14px/1 var(--fb);cursor:pointer;transition:background .3s var(--ease),transform .3s var(--ease)}"
             ".watch:hover{background:var(--a);transform:translateY(-2px)}.watch:focus-visible,.vclose:focus-visible{outline:3px solid #fff;outline-offset:3px}"
             ".watch svg{width:16px;height:16px;fill:currentColor}"
             ".vmodal{padding:0;border:0;background:#000;border-radius:16px;width:min(960px,94vw);max-height:90vh;overflow:visible;box-shadow:0 40px 100px rgba(0,0,0,.5)}"
             ".vmodal::backdrop{background:rgba(5,8,16,.78);-webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px)}"
             ".vmodal video{display:block;width:100%;max-height:86vh;border-radius:16px;background:#000}"
             ".vclose{position:absolute;top:-16px;right:-16px;width:44px;height:44px;border-radius:50%;border:0;background:#fff;color:#101828;font:400 28px/1 var(--fb);cursor:pointer;z-index:2;box-shadow:0 8px 20px rgba(0,0,0,.3)}"
             "@media(max-width:980px){.ovl{right:10px;bottom:-24px;width:34%}}"
             "@media(max-width:640px){.media.has-ovl .chip{display:none}.ovl{width:38%;bottom:-18px;border-width:3px;border-radius:12px}.watch{left:12px;top:12px;font-size:13px;padding:0 14px 0 12px}.vclose{top:8px;right:8px}}"
             "@media(prefers-reduced-motion:reduce){.still img,.ovl{animation:none!important}}")


def _i(name, cls="i"):
    return f'<svg class="{cls}"><use href="#i-{name}"/></svg>'


def _words(text, n):
    ws = text.split()
    out = []
    for k, w in enumerate(ws):
        inner = f"<em>{e(w)}</em>" if n and k >= len(ws) - n else e(w)
        out.append(f'<span class="w" style="--i:{k}">{inner}</span>')
    return " ".join(out)


def build_pitch_page(brand, pitch, ringba, everflow, has_file):
    """has_file(name) -> bool tells whether an asset exists in assets/<slug>/."""
    slug = brand["slug"]
    q = urllib.parse.quote
    digits = re.sub(r"\D", "", brand["phone"])
    tel = "+1" + digits[-10:] if digits else ""
    phone = e(brand["phone"])
    name = e(brand["name"])
    hours = brand.get("hours", "")
    badges = pitch["badges"]
    flights = brand.get("vertical") == "flights"
    lead_icon, arrow_icon = ("plane", "plane") if flights else ("shield", "check")
    icons_reason = ICONS_REASON if flights else ["shield" if i == "plane" else i for i in ICONS_REASON]
    partners = PARTNERS.get(brand.get("vertical"), "participating partners")
    cta = e(pitch["cta"])
    variant_b = brand.get("variant") == "B"  # variant B has no hero video
    # hero upgrade assets (hero_assets.py): a short branded loop, a branded still for variant B, a second branded image for the overlay card
    has_loop, has_still, has_ovl = has_file("hero-loop.mp4"), has_file("hero-still.jpg"), has_file("overlay.jpg")
    solo = variant_b and not has_still  # with no branded still, variant B's text takes the full width

    def num():
        return f'<span class="ringba-number">{phone}</span>'

    css = CSS.replace("--a:#0b5ed7;--p:#0a2a6b;", f"--a:{brand['accent_color'] or '#0b5ed7'};--p:{brand['primary_color'] or '#0a2a6b'};")
    css = css.replace("--night:#07173f;", "--night:#07173f;--night:color-mix(in srgb,var(--p) 76%,#07090d);") + EXTRA_CSS

    full = brand.get("hero_video") if brand.get("hero_video") and has_file(brand["hero_video"]) else ("hero.mp4" if not variant_b and has_file("hero.mp4") else "")
    watch = ""
    if variant_b and has_still:
        # no video on variant B: the branded still with a slow push-in
        media = f'<div class="still"><img src="/assets/{slug}/hero-still.jpg" alt="{name}" fetchpriority="high"></div>'
    elif has_loop:
        # Flight Finder Pro model: a few seconds of branded footage on a silent loop; the full spokesperson video plays on request with sound
        media = (f'<video id="v" autoplay muted loop playsinline preload="auto"' + (f' poster="/assets/{slug}/hero-still.jpg"' if has_still else "")
                 + f'><source src="/assets/{slug}/hero-loop.mp4" type="video/mp4"></video>'
                 + (f'<div class="fallback" id="vfb" style="background:#0b0f1a url(/assets/{slug}/hero-still.jpg) center/cover no-repeat"></div>' if has_still
                    else f'<div class="fallback" id="vfb"><div>{_i(lead_icon)}{name}</div></div>')
                 + f'<button class="play" id="play" aria-label="Play video"><svg viewBox="0 0 24 24"><path d="M7 4.5v15l13-7.5z"/></svg></button>')
        if full:
            watch = (f'<button class="watch" type="button" data-src="/assets/{slug}/{q(full)}" aria-haspopup="dialog">'
                     f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4.5v15l13-7.5z"/></svg>Watch the video</button>')
    elif full:
        poster = f' poster="/assets/{slug}/poster.jpg"' if has_file("poster.jpg") else ""
        media = (f'<video id="v" autoplay muted loop playsinline preload="auto"{poster}><source src="/assets/{slug}/{q(full)}" type="video/mp4"></video>'
                 + (f'<div class="fallback" id="vfb" style="background:#0b0f1a url(/assets/{slug}/poster.jpg) center/cover no-repeat"></div>' if has_file("poster.jpg")
                  else f'<div class="fallback" id="vfb"><div>{_i(lead_icon)}{name}</div></div>')
                 + f'<button class="play" id="play" aria-label="Play video"><svg viewBox="0 0 24 24"><path d="M7 4.5v15l13-7.5z"/></svg></button>')
    else:
        media = f'<div class="fallback" style="display:grid"><div>{_i(lead_icon)}{name}</div></div>'

    bullets = "".join(
        f'<li>{_i("check")}<div><b>{e(b["b"])}</b>{(" <span>" + e(b["s"]) + "</span>") if b.get("s") else ""}</div></li>' for b in pitch["bullets"])
    hours_html = f'<p class="hours rise" style="--i:7">{_i("clock")}{e(hours)}</p>' if hours else ""
    marquee = "".join(f"<span>{e(x)}</span>" for x in (badges * 2) * 2)

    c = pitch["compare"]

    def lis(items, icon):
        return "".join(f'<li style="--n:{k}">{_i(icon)}{e(t)}</li>' for k, t in enumerate(items))

    # the animated browser-tab counter belongs to the flights page; other brands get no invented statistic
    bad_stat = (f'<div class="stat"><b id="tabsn" data-to="{int(c["bad_stat"])}">0</b><span>{e(c["bad_label"])}</span></div><div class="tabs" id="tabstrip" aria-hidden="true"></div>'
                if flights else "")
    compare = (f'<section id="easy"><div class="wrap"><div class="head"><span class="eyebrow reveal">{e(c["eyebrow"])}</span><h2 class="reveal" style="--i:1">{e(c["title"])}</h2></div>'
               f'<div class="vs"><article class="panel good reveal"><h3>{e(c["good_title"])}</h3><ul>{lis(c["good"], "check")}</ul><div class="stat"><b>{e(str(c["good_stat"]))}</b><span>{e(c["good_label"])}</span></div></article>'
               f'<div class="vsbadge">VS</div>'
               f'<article class="panel bad reveal" id="pbad" style="--i:1"><h3>{e(c["bad_title"])}</h3><ul>{lis(c["bad"], "x")}</ul>{bad_stat}</article></div></div></section>')

    r = pitch["reasons"]["items"]
    tile_img = ""
    # the image tile shows a branded image too (Flight Finder Pro has its plane photo there); pick the one the hero is not already showing
    # (variant B already shows both branded images in its hero, so its tile stays text only)
    tile_file = brand.get("tile_image") if brand.get("tile_image") and has_file(brand.get("tile_image")) else \
        ("hero-still.jpg" if has_still and not variant_b else "")
    if tile_file:
        tile_img = f'<img src="/assets/{slug}/{q(tile_file)}" alt="" loading="lazy" onerror="this.remove()">'
    order = [(1, 0), (2, 2), (3, 1), (4, 3), (5, 4), (6, 5), (7, 6)]  # tile class index -> reason index
    tiles = ""
    for cls_i, ri in order:
        t, b = r[ri]
        if cls_i == 1:
            inner = f'{_i("person", "i big")}<span class="ring">{_i("phone")}</span><h3>{e(t)}</h3><p>{e(b)}</p>'
        elif cls_i == 2:
            inner = f'{tile_img}<span class="ic">{_i("search")}</span><h3>{e(t)}</h3><p>{e(b)}</p>'
        else:
            inner = f'<span class="ic">{_i(icons_reason[ri])}</span><h3>{e(t)}</h3><p>{e(b)}</p>'
        tiles += f'<article class="tile t{cls_i} reveal" style="--i:{cls_i % 4}">{inner}</article>'
    bento = (f'<section style="padding-top:0"><div class="wrap"><div class="head"><span class="eyebrow reveal">{e(pitch["reasons"]["eyebrow"])}</span>'
             f'<h2 class="reveal" style="--i:1">{e(pitch["reasons"]["title"])}</h2></div><div class="bento">{tiles}</div></div></section>')

    st = pitch["steps"]["items"]
    cards = "".join(
        f'<article class="scard{" last" if k == len(st) - 1 else ""}" style="--k:{k}"><div class="num">0{k + 1}</div><div><h3>{e(t)}</h3><p>{e(b)}</p></div>'
        f'<div class="ico">{_i(ICONS_STEP[k % 5])}</div></article>' for k, (t, b) in enumerate(st))
    steps = (f'<section class="how" style="padding-bottom:40px"><div class="wrap"><div class="head"><span class="eyebrow reveal">{e(pitch["steps"]["eyebrow"])}</span>'
             f'<h2 class="reveal" style="--i:1">{e(pitch["steps"]["title"])}</h2></div><div class="stack">{cards}</div></div></section>')

    f = pitch["free"]
    nos = "".join(f'<div class="no">{_i("ban")}{e(n)}</div>' for n in f["nos"])
    free_body = e(f["body"]).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
    free = (f'<section class="free"><div class="wrap"><div><span class="eyebrow">{e(f["eyebrow"])}</span><h2>{e(f["title"])}</h2><p class="lead">{free_body}</p>'
            f'<a class="btn light" href="tel:{tel}">{_i("phone")}<span>{e(f["cta"])}</span></a></div><div class="nos">{nos}</div></div></section>')

    cl = pitch["close"]
    cw = cl["title"].split()
    n = cl.get("accent_words", 0)
    ctitle = e(" ".join(cw[:len(cw) - n])) + (f" <em>{e(' '.join(cw[len(cw) - n:]))}</em>" if n else "")
    close = (f'<section class="close" style="padding-top:40px"><div class="wrap"><div class="box"><div><h2>{ctitle}</h2><p>{e(cl["sub"])}</p>'
             f'<a class="bigphone" href="tel:{tel}">{num()}</a></div><div class="glass"><h3>{e(cl["form_title"])}</h3>'
             f'<form id="lead-form"><input name="name" placeholder="Your name" autocomplete="name" required><input name="phone" placeholder="Best phone number" autocomplete="tel" inputmode="tel" required><input name="zip" placeholder="ZIP code" autocomplete="postal-code" inputmode="numeric" required>'
             f'<input type="hidden" name="click_id" data-track="_ef_transaction_id"><input type="hidden" name="sub1" data-track="sub1"><input type="hidden" name="affid" data-track="affid">'
             f'<button class="btn light" type="submit">{e(cl["form_cta"])}</button></form></div></div></div></section>')

    faq = "".join(
        f'<div class="qa"><button class="q" id="q{k}" aria-expanded="false" aria-controls="a{k}"><span>{e(qq)}</span><i></i></button>'
        f'<div class="a" id="a{k}" role="region" aria-labelledby="q{k}"><div><p>{e(aa)}</p></div></div></div>' for k, (qq, aa) in enumerate(pitch["faq"]))
    faq_sec = (f'<section class="faq"><div class="wrap"><div class="head"><span class="eyebrow reveal">Questions</span><h2 class="reveal" style="--i:1">Common questions</h2></div><div>{faq}</div></div></section>')

    links = "".join(f'<a href="{k}.html">{e(v)}</a>' for k, v in (
        ("privacy", "Privacy Policy"), ("terms", "Terms of Use"), ("ccpa", "California Privacy Rights"), ("opt-out", "Opt-Out"),
        ("aup", "Acceptable Use"), ("cookies", "Cookies"), ("partners", "Marketing Partners")))
    legal = e(brand.get("legal_entity") or "[Legal entity name]")
    desc = e(pitch["eyebrow"] + ". " + pitch["bullets"][0]["b"])
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            f'<title>{name} | {e(pitch["hero"])}</title><meta name="description" content="{desc}">\n<script>document.documentElement.className+=" js";</script>\n{FONTS}\n<style>\n{css}\n</style>\n{ringba}\n{everflow}\n</head><body>\n'
            f'{SPRITE}\n<div class="progress"><i></i></div>\n'
            f'<header class="nav-wrap"><div class="nav"><a class="brand" href="#top"><span class="logo">{_i(lead_icon)}</span>{name}</a><a class="tel" href="tel:{tel}">{_i("phone")}{num()}</a></div></header>\n'
            f'<main id="top"><section class="hero"><div class="wrap hero-grid{" solo" if solo else ""}"><div><span class="eyebrow rise" style="--i:0">{e(pitch["eyebrow"])}</span>'
            f'<h1 aria-label="{e(pitch["hero"])}">{_words(pitch["hero"], pitch.get("hero_accent_words", 0))}</h1><ul class="points rise" style="--i:5">{bullets}</ul>'
            f'<div class="cta-row rise" style="--i:6"><a class="btn" href="tel:{tel}">{_i("phone")}<span>{cta + ': ' + num() if brand.get('phone') else cta}</span>{_i(arrow_icon, "i arr")}</a><a class="btn ghost" href="#easy">See the easy way</a></div>{hours_html}</div>'
            + ('' if solo else f'<div class="media rise{" has-ovl" if has_ovl else ""}" style="--i:3"><div class="vid" id="vid">{media}</div><span class="chip c1">{_i("person")}{e(badges[0])}</span><span class="chip c2">{_i("heart")}{e(badges[3])}</span>'
                                 + (f'<figure class="ovl" aria-hidden="true"><img src="/assets/{slug}/overlay.jpg" alt="" loading="lazy"></figure>' if has_ovl else "")
                                 + watch + '</div>') + f'</div></section>\n'
            + ('<dialog class="vmodal" id="vmodal" aria-label="Video"><button class="vclose" type="button" aria-label="Close video">&times;</button>'
               '<video id="vfull" controls playsinline preload="none"></video></dialog>\n' if watch else '')
            + f'<div class="marquee" aria-hidden="true"><div class="track">{marquee}</div></div>\n{compare}\n{bento}\n{steps}\n{free}\n{faq_sec}\n{close}</main>\n'
            f'<footer><div class="wrap"><div class="links">{links}</div><p>&copy; {time.strftime("%Y")} {legal}. {name} is a marketing site that connects consumers with {partners}. See our Marketing Partners page for details. {e(pitch.get("disclaimer", ""))}</p></div></footer>\n'
            f'<div class="callbar"><a class="btn" href="tel:{tel}">{_i("phone")}<span>Call {num()}</span></a></div>\n<script>\n{SCRIPT_JS}\n</script>\n</body></html>')
