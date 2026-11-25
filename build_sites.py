"""Build brand landing pages as standalone static sites, one folder per brand and variant, ready to deploy as separate Vercel projects.
Variant A has a hero video, variant B has none. Usage:
    python build_sites.py debt-center:B first-legal:A:"C:/path/video.mp4" ...
Each argument is slug:variant[:video file for variant A]. Output goes to ../sites-deploy/<slug>-<variant>/ and is marked noindex until it is approved."""
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEST_ROOT = os.path.abspath(os.path.join(HERE, "..", "sites-deploy"))


def compress(src, dst_mp4, dst_poster, poster_at=1.0):
    """Web hero video that plays on every phone and browser: H.264 Main profile level 4.0, 8-bit 4:2:0, even dimensions, no audio track
    (the page plays it muted), at most 1280 wide, moov atom first so it starts streaming at once. Returns size in MB."""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-an", "-vf", "scale='min(1280,iw)':-2,fps=30,format=yuv420p", "-c:v", "libx264",
                    "-profile:v", "main", "-level", "4.0", "-preset", "slow", "-crf", "27", "-movflags", "+faststart", dst_mp4], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(poster_at), "-i", dst_mp4, "-frames:v", "1", "-q:v", "4", dst_poster], check=True)
    return os.path.getsize(dst_mp4) / 1e6


def build(slug, variant, video=None):
    brand = dict(core.get_brand(slug))
    brand["variant"] = variant
    adir = os.path.join(HERE, "assets", slug)
    os.makedirs(adir, exist_ok=True)
    brand["hero_video"] = ""
    if variant == "A" and video:
        mb = compress(video, os.path.join(adir, "hero.mp4"), os.path.join(adir, "poster.jpg"), float(os.environ.get("POSTER_AT", "1")))
        brand["hero_video"] = "hero.mp4"
        print(f"  {slug}: hero video compressed to {mb:.1f} MB")
    elif variant == "A" and os.path.exists(os.path.join(adir, "hero.mp4")):
        brand["hero_video"] = "hero.mp4"  # no new video given: reuse the one already compressed, no re-encode
    core.build_page(brand, "")
    out = os.path.join(HERE, "out", slug)
    dest = os.path.join(DEST_ROOT, f"{slug}-{variant.lower()}")
    keep = {}
    stash = os.path.join(DEST_ROOT, ".stash-" + os.path.basename(dest))
    shutil.rmtree(stash, ignore_errors=True)
    os.makedirs(stash)
    for f in (".vercel", ".env.local", ".gitignore"):
        p = os.path.join(dest, f)
        if os.path.exists(p):
            keep[f] = os.path.join(stash, f)
            os.replace(p, keep[f])
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(os.path.join(dest, "assets", slug), exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".html"):
            html = open(os.path.join(out, f), encoding="utf-8").read()
            html = re.sub(r"<!-- (?:RINGBA|EVERFLOW)_SNIPPET_PLACEHOLDER[^>]*-->\s*", "", html)
            html = html.replace("<head>", '<head><meta name="robots" content="noindex,nofollow">', 1)
            open(os.path.join(dest, f), "w", encoding="utf-8").write(html)
    if brand["hero_video"]:
        for f in ("hero.mp4", "poster.jpg"):
            if os.path.exists(os.path.join(adir, f)):
                shutil.copyfile(os.path.join(adir, f), os.path.join(dest, "assets", slug, f))
    # hero upgrade assets (hero_assets.py): the loop only for variant A, the branded images for both
    for f in (("hero-loop.mp4",) if variant == "A" else ()) + ("hero-still.jpg", "overlay.jpg"):
        if os.path.exists(os.path.join(adir, f)):
            shutil.copyfile(os.path.join(adir, f), os.path.join(dest, "assets", slug, f))
    open(os.path.join(dest, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n")
    json.dump({"$schema": "https://openapi.vercel.sh/vercel.json", "cleanUrls": True,
               "headers": [{"source": "/(.*)", "headers": [{"key": "X-Robots-Tag", "value": "noindex, nofollow"}, {"key": "X-Content-Type-Options", "value": "nosniff"},
                                                          {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"}]},
                          {"source": "/assets/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=86400"}]}]},
              open(os.path.join(dest, "vercel.json"), "w"), indent=2)
    for f, tmp in keep.items():
        os.replace(tmp, os.path.join(dest, f))
    shutil.rmtree(stash, ignore_errors=True)
    print(f"  {slug}-{variant}: built -> {dest} ({len(os.listdir(dest))} entries)")
    return dest


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        parts = arg.split(":", 2) if not re.match(r"^[\w-]+:[AB]:[A-Za-z]:", arg) else [arg.split(":")[0], arg.split(":")[1], arg.split(":", 2)[2]]
        build(parts[0], parts[1].upper(), parts[2] if len(parts) > 2 else None)
