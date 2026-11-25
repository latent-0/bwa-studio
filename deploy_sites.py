"""Deploy each folder in ../sites-deploy as its own Vercel project (no domain) and record the addresses in ../sites-deploy/urls.json.
Usage:  python deploy_sites.py debt-center-b first-legal-a ...      (folder names; default: every folder)
Project names are bw-<folder name>."""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sites-deploy"))
URLS = os.path.join(ROOT, "urls.json")


def run(args, cwd, timeout=600):
    p = subprocess.run(["cmd", "/c", "vercel", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def deploy(name):
    cwd = os.path.join(ROOT, name)
    code, out = run(["link", "--yes", "--project", f"bw-{name}"], cwd)
    if code != 0 and "Linked" not in out and "Created" not in out:
        return None, "link failed: " + out[-300:]
    code, out = run(["deploy", "--prod", "--yes"], cwd)
    alias = re.findall(r"Aliased\s+(https://\S+)", out)
    prod = re.findall(r"Production\s+(https://\S+)", out)
    if code != 0 or not (alias or prod):
        return None, "deploy failed: " + out[-400:]
    # always record the project's own vercel.app address: Vercel prints only the custom domain (e.g. lp.<brand>) once one is attached,
    # and that address does not work until its DNS record exists
    return f"https://bw-{name}.vercel.app", ""


if __name__ == "__main__":
    names = sys.argv[1:] or [d for d in sorted(os.listdir(ROOT)) if os.path.isdir(os.path.join(ROOT, d))]
    urls = json.load(open(URLS)) if os.path.exists(URLS) else {}
    for n in names:
        url, err = deploy(n)
        print(f"{n}: {url or 'FAILED ' + err}", flush=True)
        if url:
            urls[n] = url
            json.dump(urls, open(URLS, "w"), indent=2)
            try:  # log the deploy in the Landing Page Tracker so the Sheet and the studio stay in step
                import core
                import lp
                slug, variant = n.rsplit("-", 1)
                lp.log_deploy(core.get_brand(slug)["name"], variant, url)
                print(f"  {n}: logged in the Landing Page Tracker", flush=True)
            except Exception as ex:
                print(f"  {n}: not logged in the tracker ({ex})", flush=True)
