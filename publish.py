"""Go-live: publish the current generated page as an immutable release, pause it, or roll back to the previous release.
Releases live in published/<slug>/<release>/ and are served at /live/<slug>/. Set PUBLISH_CMD to also push to real hosting,
for example:  PUBLISH_CMD="npx wrangler pages deploy {dir} --project-name {slug}"  (not tested here)."""
import json
import os
import shutil
import subprocess
import time

import core
import store

PUB = core.ROOT / "published"


def _file(slug):
    return PUB / slug / "state.json"


def _state(slug):
    f = _file(slug)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"current": None, "paused": False, "history": []}


def _save(slug, s):
    _file(slug).parent.mkdir(parents=True, exist_ok=True)
    _file(slug).write_text(json.dumps(s, indent=2), encoding="utf-8")


def live_status(slug):
    s = _state(slug)
    return {"live": bool(s["current"]) and not s["paused"], "paused": s["paused"], "release": s["current"], "history": s["history"][-8:],
            "url": f"/live/{slug}/" if s["current"] else None}


def live_dir(slug):
    s = _state(slug)
    return PUB / slug / s["current"] if s["current"] else None


def _refresh(slug):
    try:
        import integrations
        integrations.refresh_stage(slug)
    except Exception:
        pass


def publish(slug, note="", actor="studio", force=False):
    cl = core.checklist(slug)
    if not cl["ready"] and not force:
        missing = [i["label"] for i in cl["items"] if not i["ok"]]
        raise ValueError("Go-live checklist is not complete. Still missing: " + ", ".join(missing))
    src = core.OUT / slug
    if not (src / "index.html").exists():
        raise ValueError("Generate the page first.")
    rel = time.strftime("r%Y%m%d-%H%M%S")
    dst = PUB / slug / rel
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("variants.json"))
    s = _state(slug)
    s["current"], s["paused"] = rel, False
    s["history"].append({"release": rel, "ts": store.now(), "note": note, "actor": actor})
    _save(slug, s)
    store.x("insert into releases(slug,release,ts,status,note,actor) values(?,?,?,?,?,?)", (slug, rel, store.now(), "live", note, actor))
    store.log_event(slug, "published", f"{rel} {note}".strip(), actor)
    hook = os.environ.get("PUBLISH_CMD")
    hook_result = None
    if hook:
        try:
            p = subprocess.run(hook.format(dir=str(dst), slug=slug), shell=True, capture_output=True, text=True, timeout=300)
            hook_result = f"exit {p.returncode}"
            store.log_event(slug, "publish.hook", f"{hook_result}: {(p.stderr or p.stdout)[:160]}", actor)
        except Exception as ex:
            hook_result = f"failed: {ex}"
            store.log_event(slug, "publish.hook", hook_result, actor)
    try:
        import integrations
        if integrations.any_sandbox() and not store.q("select 1 from traffic_daily where slug=? limit 1", (slug,)):
            integrations.simulate_traffic(slug)
    except Exception as ex:
        store.log_event(slug, "sandbox.error", str(ex)[:160])
    _refresh(slug)
    return {"release": rel, "hook": hook_result}


def pause(slug, actor="studio"):
    s = _state(slug)
    if not s["current"]:
        raise ValueError("This brand is not live.")
    s["paused"] = True
    _save(slug, s)
    store.log_event(slug, "paused", "", actor)
    _refresh(slug)


def resume(slug, actor="studio"):
    s = _state(slug)
    s["paused"] = False
    _save(slug, s)
    store.log_event(slug, "resumed", "", actor)
    _refresh(slug)


def rollback(slug, actor="studio"):
    s = _state(slug)
    if len(s["history"]) < 2:
        raise ValueError("There is no earlier release to roll back to.")
    prev = s["history"][-2]["release"]
    s["current"] = prev
    s["history"].append({"release": prev, "ts": store.now(), "note": "rollback", "actor": actor})
    _save(slug, s)
    store.log_event(slug, "rollback", prev, actor)
    return prev
