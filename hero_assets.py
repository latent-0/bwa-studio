"""Hero upgrade assets, cut from each brand's own final video (the branded shots Jeff's team produced), on the Flight Finder Pro model:
a short silent branded loop for the hero, a still for the no-video variant, and a second branded image for the overlay card and image tile.

    python hero_assets.py            all brands listed in SHOTS
    python hero_assets.py patriot-insurance refi-llc

Writes assets/<slug>/hero-loop.mp4, hero-still.jpg, overlay.jpg. SHOTS lists the start second of three branded shots in assets/<slug>/hero.mp4
(no spokesperson, chosen from contact sheets). A brand whose hero.mp4 is already a short branded clip gets no loop; its clip stays the hero."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = 1.6      # seconds per shot
FADE = 0.4     # crossfade between shots
CAPTION = 0.87  # keep the top 87% of the frame: the burned-in captions and corner logo sit in the bottom strip

SHOTS = {
    "aca-doctor": [4.2, 10.2, 50.2],
    "easy-loan-center": [18.2, 40.2, 58.2],
    "christian-insurance": [5.0, 46.2, 24.7],
    "greenback-loans": [6.2, 54.2, 66.2],
    "home-security-live": [4.2, 8.2, 75.0],
    "home-service-live": [30.7, 82.8, 62.2],
    "home-savers": [4.7, 18.2, 28.2],
    "patriot-insurance": [4.2, 44.2, 38.2],
    "prime-health-clinic": [22.2, 12.2, 72.2],
    "refi-llc": [18.2, 26.8, 77.4],
    # short branded clips already: no loop, stills only (time of the still, time of the overlay frame)
    "debt-center": [6.5, 6.5],
    "final-expense-store": [2.0, 6.0],
    "first-legal": [3.5, 1.0],
    "senior-s-guide": [3.0, 9.0],
}
# crop to the hero frame's shape (about 4:3.1), centred, above the caption strip
CROP = f"crop=trunc(ih*{CAPTION}*1.29/2)*2:trunc(ih*{CAPTION}/2)*2:(iw-ow)/2:0"


def run(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def still(src, t, dst, width):
    run(["-ss", str(t), "-i", src, "-frames:v", "1", "-vf", f"{CROP},scale={width}:-2", "-q:v", "3", dst])


def build(slug):
    d = os.path.join(HERE, "assets", slug)
    src = os.path.join(d, "hero.mp4")
    shots = SHOTS[slug]
    if len(shots) == 3:
        ins, chain = [], []
        for i, t in enumerate(shots):
            ins += ["-ss", str(t), "-t", str(SEG), "-i", src]
            chain.append(f"[{i}:v]{CROP},scale=960:-2,fps=30,format=yuv420p,setpts=PTS-STARTPTS[s{i}]")
        off1, off2 = SEG - FADE, 2 * SEG - 2 * FADE
        chain.append(f"[s0][s1]xfade=transition=fade:duration={FADE}:offset={off1}[x1]")
        chain.append(f"[x1][s2]xfade=transition=fade:duration={FADE}:offset={off2}[v]")
        run([*ins, "-filter_complex", ";".join(chain), "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-movflags", "+faststart",
             os.path.join(d, "hero-loop.mp4")])
        still(src, shots[0] + SEG / 2, os.path.join(d, "hero-still.jpg"), 1280)
        still(src, shots[1] + SEG / 2, os.path.join(d, "overlay.jpg"), 520)
    else:
        still(src, shots[0], os.path.join(d, "hero-still.jpg"), 1280)
        still(src, shots[1], os.path.join(d, "overlay.jpg"), 520)
    sizes = {f: os.path.getsize(os.path.join(d, f)) // 1024 for f in ("hero-loop.mp4", "hero-still.jpg", "overlay.jpg") if os.path.exists(os.path.join(d, f))}
    print(f"{slug}: " + ", ".join(f"{k} {v} KB" for k, v in sizes.items()))


if __name__ == "__main__":
    for s in sys.argv[1:] or SHOTS:
        build(s)
