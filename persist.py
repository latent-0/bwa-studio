"""Keeps the studio's working files alive on a serverless host. Vercel instances come and go and their disk is temporary, so every file the
studio writes (generated pages, releases, pitches, reference images, legal sign-offs, local brand settings, Sheet snapshots) is mirrored into the
`files` table. pull() runs at the start of a request and fetches whatever another instance changed; push() runs at the end and stores what this
request changed. Locally (no DATABASE_URL) both do nothing."""
import hashlib
import threading
import time

import paths
import store

ROOT = paths.ROOT
TREES = ["out", "published", "before", "data/pitch", "data/snippets", "data/sheet", "data/cache", "data/wording"]
SINGLES = ["brands.csv", "data/legal.json"]
SKIP = (".part", ".tmp")
CHECK_EVERY = 2.0

_lock = threading.RLock()
_s = {"version": None, "hashes": {}, "stat": {}, "checked": 0.0}


def enabled():
    return store.USE_PG


def _walk():
    for t in TREES:
        base = ROOT / t
        if base.exists():
            for p in base.rglob("*"):
                if p.is_file() and not p.name.endswith(SKIP):
                    yield p
    for f in SINGLES:
        p = ROOT / f
        if p.exists():
            yield p


def _rel(p):
    return p.relative_to(ROOT).as_posix()


def _sha(data):
    return hashlib.sha1(data).hexdigest()


def _mark_local():
    """Treat everything already on disk (the deployed seed files) as in sync, so only real changes are ever uploaded."""
    for p in _walk():
        st = p.stat()
        _s["hashes"][_rel(p)] = _sha(p.read_bytes())
        _s["stat"][_rel(p)] = (st.st_size, st.st_mtime_ns)


def pull(force=False):
    if not enabled():
        return
    with _lock:
        now = time.time()
        if not force and _s["version"] is not None and now - _s["checked"] < CHECK_EVERY:
            return
        rows = store.pg_run(lambda c: c.execute("select value from meta where key='version'").fetchall())
        remote = rows[0]["value"] if rows else "0"
        _s["checked"] = now
        if _s["version"] == remote:
            return
        if _s["version"] is None:
            _mark_local()
        listing = store.pg_run(lambda c: c.execute("select path, sha from files").fetchall())
        for r in listing:
            if _s["hashes"].get(r["path"]) == r["sha"]:
                continue
            row = store.pg_run(lambda c, p=r["path"]: c.execute("select data from files where path=%s", (p,)).fetchone())
            if not row:
                continue
            dest = ROOT / r["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(bytes(row["data"]))
            st = dest.stat()
            _s["hashes"][r["path"]] = r["sha"]
            _s["stat"][r["path"]] = (st.st_size, st.st_mtime_ns)
        _s["version"] = remote


def push():
    if not enabled():
        return
    with _lock:
        changed = []
        for p in _walk():
            rel = _rel(p)
            st = p.stat()
            if _s["stat"].get(rel) == (st.st_size, st.st_mtime_ns):
                continue
            data = p.read_bytes()
            _s["stat"][rel] = (st.st_size, st.st_mtime_ns)
            sha = _sha(data)
            if _s["hashes"].get(rel) != sha:
                changed.append((rel, data, sha))
        if not changed:
            return
        now = time.time()

        def write(c):
            for rel, data, sha in changed:
                c.execute("insert into files(path, data, sha, updated) values(%s,%s,%s,%s) on conflict (path) do update set data=excluded.data, sha=excluded.sha, updated=excluded.updated",
                          (rel, data, sha, now))
            return c.execute("insert into meta(key, value) values('version','1') on conflict (key) do update set value=(meta.value::bigint+1)::text returning value").fetchone()["value"]
        version = store.pg_run(write)
        for rel, data, sha in changed:
            _s["hashes"][rel] = sha
        _s["version"] = version
