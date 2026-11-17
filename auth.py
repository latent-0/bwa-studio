"""Sign-in for the studio. Passwords are never stored: only a salted PBKDF2 hash per user, in data/auth.json or in the BS_USERS environment
variable (a JSON object of email -> {salt, hash, iterations}), which is how a Vercel deployment gets its users.
Sessions are signed tokens, so they survive restarts and work across serverless instances. Lockouts live in the database.
Set or change a password locally:   python auth.py set someone@example.com        (prompts)   or   --password VALUE
Print the BS_USERS value for Vercel: python auth.py export
Turn sign-in off for local scripts (recorders, tests):   BS_AUTH=off python server.py"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import time

import paths
import store

FILE = paths.ROOT / "data" / "auth.json"
SECRET_FILE = paths.ROOT / "data" / ".auth_secret"
ITERATIONS = 240_000
SESSION_SECONDS = 12 * 3600
REMEMBER_SECONDS = 30 * 86400
MAX_FAILS, WINDOW, LOCK = 5, 300, 60

import threading  # noqa: E402

local = threading.local()


def enabled():
    return os.environ.get("BS_AUTH", "on").strip().lower() != "off"


def _load():
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
    except Exception:
        d = {"users": {}}
    d.setdefault("users", {})
    try:
        d["users"].update({k.lower(): v for k, v in json.loads(os.environ.get("BS_USERS", "{}")).items()})
    except Exception:
        pass
    return d


def _hash(password, salt, iterations=ITERATIONS):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations).hex()


def user_record(password):
    salt = secrets.token_bytes(16)
    return {"salt": salt.hex(), "hash": _hash(password, salt), "iterations": ITERATIONS, "updated": time.strftime("%Y-%m-%d %H:%M:%S")}


def set_password(email, password):
    email = email.strip().lower()
    if len(password) < 6:
        raise ValueError("Use at least 6 characters.")
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
    except Exception:
        d = {"users": {}}
    d.setdefault("users", {})[email] = user_record(password)
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")


def users():
    return sorted(_load()["users"])


def configured():
    return bool(users())


def verify(email, password):
    u = _load()["users"].get((email or "").strip().lower())
    salt = bytes.fromhex(u["salt"]) if u else b"\x00" * 16  # hash anyway when the user is unknown so timing does not reveal accounts
    got = _hash(password or "", salt, (u or {}).get("iterations", ITERATIONS))
    return bool(u) and hmac.compare_digest(got, u["hash"])


# ------------------------------------------------------------------ signed sessions

def _secret():
    s = os.environ.get("AUTH_SECRET", "")
    if s:
        return s.encode()
    try:
        return SECRET_FILE.read_text(encoding="utf-8").strip().encode()
    except Exception:
        SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
        s = secrets.token_hex(32)
        SECRET_FILE.write_text(s, encoding="utf-8")
        return s.encode()


def _b64(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _sign(payload):
    return _b64(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())


def make_token(email, remember=False):
    payload = _b64(json.dumps({"e": email, "x": int(time.time()) + (REMEMBER_SECONDS if remember else SESSION_SECONDS)}).encode())
    return payload + "." + _sign(payload)


def session(token):
    """Returns the signed-in email, or None. The user must still exist, so removing a user ends their sessions."""
    if not token or "." not in token:
        return None
    payload, _, sig = token.partition(".")
    if not hmac.compare_digest(sig, _sign(payload)):
        return None
    try:
        d = json.loads(_unb64(payload))
    except Exception:
        return None
    if d.get("x", 0) < time.time() or d.get("e", "") not in _load()["users"]:
        return None
    return d["e"]


def logout(token):
    """Sessions are stateless: signing out clears the cookie. Changing AUTH_SECRET ends every session at once."""
    return None


# ------------------------------------------------------------------ lockout

def _locked(key):
    now = time.time()
    rows = store.q("select ts from auth_fails where k=? and ts>? order by ts", (key, now - WINDOW))
    return len(rows) >= MAX_FAILS and now - rows[-1]["ts"] < LOCK


def login(email, password, ip="", remember=False):
    """Returns (token, error). error is 'locked' or 'bad'."""
    key = f"{ip}|{(email or '').strip().lower()}"
    if _locked(key):
        return None, "locked"
    if verify(email, password):
        store.x("delete from auth_fails where k=?", (key,))
        return make_token(email.strip().lower(), remember), None
    store.x("insert into auth_fails(k, ts) values(?, ?)", (key, time.time()))
    store.x("delete from auth_fails where ts<?", (time.time() - 3600,))
    time.sleep(0.4)
    return None, "bad"


def max_age(remember):
    return REMEMBER_SECONDS if remember else SESSION_SECONDS


def who():
    return getattr(local, "email", None)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["list"]:
        print("\n".join(users()) or "no users")
    elif args[:1] == ["export"]:
        print(json.dumps(_load()["users"]))
    elif args[:1] == ["set"] and len(args) >= 2:
        pw = args[args.index("--password") + 1] if "--password" in args else None
        if pw is None:
            import getpass
            pw = getpass.getpass("New password: ")
        set_password(args[1], pw)
        print("Saved", args[1].lower())
    else:
        print(__doc__)
