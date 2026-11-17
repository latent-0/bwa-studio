"""Video engine v1: turns a script variant into a captioned vertical, square or wide video with a voice track and an end card.
Local and free: ffmpeg for rendering, the Windows speech engine as a PLACEHOLDER voice (swap in a licensed voice or avatar provider
later), background from the brand's hero video, image, or a brand-color gradient. Real footage stays the primary source: this engine
assembles and captions it, and the voice track is clearly labeled as placeholder in the tracker."""
import csv
import io
import re
import shutil
import subprocess
import textwrap
import threading
import time
from pathlib import Path

import core
import store

OUTDIR = core.DATA / "video"
FORMATS = {"9x16": (1080, 1920), "1x1": (1080, 1080), "16x9": (1920, 1080)}
FONT = next((p for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arial.ttf") if Path(p).exists()), None)
VOICE = "Placeholder voice (Windows speech)"
_sem = threading.Semaphore(2)


def ffmpeg():
    return shutil.which("ffmpeg") or "ffmpeg"


def _run(cmd, cwd=None, timeout=900):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout)[-600:])
    return p


def _duration(path):
    p = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                       capture_output=True, text=True)
    try:
        return float(p.stdout.strip())
    except Exception:
        return 0.0


def tts(text, wav):
    """Synthesize speech to a WAV with the Windows speech engine. Returns True on success."""
    txt = Path(wav).with_suffix(".txt")
    txt.write_text(text, encoding="utf-8")
    ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate = 1; "
          f"$s.SetOutputToWaveFile('{wav}'); $s.Speak([IO.File]::ReadAllText('{txt}')); $s.Dispose()")
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=180)
        return Path(wav).exists() and Path(wav).stat().st_size > 1000
    except Exception:
        return False


def _chunks(script, width):
    """Split the script into short caption chunks of about 6 to 9 words."""
    words = re.sub(r"\s+", " ", script).split()
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 7 or (w.endswith((".", "?", "!")) and len(cur) >= 4):
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return ["\n".join(textwrap.wrap(c, width)) for c in out]


def _hex(c, default):
    c = (c or default).lstrip("#")
    return "0x" + (c if len(c) == 6 else default.lstrip("#"))


def _background(brand, W, H, total):
    """Returns (input args, filter fragment producing [bg])."""
    slug = brand["slug"]
    vid = core.ASSETS / slug / brand["hero_video"] if brand.get("hero_video") else None
    img = None
    for nm in (brand.get("tile_image"), brand.get("hero_image")):
        if nm and (core.ASSETS / slug / nm).exists():
            img = core.ASSETS / slug / nm
            break
    scale = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,format=yuv420p"
    if vid and vid.exists():
        return ["-stream_loop", "-1", "-i", str(vid)], f"[0:v]{scale}[bg]"
    if img:
        return ["-loop", "1", "-framerate", "25", "-i", str(img)], f"[0:v]{scale},zoompan=z='min(zoom+0.0006,1.15)':d=1:s={W}x{H}:fps=25[bg]"
    return (["-f", "lavfi", "-i", f"gradients=s={W}x{H}:c0={_hex(brand['primary_color'], '0a2a6b')}:c1={_hex(brand['accent_color'], 'b3202a')}:x0=0:y0=0:x1={W}:y1={H}:speed=0.015:r=25:d={total:.2f}"],
            "[0:v]format=yuv420p[bg]")


def render(slug, variant_id, fmt="9x16"):
    """Render one variant. Blocks until done. Returns the job row."""
    brand = core.get_brand(slug)
    variants = {v["id"]: v for v in core.load_variants(slug)} or {v["id"]: v for v in core.build_variants(brand)}
    v = variants.get(variant_id)
    if not v:
        raise ValueError("Unknown variant. Generate the page first.")
    W, H = FORMATS[fmt]
    jid = store.x("insert into video_jobs(ts,slug,variant,fmt,status,voice) values(?,?,?,?,?,?)", (store.now(), slug, variant_id, fmt, "running", VOICE))
    t0 = time.time()
    job = OUTDIR / slug / f"{variant_id}-{fmt}"
    job.mkdir(parents=True, exist_ok=True)
    try:
        with _sem:
            script = " ".join(v["parts"])
            wav = job / "voice.wav"
            have_voice = tts(script, wav)
            speech = _duration(wav) if have_voice else max(4.0, len(script.split()) / 2.6)
            end_card = 2.8
            total = speech + 0.4 + end_card
            k = min(W, H) / 1080
            width_chars = max(14, int(24 * (W if W < H else H) / 1080 * (1.0 if W < H else 1.6)))
            chunks = _chunks(script, width_chars)
            per = speech / max(1, len(chunks))
            bg_args, bg_filter = _background(brand, W, H, total)
            fs = int(70 * k)
            filters = [bg_filter, f"[bg]drawbox=x=0:y=0:w=iw:h=ih:color=black@0.38:t=fill[d0]"]
            last = "d0"
            font = f"fontfile='{FONT.replace(chr(92), '/').replace(':', chr(92) + ':')}':" if FONT else ""
            for i, ch in enumerate(chunks):
                (job / f"c{i}.txt").write_text(ch, encoding="utf-8")
                a, b = i * per, (i + 1) * per
                filters.append(f"[{last}]drawtext={font}textfile=c{i}.txt:fontsize={fs}:fontcolor=white:line_spacing={int(-14 * k)}:box=1:boxcolor=black@0.5:boxborderw={int(26 * k)}:"
                               f"x=(w-text_w)/2:y=h*{0.60 if H > W else 0.68}:enable='between(t,{a:.2f},{b:.2f})'[c{i}]")
                last = f"c{i}"
            (job / "brand.txt").write_text(brand["name"], encoding="utf-8")
            filters.append(f"[{last}]drawtext={font}textfile=brand.txt:fontsize={int(46 * k)}:fontcolor=white@0.9:x={int(60 * k)}:y={int(70 * k)}[t1]")
            ec0 = speech + 0.4
            (job / "endname.txt").write_text(brand["name"], encoding="utf-8")
            (job / "endphone.txt").write_text(brand["phone"] or "", encoding="utf-8")
            (job / "endcta.txt").write_text("\n".join(textwrap.wrap(brand["cta"] or "Call now", 26)), encoding="utf-8")
            acc = _hex(brand["accent_color"], "b3202a")
            filters.append(f"[t1]drawbox=x=0:y=0:w=iw:h=ih:color={acc}@1:t=fill:enable='gte(t,{ec0:.2f})'[e0]")
            filters.append(f"[e0]drawtext={font}textfile=endname.txt:fontsize={int(88 * k)}:fontcolor=white:x=(w-text_w)/2:y=h*0.30:enable='gte(t,{ec0:.2f})'[e1]")
            filters.append(f"[e1]drawtext={font}textfile=endcta.txt:fontsize={int(52 * k)}:fontcolor=white@0.92:line_spacing={int(-10 * k)}:x=(w-text_w)/2:y=h*0.46:enable='gte(t,{ec0:.2f})'[e2]")
            filters.append(f"[e2]drawtext={font}textfile=endphone.txt:fontsize={int(96 * k)}:fontcolor=white:x=(w-text_w)/2:y=h*0.62:enable='gte(t,{ec0:.2f})'[vout]")
            out = job / "out.mp4"

            def attempt(bgargs, bgfilter):
                filters[0] = bgfilter
                (job / "graph.txt").write_text(";\n".join(filters), encoding="utf-8")
                cmd = [ffmpeg(), "-y", "-loglevel", "error", *bgargs]
                cmd += ["-i", "voice.wav"] if have_voice else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono"]
                cmd += ["-filter_complex_script", "graph.txt", "-map", "[vout]", "-map", "1:a", "-af", f"apad=pad_dur={end_card + 1}", "-t", f"{total:.2f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "out.mp4"]
                _run(cmd, cwd=str(job))

            try:
                attempt(bg_args, bg_filter)
            except RuntimeError:
                if any("gradients" in a for a in bg_args):
                    solid = ["-f", "lavfi", "-i", f"color=c={_hex(brand['primary_color'], '0a2a6b')}:s={W}x{H}:r=25:d={total:.2f}"]
                    attempt(solid, "[0:v]format=yuv420p[bg]")
                else:
                    raise
            secs = round(time.time() - t0, 1)
            store.x("update video_jobs set status='done', path=?, seconds=? where id=?", (str(out), secs, jid))
            store.x("insert into costs(ts,slug,kind,amount,detail) values(?,?,?,?,?)", (store.now(), slug, "video", 0.0, f"{variant_id} {fmt} local render {secs}s, {VOICE}"))
            store.log_event(slug, "video.rendered", f"{variant_id} {fmt} in {secs}s")
    except Exception as ex:
        store.x("update video_jobs set status='failed', error=?, seconds=? where id=?", (str(ex)[:500], round(time.time() - t0, 1), jid))
        store.log_event(slug, "video.failed", f"{variant_id} {fmt}: {str(ex)[:160]}")
    return store.q("select * from video_jobs where id=?", (jid,))[0]


def render_async(slug, variant_ids, fmt="9x16"):
    def work():
        for vid in variant_ids:
            render(slug, vid, fmt)
    threading.Thread(target=work, daemon=True).start()


def jobs(slug):
    rows = store.q("select * from video_jobs where slug=? order by id desc limit 200", (slug,))
    latest = {}
    for r in rows:
        latest.setdefault((r["variant"], r["fmt"]), r)
    return list(latest.values())


def tracker_csv():
    """Video Tracker export using the Sheet's own column names, so rows can be pasted into HSL_videos."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["", "Video Idea", "Script Link", "Voiceover Link", "Media Preparation Stages", "Production Stages", "Final Video", "Notes", "Format", "Render seconds", "Created"])
    for b in core.load_brands():
        vmap = {v["id"]: v for v in core.load_variants(b["slug"])}
        for j in sorted(jobs(b["slug"]), key=lambda r: r["variant"]):
            v = vmap.get(j["variant"], {})
            idea = f"{j['variant']} ({v.get('opener', '')} + {v.get('cta', '')})"
            w.writerow([b["name"], idea, v.get("script", "")[:300], j["voice"], "Rendered locally" if j["status"] == "done" else j["status"].title(),
                        "Draft" if j["status"] == "done" else "", j["path"] or "", f"{v.get('words', '')} words, placeholder voice", j["fmt"], j["seconds"], j["ts"]])
    return buf.getvalue()
