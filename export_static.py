"""Export a brand's generated page as a standalone static site, ready to deploy on its own domain.
Usage:   python export_static.py flight-finder-pro ../ffp-site
Then:    cd ../ffp-site && vercel deploy --prod
Generate the page in the studio first (it reads out/<brand>/). Internal setup notes (tag placeholders) are removed. If the Ringba and Everflow tags
were pasted into data/snippets/<brand>/ before generating, they are already inside the page."""
import json
import os
import re
import shutil
import sys

SRC = os.path.dirname(os.path.abspath(__file__))


def export(slug, dest):
    out = os.path.join(SRC, "out", slug)
    if not os.path.exists(os.path.join(out, "index.html")):
        raise SystemExit(f"No generated page for {slug}. Generate it in the studio first.")
    keep = [f for f in (".vercel", ".env.local", ".gitignore") if os.path.exists(os.path.join(dest, f))]
    saved = {}
    for f in keep:  # keep the Vercel project link when re-exporting
        p = os.path.join(dest, f)
        saved[f] = open(p, "rb").read() if os.path.isfile(p) else shutil.copytree(p, p + ".bak")
    for name in os.listdir(dest) if os.path.exists(dest) else []:
        p = os.path.join(dest, name)
        if name in keep or name.endswith(".bak"):
            continue
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(os.path.join(dest, "assets", slug), exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".html"):
            html = open(os.path.join(out, f), encoding="utf-8").read()
            html = re.sub(r"<!-- (?:RINGBA|EVERFLOW)_SNIPPET_PLACEHOLDER[^>]*-->\s*", "", html)
            open(os.path.join(dest, f), "w", encoding="utf-8").write(html)
    a = os.path.join(SRC, "assets", slug)
    for f in os.listdir(a) if os.path.exists(a) else []:
        if os.path.isfile(os.path.join(a, f)):
            shutil.copyfile(os.path.join(a, f), os.path.join(dest, "assets", slug, f))
    open(os.path.join(dest, "robots.txt"), "w").write("User-agent: *\nAllow: /\n")
    json.dump({"$schema": "https://openapi.vercel.sh/vercel.json", "cleanUrls": True,
               "headers": [{"source": "/assets/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=86400"}]},
                           {"source": "/(.*)", "headers": [{"key": "X-Content-Type-Options", "value": "nosniff"}, {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"}]}]},
              open(os.path.join(dest, "vercel.json"), "w"), indent=2)
    for f, data in saved.items():
        p = os.path.join(dest, f)
        if isinstance(data, bytes):
            open(p, "wb").write(data)
        elif os.path.exists(p + ".bak"):
            shutil.rmtree(p + ".bak")
    print("exported", slug, "->", os.path.abspath(dest), sorted(os.listdir(dest)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    export(sys.argv[1], sys.argv[2])
