"""Brand page studio core: Sheet-driven config, page + compliance generation, checklist, video variants, metrics."""
import base64
import csv
import html
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from string import Template

import paths

ROOT = paths.ROOT
CONFIG = ROOT / "brands.csv"
OUT = ROOT / "out"
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
BEFORE = ROOT / "before"
METRICS = DATA / "metrics.jsonl"
SCRIPTS = DATA / "final_scripts.txt"
PITCH_DIR = DATA / "pitch"

FIELDS = ["slug", "name", "vertical", "offer", "audience", "phone", "tone", "primary_color", "accent_color",
          "buyer", "cta", "current_url", "hero_image", "legal_entity", "contact_email", "legal_reviewed", "hero_video", "tile_image", "hours",
          "ringba_campaign", "everflow_offer", "delivery", "leadprosper_campaign", "leadprosper_supplier"]

COMPLIANCE_PAGES = {
    "privacy": "Privacy Policy",
    "terms": "Terms of Use",
    "ccpa": "California Privacy Rights (CCPA)",
    "opt-out": "Opt-Out / Do Not Sell or Share",
    "aup": "Acceptable Use Policy",
    "cookies": "Cookie Policy",
    "partners": "Marketing Partners",
}

e = html.escape


# ---------------------------------------------------------------- config (the Sheet)

def _local_rows():
    with open(CONFIG, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def config_source():
    import sheet
    sheet.roster()
    return sheet.status()["source"] + " + brands.csv"


ACCENTS = ["#0b5ed7", "#b3202a", "#0f766e", "#7c3aed", "#c2410c", "#0e7490", "#4d7c0f", "#be185d"]
FALLBACK_LOOK = {"offer": "Talk with a real person about your options", "audience": "people looking for help", "tone": "trustworthy, plain-spoken, no hype",
                 "cta": "Call now", "primary_color": "#14213d", "accent_color": "#0b5ed7"}


def _defaults(sb, rows):
    """A new brand takes the copy and look of the first local brand in the same vertical, with its own accent."""
    kin = next((r for r in rows if r.get("vertical") == sb["vertical"]), None) or {}
    d = {k: kin.get(k, FALLBACK_LOOK.get(k, "")) for k in ("offer", "audience", "tone", "cta", "primary_color", "accent_color")}
    d = {k: (v or FALLBACK_LOOK.get(k, "")) for k, v in d.items()}
    d["accent_color"] = ACCENTS[sum(map(ord, sb["slug"])) % len(ACCENTS)]
    return {**{k: "" for k in FIELDS}, **d, "slug": sb["slug"]}


def sheet_info(slug=None):
    """What the Sheet knows about each brand (priority, site status, buyers, campaigns). One brand's dict, or all of them keyed by slug."""
    import sheet
    info = {b["slug"]: b for b in sheet.roster()}
    return info.get(slug) if slug else info


def load_brands():
    """Brands come from the Google Sheet (Priority List order). The Sheet owns name, vertical and, unless set locally, website, buyer and
    delivery type. brands.csv holds what the Sheet does not: phone, colors, copy, mappings and legal flags. Falls back to brands.csv alone."""
    import sheet
    local = _local_rows()
    by_slug = {r["slug"]: r for r in local if r.get("slug")}
    roster = sheet.roster()
    if not roster:
        return [{k: (r.get(k) or "").strip() for k in FIELDS} for r in local if (r.get("slug") or "").strip()]
    out = []
    for sb in roster:
        r = dict(by_slug.get(sb["slug"]) or _defaults(sb, local))
        r["name"], r["vertical"] = sb["name"], sb["vertical"]
        r["current_url"] = (r.get("current_url") or "").strip() or sb["url"]
        if not (r.get("buyer") or "").strip() and sb["buyer_confirmed"]:
            r["buyer"] = sb["buyers"]
        if not (r.get("delivery") or "").strip():
            r["delivery"] = sb["delivery"] or "calls"
        out.append({k: (r.get(k) or "").strip() for k in FIELDS})
    return out


def get_brand(slug):
    for b in load_brands():
        if b["slug"] == slug:
            return b
    raise KeyError(slug)


def set_brand_field(slug, field, value):
    """Writes the brand's local row (created from the merged brand if it is new). The Sheet itself is read-only from here."""
    rows = _local_rows()
    row = next((r for r in rows if r["slug"] == slug), None)
    if row is None:
        sb = sheet_info(slug)
        if not sb:
            raise KeyError(slug)
        row = _defaults(sb, rows)  # only identity and look: the Sheet stays the source for buyer, website and delivery
        row["name"], row["vertical"] = sb["name"], sb["vertical"]
        rows.append(row)
    row[field] = value
    with open(CONFIG, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in FIELDS} for r in rows)


# ---------------------------------------------------------------- copy

BANK = {
    "insurance": {
        "hero": "Stop overpaying for the coverage your family relies on",
        "sub": "Talk to a licensed agent who compares options for {audience}. Free to check, no obligation.",
        "trust": ["Free to compare", "No obligation", "Licensed agents", "Real people on the phone"],
        "benefits": [("Compare, don't guess", "We look across carriers so you can see real options side by side."),
                     ("Real people, real answers", "Speak with a licensed agent by phone. No endless forms."),
                     ("Free, no obligation", "Checking costs nothing, and you decide what happens next.")],
        "faq": [("Does it cost anything to compare?", "No. Comparing options is free and there is no obligation to buy."),
                ("Who will I speak with?", "A licensed insurance agent who can walk you through your options."),
                ("How long does it take?", "It only takes a few minutes to review your options.")],
        "steps": [("Call or leave your number", "It takes a minute. Tell us what you are looking for and who it is for."),
                  ("Talk with a licensed agent", "A real person compares options across carriers and explains them in plain language."),
                  ("Decide on your terms", "There is no cost to compare and no obligation to buy.")],
        "angles": {
            "life": ("Protect your family with life insurance that fits your budget",
                     "If something happened tomorrow, would your family be able to keep the house? See how affordable coverage can be."),
            "auto": ("Your neighbor may be paying half what you pay for the same car insurance",
                     "If you have been with the same company for years, it is worth a quick comparison."),
            "home": ("Home insurance rates are climbing. See what you could save",
                     "Shop the market with one call and see your options for {audience}."),
            "health": ("Don't go without health coverage",
                       "Find a plan that fits your budget with help from a licensed agent."),
            "medicare": ("Make sure you are getting everything your Medicare can offer",
                         "A licensed agent can explain your plan options in plain language."),
            "final expense": ("Make sure your family isn't stuck paying for a funeral",
                              "Simple final expense coverage can put the money in place before it is needed."),
        },
    },
    "flights": {
        "eyebrow": "Personal flight booking assistance",
        "hero": "Stop searching. Start your journey.",
        "sub": "Tell a real person where you are headed. We help you explore flight options around your schedule and budget.",
        "trust": ["A conversation, not endless searching", "Options around your plans", "Personal help with your travel plans", "For travelers and referral partners"],
        "benefits": [("A conversation, not endless searching", "Tell us where you are headed and we do the searching with you."),
                     ("Options around your schedule and budget", "We help you compare fares, schedules and connections."),
                     ("Personal help with your plans", "Ask questions and review the details before you decide.")],
        "faq": [("What do I need when I call?", "Your destination, rough travel dates, how many people are traveling, and what matters most to you."),
                ("When can I call?", "Monday to Friday, 9am to 6pm EST."),
                ("Will prices change?", "Fares and availability are subject to change, so your agent confirms current options with you on the call."),
                ("Who will I speak with?", "A real person who helps you explore flight options.")],
        "steps": [("Tell us about your trip", "Share your destination, travel dates, travelers, and what matters most to you."),
                  ("Explore your options", "Compare available fares, schedules and connections around your plans."),
                  ("Plan your next step", "Review the details and ask questions before deciding how you would like to travel.")],
        "compare": {"eyebrow": "The easy way to book", "title": "One conversation, or twenty seven tabs.",
                    "good_title": "Flight Finder Pro", "good": ["One phone call", "Personal help", "We do the searching", "Options around your plans"],
                    "good_stat": "1", "good_label": "phone call",
                    "bad_title": "Searching online", "bad": ["27 browser tabs", "Prices keep changing", "Confusing options", "Hours comparing"],
                    "bad_stat": 27, "bad_label": "browser tabs open"},
        "partners": {"eyebrow": "Affiliates and traffic partners", "title": "Good journeys start with good connections.",
                     "body": "Let us discuss your referral plans and confirm the right next steps before routing callers.", "cta": "Talk partnerships"},
        "disclaimer": " Fares and availability are subject to change.",
        "chips": ["Personal help", "Real conversation"],
        "angles": {},
    },
    "debt": {
        "hero": "Buried in debt? There is a way out",
        "sub": "Find out in minutes if you may qualify for debt relief. A free call, no upfront cost.",
        "trust": ["Free consultation", "No upfront fees", "Real specialists", "Confidential"],
        "benefits": [("Lower your payments", "Specialists work with your creditors to build a plan."),
                     ("Real people, real plan", "Talk it through with an expert who listens."),
                     ("Free to find out", "See what you may qualify for before you commit.")],
        "faq": [("Does the call cost anything?", "No. The consultation is free."),
                ("What debt qualifies?", "Programs commonly look at $10,000 or more in credit card, medical or loan debt."),
                ("Is it confidential?", "Yes. We keep your information private.")],
        "steps": [("Make a free call", "Tell a specialist what you owe and what is weighing on you."),
                  ("Review your options", "See what programs you may qualify for and what they could mean for your payments."),
                  ("Choose your next step", "You decide. The consultation is free.")],
        "angles": {},
    },
}

from banks import EXTRA  # noqa: E402
BANK.update(EXTRA)

_EMOJI = re.compile("[🀀-🫿☀-➿️‍]")


def clean(x):
    """No em or en dashes, no emojis, in any generated text. Recurses into lists and dicts."""
    if isinstance(x, str):
        x = _EMOJI.sub("", x)
        x = re.sub(r"(?<=\d)–(?=\d)", "-", x)
        return re.sub(r"\s*[—–]\s*", ", ", x).strip()
    if isinstance(x, list):
        return [clean(i) for i in x]
    if isinstance(x, dict):
        return {k: clean(v) if k not in ("source", "tokens_in", "tokens_out") else v for k, v in x.items()}
    return x


def offline_copy(brand, prompt):
    bank = BANK.get(brand["vertical"], BANK["insurance"])
    hero, sub = bank["hero"], bank["sub"]
    p = (prompt or "").lower()
    for key, (h, s) in bank["angles"].items():
        if key in p:
            hero, sub = h, s
            break
    ctx = {"audience": brand["audience"] or "your family", "name": brand["name"]}
    return {
        "hero": hero, "sub": sub.format(**ctx), "trust": bank["trust"],
        "benefits": [{"title": t, "body": b} for t, b in bank["benefits"]],
        "faq": [{"q": q, "a": a} for q, a in bank["faq"]],
        "steps": [{"title": t, "body": b} for t, b in bank["steps"]],
        "eyebrow": bank.get("eyebrow"), "compare": bank.get("compare"), "partners": bank.get("partners"),
        "disclaimer": bank.get("disclaimer", ""), "chips": bank.get("chips"),
        "cta": brand["cta"] or "Call now", "source": "offline template", "tokens_in": 0, "tokens_out": 0,
    }


SALES_RULES = (
    "Write direct-response SALES copy for a phone-call landing page. Lead with the outcome the reader wants, in plain words. "
    "Hero: one clear promise a real person would say out loud. Bullets and reasons: specific, benefit-led, short punchy lines. "
    "Handle the doubts people have (cost, time, whether it is a hassle, who they will talk to) in the FAQ and steps. "
    "Every section should push toward the same action: call now. Use urgency only when it is true (for example office hours); never fake scarcity. "
    "Compliance: no guarantees, no invented statistics, testimonials, awards, ratings or savings amounts, and no claim the brand details below do not support "
    "(do not say a service is free, or who pays, unless the offer says so). Never use em dashes, en dashes or emojis. Do not mention AI."
)


VERTICAL_NOTES = {
    "medicare": "Medicare and senior insurance: never imply a government agency, Medicare itself or Social Security endorses or runs this site. Do not name carriers, plan prices or benefit amounts. Say a licensed agent can explain options.",
    "insurance": "Insurance: do not name carriers, prices or savings amounts. Say a licensed agent can explain options.",
    "final-expense": "Final expense insurance: be gentle and plain, no prices, no guaranteed acceptance, no fear tactics. Say a licensed agent can explain options.",
    "legal": "Legal services: never promise a result, compensation, case value or that the reader has a case. Do not call anyone an attorney or law firm unless the offer says so. Say the team can talk through their situation and next steps.",
    "debt": "Debt relief: never promise a reduction amount or percentage, never say debt is erased or forgiven, no timelines. Say an expert can walk through options.",
    "loans": "Loans: no rates, approval promises or amounts. Say a specialist explains what may be available.",
    "addiction": "Treatment services: no promises of recovery or outcomes, be compassionate and confidential, no medical claims.",
}


def _brand_brief(b):
    bits = [f"Brand: {b['name']}", f"vertical: {b['vertical']}", f"offer: {b['offer']}", f"audience: {b['audience']}", f"tone: {b['tone']}", f"call to action: {b['cta'] or 'Call now'}"]
    if b.get("hours"):
        bits.append(f"call hours: {b['hours']}")
    note = VERTICAL_NOTES.get(b.get("vertical", ""), "")
    return " | ".join(bits) + (". " + note if note else "")


def gemini_key():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if k:
        return k
    try:
        return json.loads((DATA / "integrations.json").read_text(encoding="utf-8")).get("gemini", {}).get("api_key", "").strip()
    except Exception:
        return ""


def ai_provider():
    """Which model reads images and writes copy: Gemini if a key is set, else Claude by API key, else the Claude Code CLI (images only), else none."""
    if gemini_key():
        return "Gemini"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "Claude"
    return "Claude CLI"


def _via_gemini(key, prompt, img=None, max_tokens=4000):
    """One Gemini generateContent call that must return JSON. Returns (text, tokens_in, tokens_out)."""
    parts = []
    if img is not None:
        parts.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(Path(img).read_bytes()).decode()}})
    parts.append({"text": prompt})
    body = {"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3, "maxOutputTokens": max_tokens}}
    # Google retires models for new keys without notice, so try the "latest" alias first and fall back down a short list on 404
    models = [m for m in (os.environ.get("STUDIO_GEMINI_MODEL"), "gemini-flash-latest", "gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-pro-latest") if m]
    detail = ""
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for attempt in range(3):
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"x-goog-api-key": key, "content-type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    js = json.loads(r.read())
                cand = (js.get("candidates") or [{}])[0]
                text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
                if not text.strip():
                    raise RuntimeError("Gemini returned no text (" + str(cand.get("finishReason", "empty")) + ").")
                u = js.get("usageMetadata", {})
                return text, u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0)
            except urllib.error.HTTPError as ex:
                detail = f"HTTP {ex.code}: " + ex.read()[:160].decode("utf-8", "ignore")
                if ex.code in (429, 500, 503) and attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                break  # 404 or another hard error: next model
    raise RuntimeError("Gemini request failed (" + detail + ")")


def llm_copy(brand, prompt):
    gkey = gemini_key()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key and not gkey:
        return None
    ask = (
        "Write landing page copy as JSON only, with keys: hero (string), sub (string), trust (4 short strings), "
        "benefits (3 objects with title, body), steps (3 objects with title, body: how it works), faq (3 objects with q, a), cta (string).\n"
        + _brand_brief(brand) + "\n"
        f"Direction from the operator: {prompt}\n"
        + SALES_RULES + " Do not claim licenses or awards beyond 'licensed agents' where relevant."
    )
    try:
        if gkey:
            text, tin, tout = _via_gemini(gkey, ask, None, 2500)
            source = "Gemini"
        else:
            body = {"model": os.environ.get("STUDIO_MODEL", "claude-sonnet-5"), "max_tokens": 1500, "messages": [{"role": "user", "content": ask}]}
            req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                         headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            text = resp["content"][0]["text"]
            tin, tout = resp.get("usage", {}).get("input_tokens", 0), resp.get("usage", {}).get("output_tokens", 0)
            source = "Claude"
        data = json.loads(text[text.index("{"): text.rindex("}") + 1])
        data["source"] = source
        data["tokens_in"], data["tokens_out"] = tin, tout
        data.setdefault("cta", brand["cta"] or "Call now")
        return data
    except Exception:
        return None


# ---------------------------------------------------------------- page

TRACKING_JS = """(function(){
  var keys=['_ef_transaction_id','eftid','oid','affid','sub1','sub2','sub3','sub4','sub5','click_id','gclid','fbclid','utm_source','utm_medium','utm_campaign'];
  var q=new URLSearchParams(location.search), t={};
  try{t=JSON.parse(sessionStorage.getItem('bwa_tracking')||'{}');}catch(e){}
  keys.forEach(function(k){var v=q.get(k); if(v){t[k]=v;}});
  try{sessionStorage.setItem('bwa_tracking',JSON.stringify(t));}catch(e){}
  window.BWA_TRACKING=t;
  document.querySelectorAll('input[data-track]').forEach(function(i){i.value=t[i.getAttribute('data-track')]||'';});
  var f=document.getElementById('lead-form');
  if(f){f.addEventListener('submit',function(ev){ev.preventDefault();f.innerHTML='<p><strong>Thank you.</strong> A licensed agent will call you shortly.</p>';});}
})();"""

from template import PAGE, MOTION_JS, LEGAL_PAGE, FONTS  # noqa: E402

_SV = 'class="ico draw" viewBox="0 0 96 96" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'
ICONS = [
    f'<svg {_SV}><rect pathLength="100" x="28" y="10" width="40" height="76" rx="9"/><path pathLength="100" d="M42 20h12"/><circle pathLength="100" cx="48" cy="72" r="4"/></svg>',
    f'<svg {_SV}><circle pathLength="100" cx="36" cy="38" r="14"/><path pathLength="100" d="M12 82c0-14 11-24 24-24s24 10 24 24"/><circle pathLength="100" cx="66" cy="42" r="10"/><path pathLength="100" d="M62 62c12-2 22 6 22 20"/></svg>',
    f'<svg {_SV}><circle pathLength="100" cx="48" cy="48" r="34"/><path pathLength="100" d="M33 49l11 11 20-23"/></svg>',
]


def load_pitch(slug):
    f = PITCH_DIR / f"{slug}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def save_reference(slug, raw):
    """Save an uploaded reference image as before/<slug>-concept.png."""
    from PIL import Image
    BEFORE.mkdir(exist_ok=True)
    Image.open(io.BytesIO(raw)).convert("RGB").save(BEFORE / f"{slug}-concept.png", optimize=True)


PITCH_KEYS = ["eyebrow", "hero", "bullets", "cta", "badges", "compare", "reasons", "steps", "free", "close", "faq"]


def _pitch_prompt(slug, example_path, img_path, inline=False, brand=None, mode="inspire"):
    """Prompt for reading a landing page image. mode 'inspire' (default) writes NEW sales copy for the brand using the image for angle, structure and
    emphasis. mode 'exact' keeps the image's own wording. inline=True is for API providers that cannot read files: the example pitch is pasted in."""
    shape = ("reasons.items must have 7 [title, short line] pairs, steps.items 3 to 5 pairs, badges 4 strings. "
             "If the image shows no such section, write a neutral, claim-free version for this brand.")
    if inline:
        example = Path(example_path).read_text(encoding="utf-8")
        where = "Return ONLY one JSON object, no markdown, with exactly the same keys and shapes as this example (copy its structure, not its wording):\n" + example + "\n"
        look = "the attached landing page image"
    else:
        where = ("Return ONLY one JSON object, no markdown, with exactly the same keys and shapes as the example file at " + str(example_path) + " (read it for the structure). ")
        look = "the landing page image at " + str(img_path)
    if mode == "exact" or not brand:
        return ("Read the sales pitch on " + look + ". " + where +
                "Use the wording from the image: shorten nothing, invent no claims, no em dashes, no emojis. " + shape)
    return ("You are a direct-response copywriter. " + _brand_brief(brand) + ".\n"
            "Study " + look + ". It is a landing page from a similar campaign. Use it as INSPIRATION only: notice its angle, headline style, section order, what it "
            "emphasizes (a person on video, a comparison, reasons to call, easy steps, reassurance) and why it persuades. Then write NEW copy for " + brand["name"] +
            " in the same spirit, about this brand's own offer. Do not copy the image's brand name, phone number, prices, hours or claims, and do not carry over "
            "the image's subject matter if it is a different service. " + SALES_RULES + " "
            "Invent no statistics anywhere, including compare.good_stat and compare.bad_stat: use plain counts of the action itself (for example 1 phone call) and 0 where unsure. "
            "In the reassurance section ('free') list only reassurances you can stand behind, such as no pressure, no obligation, confidential, a real person. "
            "Never state fees, 'free', 'no cost' or 'no upfront fee' unless the offer above says so.\n" + where + shape)


def _via_api(key, prompt, img):
    body = {"model": os.environ.get("STUDIO_MODEL", "claude-sonnet-5"), "max_tokens": 4000,
            "messages": [{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.b64encode(img.read_bytes()).decode()}},
                {"type": "text", "text": prompt}]}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                 headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())["content"][0]["text"]


def _via_cli(prompt):
    import shutil
    import subprocess
    exe = shutil.which("claude")
    if not exe:
        raise RuntimeError("To read an image the studio needs a Gemini key (Integrations page), an ANTHROPIC_API_KEY, or the Claude Code CLI signed in.")
    p = subprocess.run([exe, "-p", prompt, "--allowedTools", "Read", "--output-format", "text"],
                       cwd=str(ROOT), capture_output=True, text=True, timeout=300, encoding="utf-8")
    if p.returncode != 0:
        msg = (p.stderr or p.stdout or "")
        if "authenticate" in msg.lower() or "oauth" in msg.lower() or "login" in msg.lower():
            raise RuntimeError("The Claude CLI is not signed in. Run claude login in a terminal, or set ANTHROPIC_API_KEY, then try again. The current pitch stays in use.")
        raise RuntimeError("Claude CLI failed: " + msg[:300])
    return p.stdout


_RISKY = re.compile(r"\b(free|no[- ]cost|no[- ]charge|no[- ]upfront|upfront|no[- ]fees?|fees?|guarantee[ds]?|risk[- ]free|lowest|best price)\b", re.I)


def sanitize_pitch(data, brand):
    """Safety pass for copy the model wrote 'in the spirit of' an image: drop fee, free and guarantee claims the brand never supplied.
    Reassurances are swapped for ones that are always safe, and cost answers point to the call. The legal gate still reviews everything."""
    if _RISKY.search(brand.get("offer", "")):
        return data
    safe = ["No pressure", "No obligation", "Confidential", "A real person"]
    free = data.get("free")
    if isinstance(free, dict) and isinstance(free.get("nos"), list):
        kept = [n for n in free["nos"] if not _RISKY.search(str(n))]
        for s in safe:
            if len(kept) >= 4:
                break
            if s not in kept and not any(s.split()[-1].lower() in k.lower() for k in kept):
                kept.append(s)
        free["nos"] = kept[:4]
        for k in ("title", "body"):
            if isinstance(free.get(k), str) and _RISKY.search(free[k]):
                free[k] = re.sub(r"\s*[^.]*\b(free|no[- ]cost|no[- ]charge|upfront|fees?)\b[^.]*\.?", "", free[k], flags=re.I).strip() or "Talk it through with a real person."
    faq = data.get("faq")
    if isinstance(faq, list):
        for item in faq:
            if isinstance(item, list) and len(item) >= 2 and _RISKY.search(str(item[1])):
                item[1] = "Ask about costs on the call. Your expert explains everything clearly before you decide anything."
    comp = data.get("compare")
    if isinstance(comp, dict):  # statistics are never invented
        comp["good_stat"] = comp["good_stat"] if str(comp.get("good_stat", "")).isdigit() and int(comp["good_stat"]) <= 3 else 1
        comp["bad_stat"] = 0
    badges = data.get("badges")
    if isinstance(badges, list):
        kept = [x for x in badges if not _RISKY.search(str(x))]
        data["badges"] = (kept + [s for s in safe if s not in kept])[:4]
    return data


def extract_pitch(slug, mode="inspire"):
    """Read the sales pitch off the reference image (API key if set, else the Claude Code CLI) and save data/pitch/<slug>.json.
    The result is validated by building a page from it before it replaces the current pitch."""
    img = BEFORE / f"{slug}-concept.png"
    if not img.exists():
        raise RuntimeError("No reference image for this brand yet.")
    PITCH_DIR.mkdir(parents=True, exist_ok=True)
    cur = PITCH_DIR / f"{slug}.json"
    ex = cur if cur.exists() else next(iter(sorted(PITCH_DIR.glob("*.json"))), None)
    if not ex:
        raise RuntimeError("Needs one example pitch file in data/pitch/ to copy the structure from.")
    gkey, key = gemini_key(), os.environ.get("ANTHROPIC_API_KEY")
    brand = get_brand(slug)
    if gkey:
        text = _via_gemini(gkey, _pitch_prompt(slug, ex, img, True, brand, mode), img)[0]
    elif key:
        text = _via_api(key, _pitch_prompt(slug, ex, img, True, brand, mode), img)
    else:
        text = _via_cli(_pitch_prompt(slug, ex, img, False, brand, mode))
    try:
        data = clean(json.loads(text[text.index("{"): text.rindex("}") + 1]))
        if mode != "exact":
            data = sanitize_pitch(data, get_brand(slug))
        missing = [k for k in PITCH_KEYS if k not in data]
        if missing:
            raise ValueError("missing keys: " + ", ".join(missing))
        from pitch_site import build_pitch_page
        build_pitch_page(get_brand(slug), data, "", "", lambda n: False)
    except Exception as e:
        raise RuntimeError("Could not use the pitch it read (" + str(e)[:120] + "). The previous pitch stays in use.")
    if cur.exists():
        (PITCH_DIR / f"{slug}.prev.json").write_text(cur.read_text(encoding="utf-8"), encoding="utf-8")
    cur.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def _after_generate(slug, source):
    import store
    store.log_event(slug, "page.generated", source)
    try:
        import integrations
        integrations.refresh_stage(slug)
    except Exception:
        pass


def _build_from_pitch(brand, pitch, t0):
    from pitch_site import build_pitch_page
    slug = brand["slug"]
    page = build_pitch_page(
        brand, clean(pitch),
        _snippet("ringba_snippet.html", "<!-- RINGBA_SNIPPET_PLACEHOLDER: paste the campaign's number insertion tag into studio/data/snippets/" + slug + "/ringba_snippet.html -->", slug),
        _snippet("everflow_snippet.html", "<!-- EVERFLOW_SNIPPET_PLACEHOLDER: paste the Everflow tracking tag into studio/data/snippets/" + slug + "/everflow_snippet.html -->", slug),
        lambda name: (ASSETS / slug / name).exists())
    d = OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(brand_extras(slug, page), encoding="utf-8")
    import wording
    wording.after_build(slug)
    n = build_compliance(brand)
    variants = build_variants(brand)
    rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "slug": slug, "seconds": round(time.time() - t0, 2), "source": "pitch from reference image",
           "tokens_in": 0, "tokens_out": 0, "compliance_pages": n, "variants": len(variants)}
    with open(METRICS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    _after_generate(slug, rec["source"])
    return rec


def _q(name):
    return urllib.parse.quote(name)


def compare_html(c):
    if not c:
        return ""
    def items(lst, icon):
        return "".join(f'<li style="--n:{i}"><svg class="i"><use href="#{icon}"/></svg>{e(x)}</li>' for i, x in enumerate(lst))
    return (f'<section id="easy"><div class="wrap"><div class="head"><span class="eyebrow reveal">{e(c["eyebrow"])}</span>'
            f'<h2 class="reveal" style="--i:1">{e(c["title"])}</h2></div><div class="vs">'
            f'<article class="panel good reveal"><h3>{e(c["good_title"])}</h3><ul>{items(c["good"], "i-check")}</ul>'
            f'<div class="stat"><b>{e(str(c["good_stat"]))}</b><span>{e(c["good_label"])}</span></div></article>'
            f'<div class="vsbadge">VS</div>'
            f'<article class="panel bad reveal" id="pbad" style="--i:1"><h3>{e(c["bad_title"])}</h3><ul>{items(c["bad"], "i-x")}</ul>'
            f'<div class="stat"><b id="tabsn" data-to="{int(c["bad_stat"])}">0</b><span>{e(c["bad_label"])}</span></div>'
            f'<div class="tabs" id="tabstrip" aria-hidden="true"></div></article></div></div></section>')


def partners_html(p, email):
    if not p:
        return ""
    href = f"mailto:{e(email)}" if email else "#"
    return (f'<section id="partners" style="padding:0 0 112px"><div class="wrap"><div class="pbar reveal"><div>'
            f'<span class="eyebrow">{e(p["eyebrow"])}</span><h2>{e(p["title"])}</h2><p>{e(p["body"])}</p></div>'
            f'<a class="btn light" href="{href}"><span>{e(p["cta"])}</span></a></div></div></section>')


def is_placeholder_phone(phone):
    return (not phone) or bool(re.search(r"555-"+chr(92)+"d{4}", phone))


def _snippet(name, placeholder, slug=None):
    for f in ([DATA / "snippets" / slug / name] if slug else []) + [DATA / name]:
        if f.exists():
            return f.read_text(encoding="utf-8")
    return placeholder


def build_page(brand, prompt):
    t0 = time.time()
    pitch = load_pitch(brand["slug"])
    if pitch:
        return _build_from_pitch(brand, pitch, t0)
    copy = llm_copy(brand, prompt) or offline_copy(brand, prompt)
    fallback = offline_copy(brand, prompt)
    for k in ("trust", "benefits", "steps", "faq", "eyebrow", "compare", "partners", "disclaimer", "chips"):
        copy.setdefault(k, fallback[k])
    copy = clean(copy)
    slug = brand["slug"]
    img = ASSETS / slug / brand["hero_image"] if brand["hero_image"] else None
    vid = ASSETS / slug / brand["hero_video"] if brand["hero_video"] else None
    if vid and vid.exists():
        poster = ASSETS / slug / "poster.jpg"
        pst = f' poster="/assets/{slug}/poster.jpg"' if poster.exists() else ""
        photo = (f'<div class="slot has-video"><video autoplay muted loop playsinline preload="auto"{pst}>'
                 f'<source src="/assets/{slug}/{_q(brand["hero_video"])}" type="video/mp4"></video></div>')
    elif img and img.exists():
        photo = f'<div class="slot"><img src="/assets/{slug}/{_q(brand["hero_image"])}" alt="{e(brand["name"])}"></div>'
    else:
        photo = '<div class="slot"><span>Drop a real photo or hero video here<br>(credibility shot from the brand folder)</span></div>'
    links = " ".join(f'<a href="{k}.html">{e(v)}</a>' for k, v in COMPLIANCE_PAGES.items())
    digits = re.sub(r"\D", "", brand["phone"])
    words = "".join(f'<span class="w" style="--i:{i}">{e(w)}</span> ' for i, w in enumerate(copy["hero"].split()))
    trust = copy["trust"]
    marquee = "".join(f"<span>{e(x)}</span>" for x in (trust * 2) * 2)
    checks = "".join(
        f'<li style="--i:{i}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
        f'stroke-linejoin="round"><circle cx="12" cy="12" r="10" opacity=".25"/><path pathLength="24" d="M7 12.5l3.5 3.5L17 9"/></svg>{e(x)}</li>'
        for i, x in enumerate(trust))
    ben = copy["benefits"]
    steps = "".join(
        f'<article class="scard k{i}" style="--k:{i}"><div class="num">0{i + 1}</div><div><h3>{e(s["title"])}</h3><p>{e(s["body"])}</p></div>{ICONS[i % 3]}</article>'
        for i, s in enumerate(copy["steps"]))
    faq = "".join(
        f'<div class="qa"><button class="q" id="q{i}" aria-expanded="false" aria-controls="a{i}"><span>{e(f["q"])}</span><i></i></button>'
        f'<div class="a" id="a{i}" role="region" aria-labelledby="q{i}"><div><p>{e(f["a"])}</p></div></div></div>'
        for i, f in enumerate(copy["faq"]))
    hours = brand["hours"]
    tile = ASSETS / slug / brand["tile_image"] if brand["tile_image"] else None
    has_tile = bool(tile and tile.exists())
    page = PAGE.substitute(
        navextra='<a class="navlink" href="#partners">For partners</a>' if copy.get("partners") else "",
        hours_html=(f'<p class="hours rise" style="--i:7"><svg class="i"><use href="#i-clock"/></svg>{e(hours)}</p>' if hours else ""),
        compare=compare_html(copy.get("compare")), partners=partners_html(copy.get("partners"), brand["contact_email"]),
        t2cls="has-img" if has_tile else "",
        t2img=(f'<img src="/assets/{slug}/{_q(brand["tile_image"])}" alt="">' if has_tile else ""),
        lead="Call now or leave your details and we will call you." + (f" We answer {e(hours)}." if hours else ""),
        disclaimer=e(copy.get("disclaimer") or ""),
        name=e(brand["name"]), offer=e(brand["offer"]), sub=e(copy["sub"]), hero=words, hero_plain=e(copy["hero"]),
        eyebrow=e(copy.get("eyebrow") or brand["vertical"].title()), fonts=FONTS,
        primary=e(brand["primary_color"] or "#0b2a5b"), accent=e(brand["accent_color"] or "#b3202a"),
        phone=e(brand["phone"]), telhref="+1" + digits[-10:] if digits else "", cta=e(copy["cta"]), photo=photo,
        chip1=e((copy.get("chips") or [trust[0], trust[min(2, len(trust) - 1)]])[1]), chip2=e((copy.get("chips") or [trust[0]])[0]), marquee=marquee, checks=checks,
        bento_title=e("Why people call " + brand["name"]), steps_title="Three steps. One conversation.",
        b0t=e(ben[0]["title"]), b0b=e(ben[0]["body"]), b1t=e(ben[1]["title"]), b1b=e(ben[1]["body"]),
        b2t=e(ben[2]["title"]), b2b=e(ben[2]["body"]), steps=steps, offer_h=e(brand["offer"]), faq=faq,
        links=links, year=time.strftime("%Y"), legal=e(brand["legal_entity"] or "[Legal entity name]"),
        ringba=_snippet("ringba_snippet.html", "<!-- RINGBA_SNIPPET_PLACEHOLDER: paste the campaign's number insertion tag into studio/data/snippets/" + slug + "/ringba_snippet.html -->", slug),
        everflow=_snippet("everflow_snippet.html", "<!-- EVERFLOW_SNIPPET_PLACEHOLDER: paste the Everflow tracking tag into studio/data/snippets/" + slug + "/everflow_snippet.html -->", slug),
        tracking=TRACKING_JS, motion=MOTION_JS,
    )
    d = OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(brand_extras(slug, page), encoding="utf-8")
    import wording
    wording.after_build(slug)
    n = build_compliance(brand)
    variants = build_variants(brand)
    secs = round(time.time() - t0, 2)
    rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "slug": slug, "seconds": secs, "source": copy["source"],
           "tokens_in": copy["tokens_in"], "tokens_out": copy["tokens_out"], "compliance_pages": n, "variants": len(variants)}
    with open(METRICS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    _after_generate(slug, rec["source"])
    return rec


# ---------------------------------------------------------------- compliance

LEGAL = {
    "privacy": """<p>This Privacy Policy explains how $name ("we", "us") collects, uses and shares information when you visit this site or contact us.</p>
<h2>Information we collect</h2><p>Information you give us (such as name, phone number and ZIP code), information from your device and browser, and call-related information such as the time and length of a call.</p>
<h2>How we use it</h2><p>To respond to your request, connect you with a licensed professional or partner, operate and improve the site, prevent fraud and meet legal obligations.</p>
<h2>How we share it</h2><p>With service providers and with partners who can help with your request, listed on our Marketing Partners page. We do not sell personal information for monetary consideration except as described in our California page.</p>
<h2>Your choices</h2><p>See our Opt-Out page and California Privacy Rights page. Contact us at $email.</p>""",
    "terms": """<p>By using this site you agree to these Terms of Use. $name connects consumers with licensed professionals and partners and is not itself an insurer, lender, law firm or airline unless stated.</p>
<h2>No guarantee</h2><p>Offers, rates and availability vary by person and location and are not guaranteed.</p>
<h2>Calls and messages</h2><p>Calls may be recorded for quality and compliance. By providing your number you agree we and our partners may contact you about your request. Consent is not required to purchase anything.</p>
<h2>Limits and law</h2><p>The site is provided as is. Our liability is limited to the extent permitted by law. Contact: $email.</p>""",
    "ccpa": """<p>If you are a California resident you may have the right to know what personal information we collect, to request deletion or correction, and to opt out of the sale or sharing of personal information.</p>
<h2>How to make a request</h2><p>Email $email with your name and the request. We will verify your identity before acting and will not discriminate against you for exercising your rights.</p>
<h2>Do Not Sell or Share</h2><p>Use the Opt-Out page or email us with the subject "Do Not Sell or Share".</p>""",
    "opt-out": """<h2>Opt out of sale or sharing</h2><p>To opt out of the sale or sharing of your personal information, email $email with the subject "Opt-Out" and the phone number or email you used.</p>
<h2>Opt out of calls and texts</h2><p>Tell the agent on the call to add you to our do-not-contact list, reply STOP to any text, or email us.</p>""",
    "aup": """<p>You agree not to misuse this site. Do not submit false or another person's information, attempt to disrupt or gain unauthorized access to the site, use automated tools to scrape or submit forms, or use the site for unlawful purposes. We may block access that violates this policy.</p>""",
    "cookies": """<p>We use cookies and similar technologies to run the site, measure traffic, and attribute calls and leads to the campaign that brought you here (for example, tracking parameters in the page address).</p>
<h2>Your choices</h2><p>You can block or delete cookies in your browser settings. Some features may not work without them. Contact: $email.</p>""",
    "partners": """<p>We may share your information with the following categories of partners to help with your request: licensed insurance agents and carriers, lenders, debt resolution providers, legal intake partners, travel providers, call-tracking and analytics providers.</p>
<p>A current named list of partners is available on request at $email.</p>""",
}

def build_compliance(brand):
    import compliance
    slug = brand["slug"]
    approved = compliance.is_approved(slug)
    d = OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    for key, title in COMPLIANCE_PAGES.items():
        own = legal_override(slug, key)
        banner = "" if approved else '<p class="draft">Draft template. Have counsel review before this brand goes live.</p>'
        if own is not None:  # the brand's own counsel-written text, which carries its own "last updated" date
            body = own
            if banner:
                banner = '<p class="draft">Brand legal text. Sign off in Legal review before this brand goes live.</p>'
        else:
            body = Template(LEGAL[key]).safe_substitute(name=e(brand["name"]), email=e(brand["contact_email"] or "[contact email]"))
        page = LEGAL_PAGE.substitute(
            title=title, name=e(brand["name"]), primary=e(brand["primary_color"] or "#0b2a5b"),
            accent=e(brand["accent_color"] or "#b3202a"), fonts=FONTS, banner=banner, date=time.strftime("%B %d, %Y"), body=body)
        if own is not None:
            page = page.replace(f'<p class="upd">Last updated {time.strftime("%B %d, %Y")}</p>', "", 1)
        (d / f"{key}.html").write_text(brand_extras(slug, page), encoding="utf-8")
        import wording
        wording.after_build(slug, key)
    return len(COMPLIANCE_PAGES)


# ---------------------------------------------------------------- per-brand legal (legal/<slug>/)
# legal/<slug>/<page key>.html  the brand's own legal text for that compliance page (replaces the generic template)
# legal/<slug>/footer.txt       the exact footer line counsel wants under the landing page links
# legal/<slug>/settings.json    {"cookie_banner": true} adds the cookie consent banner to every page of the brand

LEGAL_DIR = paths.SRC / "legal"  # read-only brand legal text ships with the code, so read it from the code folder (ROOT is a /tmp copy on Vercel)


def legal_override(slug, key):
    f = LEGAL_DIR / slug / f"{key}.html"
    return f.read_text(encoding="utf-8") if f.exists() else None


def legal_settings(slug):
    f = LEGAL_DIR / slug / "settings.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except Exception:
        return {}


def brand_extras(slug, page):
    """Applies the brand's legal footer text and cookie banner to a built page. Runs before wording edits, so reviewers can still edit both."""
    f = LEGAL_DIR / slug / "footer.txt"
    if f.exists():
        footer = e(f.read_text(encoding="utf-8").strip())
        page = re.sub(r'(<footer>.*?<div class="links">.*?</div>)<p>.*?</p>', lambda m: m.group(1) + f"<p>{footer}</p>", page, count=1, flags=re.S)
    if legal_settings(slug).get("cookie_banner") and 'id="bw-consent"' not in page:
        from cookie_banner import BANNER
        page = page.replace("</body>", BANNER + "\n</body>", 1)
    return page


# ---------------------------------------------------------------- go-live checklist

def delivery_modes(b):
    modes = [m for m in (b.get("delivery") or "calls").replace(" ", "").split(",") if m in ("calls", "clicks", "leads")]
    return modes or ["calls"]


def _delivery_checks(b, txt):
    """One (setup, test) pair per delivery mode: calls use Ringba, clicks use Everflow, leads use LeadProsper."""
    import integrations as ig
    out = []
    for m in delivery_modes(b):
        live = ig.mode(ig.SYSTEM_FOR[m]) == "live"
        if m == "calls":
            phone, placeholder = b["phone"], is_placeholder_phone(b["phone"])
            camp = ig.ids(b["ringba_campaign"], ig.ringba_campaign_id) if live else b["ringba_campaign"]
            ok = bool(phone) and phone in txt and not placeholder and (bool(camp) or not live)
            if not b["ringba_campaign"] and live:
                detail = "Pick this brand's Ringba campaign"
            elif not phone or placeholder:
                detail = (phone + " is a placeholder. Use the Ringba campaign number") if phone else "No phone number yet. Use the Ringba campaign number"
            elif phone not in txt:
                detail = "Regenerate the page so it shows " + phone
            else:
                detail = phone
            tdone = ig.has_test_call(b["slug"])
            out.append((("Number present", "number", ok, detail), ("Test call", "test", tdone, "Test call recorded" if tdone else "Place a test call to the number")))
        elif m == "leads":
            camp = ig.ids(b["leadprosper_campaign"], ig.lp_campaign_id) if live else b["leadprosper_campaign"]
            ok = bool(camp)
            tdone = ig.has_test_lead(b["slug"])
            out.append((("Lead campaign", "number", ok, f"{len(camp) if isinstance(camp, list) else 1} LeadProsper campaign(s) mapped" if ok else "Pick this brand's LeadProsper campaign"),
                        ("Test lead", "test", tdone, "Test lead accepted" if tdone else "Send a test lead to the campaign")))
        else:
            oid = ig.ids(b["everflow_offer"], ig.everflow_offer_id) if live else b["everflow_offer"]
            ok = bool(oid)
            got = bool(store_q("select 1 from traffic_daily where slug=? and source='everflow' and clicks>0 limit 1", (b["slug"],))) if live else bool(store_q("select 1 from clicks where slug=? limit 1", (b["slug"],)))
            out.append((("Everflow offer", "number", ok, f"{len(oid) if isinstance(oid, list) else 1} Everflow offer(s) mapped" if ok else "Pick this brand's Everflow offer"),
                        ("Test click", "test", got, "Clicks are reaching Everflow" if got else "Send a test click through the tracking link, then check")))
    return out


def store_q(sql, args=()):
    import store
    return store.q(sql, args)


def checklist(slug):
    """Seven go-live checks. A brand is ready only when every one passes. Delivery setup and the test depend on how the brand delivers:
    calls (Ringba), clicks (Everflow) or leads (LeadProsper)."""
    import compliance
    import integrations
    b = get_brand(slug)
    d = OUT / slug
    page = d / "index.html"
    txt = page.read_text(encoding="utf-8") if page.exists() else ""
    missing = [k for k in COMPLIANCE_PAGES if not (d / f"{k}.html").exists()]
    legal = compliance.status(slug)
    pairs = _delivery_checks(b, txt)
    setup = [p[0] for p in pairs]
    tests = [p[1] for p in pairs]

    def merge(parts, label):
        if len(parts) == 1:
            lab, key, ok, detail = parts[0]
            return {"label": lab, "key": key, "ok": ok, "detail": detail}
        return {"label": label, "key": parts[0][1], "ok": all(p[2] for p in parts), "detail": "; ".join(f"{p[0]}: {p[3]}" for p in parts)}

    items = [
        {"label": "Page up", "key": "page", "ok": page.exists(), "detail": "index.html generated" if page.exists() else "Not generated yet"},
        merge(setup, "Delivery set up"),
        {"label": "Tracking captured", "key": "tracking", "ok": "BWA_TRACKING" in txt, "detail": "Click ID and sub params captured from the URL" if "BWA_TRACKING" in txt else "Tracking script missing"},
        {"label": "Compliance pages", "key": "compliance", "ok": not missing and page.exists(), "detail": f"{len(COMPLIANCE_PAGES) - len(missing)}/{len(COMPLIANCE_PAGES)} present"},
        {"label": "Buyer assigned", "key": "buyer", "ok": bool(b["buyer"]), "detail": b["buyer"] or "No confirmed buyer yet"},
        {"label": "Legal review", "key": "legal", "ok": legal["approved"], "detail": legal["label"]},
        merge(tests, "Test delivery"),
    ]
    items[1]["key"], items[6]["key"] = "delivery", "test"
    warnings = []
    for name, ph in (("Ringba", "RINGBA_SNIPPET_PLACEHOLDER"), ("Everflow", "EVERFLOW_SNIPPET_PLACEHOLDER")):
        if txt and ph in txt:
            if integrations.mode(name.lower()) == "sandbox":
                warnings.append(f"{name} is in sandbox mode: the live tag is not installed and data is simulated.")
            else:
                warnings.append(f"{name} tag not installed on this page. Paste it into studio/data/snippets/{slug}/{name.lower()}_snippet.html and regenerate.")
    if txt and "Drop a real photo" in txt:
        warnings.append("Hero slot is empty. Add a real photo to studio/assets/" + slug + "/")
    return {"slug": slug, "items": items, "warnings": warnings, "ready": all(i["ok"] for i in items), "delivery": delivery_modes(b)}


# ---------------------------------------------------------------- video variants

SOURCES = {
    "insurance": ["AUTO INSURANCE", "HOME INSURANCE", "LIFE INSURANCE"],
    "debt": ["DEBT HELP"], "flights": ["FLIGHT DEALS"],
    "legal": ["MOTOR VEHICLE ACCIDENTS", "UBER/LYFT PASSENGERS", "HAIR RELAXERS"],
    "home": ["ROOFING", "HVAC", "WINDOWS"],
    "pest": ["PEST CONTROL", "WATER DAMAGE", "MOLD REMEDIATION"],
    "medicare": ["MEDICARE SUPPLEMENT/ADVANTAGE"], "final-expense": ["FINAL EXPENSE INSURANCE"],
    "loans": ["LOANS", "HOME REFINANCING"]
}
CTAS = {"insurance": "INSURANCE CTAs", "debt": "FINANCIAL CTAs", "flights": "FLIGHTS CTAs",
        "legal": "LEGAL CTAs", "home": "HOME SERVICES CTAs", "pest": "HOME SERVICES CTAs",
        "medicare": "INSURANCE CTAs", "final-expense": "INSURANCE CTAs", "loans": "FINANCIAL CTAs"}


NO_SCRIPTS = {"addiction", "home-security"}


def load_sections():
    sections, cur = {}, None
    for line in SCRIPTS.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        m = re.match(r"^\[(.+?)\]$", s)
        if m:
            cur = m.group(1).strip()
            sections[cur] = []
        elif s.startswith("=====") or s.startswith("STOP HERE"):
            cur = None
        elif cur and s:
            sections[cur].append(s)
    return sections


def build_variants(brand):
    if not SCRIPTS.exists():
        return []
    sec = load_sections()
    v = brand["vertical"]
    if v in NO_SCRIPTS:  # Jeff's scripts doc has nothing for this vertical, so do not borrow another vertical's claims
        d = OUT / brand["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "variants.json").write_text("[]", encoding="utf-8")
        return []
    srcs = SOURCES.get(v, SOURCES["insurance"])
    pool = []
    if len(srcs) >= 3:
        for s in srcs[:3]:
            L = sec.get(s, [])
            if len(L) > 2:
                pool.append((L[0], L[2]))
    else:
        L = sec.get(srcs[0], [])
        for i in range(3):
            if len(L) > i + 3:
                pool.append((L[i], L[i + 3]))
    ctas = sec.get(CTAS.get(v, "INSURANCE CTAs"), [])[:3]
    pack = sec.get(brand["name"], [])
    brand_line = " ".join(pack[:2])
    out = []
    for i, (op, body) in enumerate(pool):
        for j, cta in enumerate(ctas):
            parts = clean([op, body] + ([brand_line] if brand_line else []) + [cta])
            script = "\n".join(parts)
            words = len(script.split())
            out.append({"id": f"{brand['slug']}-v{len(out) + 1:02d}", "opener": f"O{i + 1}", "cta": f"C{j + 1}",
                        "parts": parts, "script": script, "words": words, "est_seconds": round(words / 2.5)})
    d = OUT / brand["slug"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "variants.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def load_variants(slug):
    f = OUT / slug / "variants.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


# ---------------------------------------------------------------- metrics

def metrics_summary():
    import store
    try:  # every generate is logged in the events table, which survives restarts (metrics.jsonl does not on a serverless host)
        pages = store.q("select count(distinct slug) as n from events where kind='page.generated'")[0]["n"] or 0
    except Exception:
        pages = None
    if paths.SERVERLESS and pages is not None:
        return {"runs": pages}
    if not METRICS.exists():
        return {"runs": pages or 0}
    rows = [json.loads(x) for x in METRICS.read_text(encoding="utf-8").splitlines() if x.strip()]
    llm = [r for r in rows if r["source"] == "Claude"]
    tin, tout = sum(r["tokens_in"] for r in llm), sum(r["tokens_out"] for r in llm)
    # Rates are placeholders. Set real $/million-token prices via env before quoting a cost.
    rin, rout = float(os.environ.get("RATE_IN_PER_M", 0)), float(os.environ.get("RATE_OUT_PER_M", 0))
    return {"runs": len(rows), "avg_seconds": round(sum(r["seconds"] for r in rows) / len(rows), 2),
            "llm_runs": len(llm), "tokens_in": tin, "tokens_out": tout,
            "est_llm_cost": round(tin / 1e6 * rin + tout / 1e6 * rout, 4) if (rin or rout) else None}
