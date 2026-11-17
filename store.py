"""Store for events, traffic, calls, leads, releases, CRM records, video jobs, costs and sign-in lockouts.
SQLite locally (data/studio.db). On Vercel, set DATABASE_URL (Neon Postgres): the same SQL runs on both, translated on the fly."""
import json
import os
import re
import sqlite3
import threading
import time
from decimal import Decimal

import paths

ROOT = paths.ROOT
DB = ROOT / "data" / "studio.db"
DSN = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""
USE_PG = DSN.startswith("postgres")
_lock = threading.RLock()

SCHEMA = """
create table if not exists events(id integer primary key, ts text, slug text, kind text, actor text, detail text);
create table if not exists clicks(id integer primary key, ts text, slug text, click_id text unique, source text, sub1 text, affid text, sandbox integer default 0);
create table if not exists calls(id integer primary key, ts text, slug text, call_id text unique, click_id text, caller text, duration integer,
  converted integer default 0, payout real default 0, buyer text, campaign text, is_test integer default 0, sandbox integer default 0, ghl_synced integer default 0);
create table if not exists releases(id integer primary key, slug text, release text, ts text, status text, note text, actor text);
create table if not exists ghl_contacts(id text primary key, slug text, phone text, name text, tags text, fields text, ts text);
create table if not exists ghl_opps(id text primary key, contact_id text, slug text, pipeline text, stage text, name text, value real, ts text, updated text);
create table if not exists video_jobs(id integer primary key, ts text, slug text, variant text, fmt text, status text, path text, seconds real, error text, voice text);
create table if not exists traffic_daily(slug text, day text, source text, clicks integer default 0, conversions integer default 0, revenue real default 0, sandbox integer default 0, primary key(slug,day,source));
create table if not exists leads(id integer primary key, ts text, slug text, lead_id text unique, campaign text, status text, revenue real default 0, is_test integer default 0,
  sandbox integer default 0, ghl_synced integer default 0, detail text);
create table if not exists leads_daily(slug text, day text, campaign text, leads integer default 0, accepted integer default 0, duplicated integer default 0, failed integer default 0,
  revenue real default 0, cost real default 0, sandbox integer default 0, primary key(slug,day,campaign));
create table if not exists costs(id integer primary key, ts text, slug text, kind text, amount real, detail text);
create table if not exists auth_fails(k text, ts real);
create table if not exists files(path text primary key, data bytea, sha text, updated real);
create table if not exists meta(key text primary key, value text);
"""

# conflict targets for "insert or replace", and the tables whose integer id the code reads back
PK = {"traffic_daily": ("slug", "day", "source"), "leads_daily": ("slug", "day", "campaign"), "leads": ("lead_id",), "ghl_contacts": ("id",), "ghl_opps": ("id",), "meta": ("key",)}
ID_TABLES = {"events", "clicks", "calls", "releases", "video_jobs", "leads", "costs"}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------------------ SQLite

_ready = {"sqlite": False, "pg": False}


def conn():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=20, check_same_thread=False)
    c.row_factory = sqlite3.Row
    if not _ready["sqlite"]:
        c.executescript(re.sub(r"\bbytea\b", "blob", SCHEMA))
        _ready["sqlite"] = True
    return c


# ------------------------------------------------------------------ Postgres

_pg = {"c": None}


def _pg_sql(sql):
    s = sql.strip().rstrip(";")
    low = s.lower()
    tail = ""
    if low.startswith("insert or replace into"):
        s = "insert into" + s[len("insert or replace into"):]
        m = re.match(r"insert into\s+(\w+)\s*\(([^)]*)\)", s, re.I)
        table, cols = m.group(1), [c.strip() for c in m.group(2).split(",")]
        pk = PK[table]
        tail = f" on conflict ({','.join(pk)}) do update set " + ", ".join(f"{c}=excluded.{c}" for c in cols if c not in pk)
    elif low.startswith("insert or ignore into"):
        s = "insert into" + s[len("insert or ignore into"):]
        tail = " on conflict do nothing"
    s = s.replace("%", "%%").replace("?", "%s")
    return s + tail


def _pg_ddl():
    ddl = re.sub(r"\binteger primary key\b", "bigserial primary key", SCHEMA)
    ddl = re.sub(r"\breal\b", "double precision", ddl)
    return [x.strip() for x in ddl.split(";") if x.strip()]


def pg():
    """The shared Postgres connection (created on first use, schema ensured once per process)."""
    import psycopg
    from psycopg.rows import dict_row
    if _pg["c"] is None or _pg["c"].closed:
        _pg["c"] = psycopg.connect(DSN, autocommit=True, row_factory=dict_row, connect_timeout=15)
        if not _ready["pg"]:
            _pg["c"].execute("; ".join(_pg_ddl()))  # one round trip, not one per table
            _ready["pg"] = True
    return _pg["c"]


def pg_run(fn):
    """Run fn(connection) with one reconnect, because serverless instances outlive Neon's idle connections."""
    for attempt in (0, 1):
        try:
            return fn(pg())
        except Exception as ex:
            name = type(ex).__name__
            if attempt == 0 and ("Operational" in name or "Interface" in name or "closed" in str(ex).lower()):
                try:
                    _pg["c"].close()
                except Exception:
                    pass
                _pg["c"] = None
                continue
            raise


def _plain(row):
    return {k: (float(v) if isinstance(v, Decimal) else v) for k, v in row.items()}


# ------------------------------------------------------------------ public API

def q(sql, args=()):
    with _lock:
        if USE_PG:
            return pg_run(lambda c: [_plain(r) for r in c.execute(_pg_sql(sql), args).fetchall()])
        c = conn()
        try:
            return [dict(r) for r in c.execute(sql, args).fetchall()]
        finally:
            c.close()


def x(sql, args=()):
    """Execute a write. Returns the new row id for tables with one."""
    with _lock:
        if USE_PG:
            s = _pg_sql(sql)
            m = re.match(r"insert into\s+(\w+)", s, re.I)
            want_id = bool(m) and m.group(1).lower() in ID_TABLES and "on conflict" not in s.lower()
            if want_id:
                s += " returning id"

            def run(c):
                cur = c.execute(s, args)
                if want_id:
                    r = cur.fetchone()
                    return r["id"] if r else None
                return None
            return pg_run(run)
        c = conn()
        try:
            cur = c.execute(sql, args)
            c.commit()
            return cur.lastrowid
        finally:
            c.close()


def xmany(sql, rows):
    rows = list(rows)
    if not rows:
        return
    with _lock:
        if USE_PG:
            s = _pg_sql(sql)
            pg_run(lambda c: c.cursor().executemany(s, rows))
            return
        c = conn()
        try:
            c.executemany(sql, rows)
            c.commit()
        finally:
            c.close()


def log_event(slug, kind, detail="", actor="studio"):
    x("insert into events(ts,slug,kind,actor,detail) values(?,?,?,?,?)", (now(), slug, kind, actor, detail if isinstance(detail, str) else json.dumps(detail)))


def events(slug=None, limit=40):
    if slug:
        return q("select * from events where slug=? order by id desc limit ?", (slug, limit))
    return q("select * from events order by id desc limit ?", (limit,))


def first_event(slug, kind):
    r = q("select ts from events where slug=? and kind=? order by id asc limit 1", (slug, kind))
    return r[0]["ts"] if r else None


def has_event(slug, kind):
    return bool(q("select 1 from events where slug=? and kind=? limit 1", (slug, kind)))
