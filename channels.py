"""Phone numbers by traffic channel (action item 18).

One number per channel (search, CTV, push, email) so every call shows which channel it came from and what the buyer pays for it.
Each channel gets its own publisher in Ringba on the brand's campaign, with its own number; the buyers (targets) and their static bids stay
as they are. The landing page picks the channel from ?ch= (or utm_medium) and shows that channel's number; any other visitor keeps the
ring-pool number from the brand's DNI tag.

Config: data/snippets/<slug>/channels.json, {"dni": "<the DNI script tag>", "channels": {"search": {"number": "(888) 555-0100", "ready": true}, ...}}.
A channel only goes on the page once "ready" is true, which means its number is attached to the campaign in Ringba; until then its visitors see
the pool number, so no call is ever sent to a number that does not ring. Run `python channels.py <slug>` to rewrite ringba_snippet.html."""
import json
import re
import sys

import paths

CHANNELS = {
    "search": ("Search", ("search", "cpc", "ppc", "sem", "google", "bing")),
    "ctv": ("CTV", ("ctv", "ott", "tv", "streaming")),
    "push": ("Push", ("push", "inpage", "in-page", "pop", "popunder", "native")),
    "email": ("Email", ("email", "newsletter", "mail")),
}


def path(slug):
    return paths.SRC / "data" / "snippets" / slug / "channels.json"


def load(slug):
    f = path(slug)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def _digits(n):
    d = re.sub(r"\D", "", n or "")
    return d if len(d) == 11 else ("1" + d if len(d) == 10 else "")


def snippet(cfg):
    """The head snippet: channel number for tagged visitors, the DNI tag for everyone else."""
    if not any(v.get("ready") and _digits(v.get("number")) for v in cfg.get("channels", {}).values()):
        return cfg.get("dni", "").strip() + "\n"  # no channel number is live yet: the plain ring-pool tag, exactly as before
    dni = re.search(r'src="([^"]+)"', cfg.get("dni", ""))
    dni_src = dni.group(1) if dni else ""
    ready = {k: _digits(v["number"]) for k, v in cfg.get("channels", {}).items() if v.get("ready") and _digits(v.get("number")) and k in CHANNELS}
    alias = {a: k for k, (_, words) in CHANNELS.items() if k in ready for a in words}
    js = ("(function(){var N=" + json.dumps(ready) + ",A=" + json.dumps(alias) + ",D=" + json.dumps(dni_src) + ",c='';"
          "try{var q=new URLSearchParams(location.search),v=(q.get('ch')||q.get('utm_medium')||'').toLowerCase();c=A[v]||'';"
          "if(c){sessionStorage.setItem('bw_ch',c);}else{c=sessionStorage.getItem('bw_ch')||'';if(!N[c])c='';}}catch(e){}"
          "if(!c||!N[c]){if(D){var s=document.createElement('script');s.src=D;s.async=true;document.head.appendChild(s);}return;}"
          "var d=N[c],t='('+d.substr(1,3)+') '+d.substr(4,3)+'-'+d.substr(7);"
          "function put(){document.querySelectorAll('a[href^=\"tel:\"]').forEach(function(a){a.href='tel:+'+d;});"
          "document.querySelectorAll('.ringba-number').forEach(function(x){x.textContent=t;});document.documentElement.setAttribute('data-channel',c);}"
          "if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',put);}else{put();}})();")
    return f"<!-- Phone numbers by channel: built by studio/channels.py from channels.json. Edit that file, not this one. -->\n<script>{js}</script>\n"


def write(slug):
    cfg = load(slug)
    if not cfg:
        raise SystemExit(f"No channels.json for {slug}")
    out = path(slug).with_name("ringba_snippet.html")
    out.write_text(snippet(cfg), encoding="utf-8")
    return out


if __name__ == "__main__":
    for s in sys.argv[1:]:
        print("wrote", write(s))
