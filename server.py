"""Local staging server: dashboard, studio (prompt box + before/after), live preview of generated pages.
Run:  python server.py   then open http://localhost:8000
"""
import base64
import html
import json
import mimetypes
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import api
import auth
import core
import integrations
import persist
import publish
import ui2
import ui_board
import ui_buyers
import ui_publishers
import ui_report
import ui_pages
import ui_review
import ui_history
import video
from ui import dashboard, studio
from ui_auth import login_page

e = html.escape
def before_page(slug):
    saved = core.BEFORE / f"{slug}.html"
    if saved.exists():
        return saved.read_bytes(), "text/html; charset=utf-8"
    shot = core.BEFORE / f"{slug}-desktop.png"
    if shot.exists():
        return (f"<!doctype html><meta charset='utf-8'><body style='margin:0;background:#fff'>"
                f"<img src='/before-img/{slug}-desktop.png' style='display:block;width:100%'></body>").encode(), "text/html; charset=utf-8"
    b = core.get_brand(slug)
    url = b["current_url"]
    msg = (f"<p>No saved copy of the current page yet.</p><p>{'<a target=_blank href=' + chr(34) + e(url) + chr(34) + '>Open the current page</a>' if url else 'Set current_url in the Sheet, or save the current page HTML to studio/before/' + e(slug) + '.html.'}</p>")
    return f"<body style='font:16px system-ui;padding:40px;color:#333'>{msg}</body>".encode(), "text/html; charset=utf-8"


def safe_file(base: Path, rel: str):
    p = (base / rel).resolve()
    return p if base.resolve() in p.parents and p.is_file() else None


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, data, ctype="text/html; charset=utf-8", headers=None):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_file(self, f):
        """Serve a file with Range support so video can play, seek and loop."""
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        data = f.read_bytes()
        total = len(data)
        rng = self.headers.get("Range")
        start, end, code = 0, total - 1, 200
        if rng and rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            start = int(a) if a else max(0, total - int(b))
            end = int(b) if (a and b) else total - 1
            end = min(end, total - 1)
            code = 206
        chunk = data[start:end + 1]
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(len(chunk)))
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def json(self, obj, code=200, headers=None):
        self.send(code, json.dumps(obj), "application/json", headers)

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def token(self):
        for part in self.headers.get("Cookie", "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "bs_session":
                return v
        return ""

    def gate(self, path, parts):
        """Sign-in check. Public: the login page and the published /live/ pages with their assets (not the downloaded media library).
        Returns True when it already answered the request."""
        if not auth.enabled():
            auth.local.email = None
            return False
        auth.local.email = auth.session(self.token())
        if path in ("/login", "/favicon.ico", "/api/login", "/api/cron/refresh"):
            return False
        if parts and parts[0] == "live":
            return False
        if parts and parts[0] == "onboard" and len(parts) in (2, 3):
            return False
        if len(parts) >= 3 and parts[0] == "assets" and parts[2] != "media":
            return False
        if auth.local.email:
            return False
        if parts and parts[0] == "api":
            self.json({"ok": False, "error": "Sign in required."}, 401)
        else:
            self.redirect("/login?next=" + quote(self.path, safe=""))
        return True

    @staticmethod
    def safe_next(n):
        n = n or "/"
        return n if n.startswith("/") and not n.startswith("//") and not n.startswith("/login") else "/"

    def client_ip(self):
        fwd = self.headers.get("X-Forwarded-For", "")
        if fwd:
            return fwd.split(",")[0].strip()
        try:
            return self.client_address[0]
        except Exception:
            return ""

    def do_GET(self):
        persist.pull()
        try:
            self._get()
        finally:
            persist.push()

    def do_POST(self):
        persist.pull()
        try:
            self._post()
        finally:
            persist.push()

    def _get(self):
        path = unquote(urlparse(self.path).path)
        parts = [p for p in path.split("/") if p]
        try:
            if self.gate(path, parts):
                return
            if path == "/login":
                if auth.local.email:
                    return self.redirect(self.safe_next(parse_qs(urlparse(self.path).query).get("next", ["/"])[0]))
                note = "" if auth.configured() else "No users are set up yet. Run: python auth.py set your@email"
                return self.send(200, login_page(self.safe_next(parse_qs(urlparse(self.path).query).get("next", ["/"])[0]), note))
            if path == "/api/cron/refresh":
                secret = os.environ.get("CRON_SECRET", "")
                if not (secret and self.headers.get("Authorization", "") == "Bearer " + secret) and not auth.local.email:
                    return self.json({"ok": False, "error": "Not allowed."}, 401)
                t0 = time.time()
                res = integrations.refresh(None, rebuild=True)
                try:
                    import lot
                    lot.build(save=True)  # the daily snapshot the lot report compares against
                except Exception:
                    pass
                return self.json({"ok": True, "brands": len(res), "seconds": round(time.time() - t0, 1)})
            if path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            if not parts:
                return self.send(200, dashboard())
            query = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
            if parts == ["launch"]:
                return self.send(200, ui2.launch_page())
            if parts == ["board"]:
                return self.send(200, ui_board.board_page())
            if parts == ["pages"]:
                return self.send(200, ui_pages.pages_page())
            if parts == ["ops"]:
                return self.send(200, ui2.ops_page(int(query.get("days", 14))))
            if parts == ["history"]:
                return self.send(200, ui_history.history_page())
            if parts == ["api", "history.csv"]:
                import history
                stamp = time.strftime("%Y-%m-%d")
                return self.send(200, history.to_csv(query), "text/csv; charset=utf-8",
                                 {"Content-Disposition": f'attachment; filename="studio-history-{stamp}.csv"'})
            if parts == ["review"]:
                return self.send(200, ui_review.list_page())
            if parts[0] == "review" and len(parts) == 2:
                return self.send(200, ui_review.review_page(parts[1]))
            if parts == ["crm"]:
                return self.send(200, ui2.crm_page())
            if parts == ["golive"]:
                import ui_golive
                return self.send(200, ui_golive.golive_page())
            if parts == ["report"]:
                return self.send(200, ui_report.report_page())
            if parts == ["api", "report.txt"]:
                import lot
                return self.send(200, lot.as_text(lot.build(save=True)), "text/plain; charset=utf-8")
            if parts == ["publishers"]:
                return self.send(200, ui_publishers.publishers_page())
            if parts == ["buyers"]:
                host = self.headers.get("Host", "")
                scheme = "http" if host.startswith(("localhost", "127.0.0.1")) else "https"
                return self.send(200, ui_buyers.buyers_page(f"{scheme}://{host}" if host else ""))
            if parts[0] == "onboard" and len(parts) == 2:
                page = ui_buyers.onboard_page(parts[1])
                return self.send(200, page) if page else self.send(404, "This onboarding link is not active.")
            if parts == ["integrations"]:
                return self.send(200, ui2.integrations_page())
            if parts == ["api", "video", "tracker.csv"]:
                return self.send(200, video.tracker_csv(), "text/csv; charset=utf-8")
            if parts[0] == "live" and len(parts) >= 2:
                d = publish.live_dir(parts[1]) if publish.live_status(parts[1])["live"] else None
                f = safe_file(d, "/".join(parts[2:]) or "index.html") if d else None
                if f:
                    return self.send_file(f)
                return self.send(404, "This brand is not live")
            if parts[0] == "video" and len(parts) == 4:
                f = safe_file(video.OUTDIR, f"{parts[1]}/{parts[2]}-{parts[3]}/out.mp4")
                if f:
                    return self.send_file(f)
                return self.send(404, "Not rendered yet")
            r = api.get(parts, query)
            if r:
                return self.json(r[1], r[0])
            if parts[0] == "studio" and len(parts) == 2:
                return self.send(200, studio(parts[1]))
            if parts[0] == "before" and len(parts) == 2:
                data, ct = before_page(parts[1])
                return self.send(200, data, ct)
            if parts[0] == "api" and len(parts) == 3 and parts[1] == "checklist":
                return self.json(core.checklist(parts[2]))
            if parts[0] == "api" and len(parts) == 3 and parts[1] == "variants":
                return self.json(core.load_variants(parts[2]))
            if parts[0] == "p" and len(parts) >= 2:
                rel = "/".join(parts[2:]) or "index.html"
                f = safe_file(core.OUT / parts[1], rel)
                if f:
                    return self.send_file(f)
                if len(parts) == 2 or parts[2] == "index.html":
                    return self.send(200, "<!doctype html><meta charset='utf-8'><body style=\"margin:0;min-height:100vh;display:grid;place-items:center;font:15px Inter,system-ui,sans-serif;color:#667085;background:#f6f4ef;text-align:center\"><div><div style=\"font:600 22px Poppins,Inter,sans-serif;color:#14171c;margin-bottom:8px\">Nothing generated yet</div>Write a prompt and hit Generate to build this page.</div></body>")
                return self.send(404, "Not found")
            if parts[0] == "before-concept" and len(parts) == 2:
                return self.send(200, (f"<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
                                       f"<body style='margin:0;background:#fff'><img src='/before-img/{parts[1]}-concept.png' style='display:block;width:100%'></body>"))
            if parts[0] == "before-mobile" and len(parts) == 2:
                return self.send(200, (f"<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
                                       f"<body style='margin:0;background:#fff'><img src='/before-img/{parts[1]}-mobile.png' style='display:block;width:100%'></body>"))
            if parts[0] == "before-img" and len(parts) == 2:
                f = safe_file(core.BEFORE, parts[1])
                if f:
                    return self.send_file(f)
            if parts[0] == "site" and len(parts) >= 2:
                f = safe_file(core.ROOT / "sites" / parts[1], "/".join(parts[2:]) or "index.html")
                if f:
                    return self.send_file(f)
                return self.send(404, "No mockup site for this brand")
            if parts[0] == "assets" and len(parts) >= 3:
                f = safe_file(core.ASSETS / parts[1], "/".join(parts[2:]))
                if f:
                    return self.send_file(f)
            self.send(404, "Not found")
        except KeyError:
            self.send(404, "Unknown brand")

    def _post(self):
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        path = urlparse(self.path).path
        try:
            if path == "/api/login":
                ok, err = auth.login(data.get("email", ""), data.get("password", ""), self.client_ip(), bool(data.get("remember")))
                if err == "locked":
                    return self.json({"ok": False, "error": "Too many attempts. Try again in a minute."}, 429)
                if err:
                    return self.json({"ok": False, "error": "That email and password do not match."}, 401)
                cookie = f"bs_session={ok}; Path=/; HttpOnly; SameSite=Lax; Max-Age={auth.max_age(bool(data.get('remember')))}"
                return self.json({"ok": True, "next": self.safe_next(data.get("next"))}, 200, {"Set-Cookie": cookie})
            pp = [p for p in path.split("/") if p]
            if len(pp) == 3 and pp[0] == "onboard" and pp[2] == "tech":
                import buyers
                try:
                    buyers.submit_tech(pp[1], data if isinstance(data, dict) else {})
                    return self.json({"ok": True})
                except ValueError as ex:
                    return self.json({"ok": False, "error": str(ex)}, 400)
            if self.gate(path, pp):
                return
            if path == "/api/logout":
                auth.logout(self.token())
                return self.json({"ok": True}, 200, {"Set-Cookie": "bs_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"})
            if path == "/api/generate":
                return self.json(core.build_page(core.get_brand(data["slug"]), data.get("prompt", "")))
            if path == "/api/reference":
                raw = base64.b64decode(data["data"].split(",", 1)[-1])
                core.save_reference(data["slug"], raw)
                return self.json({"ok": True})
            if path == "/api/extract":
                try:
                    p = core.extract_pitch(data["slug"], "exact" if data.get("mode") == "exact" else "inspire")
                    return self.json({"ok": True, "hero": p.get("hero", ""), "provider": core.ai_provider()})
                except Exception as ex:
                    return self.json({"ok": False, "error": str(ex)}, 400)
            if path == "/api/buyer":
                core.set_brand_field(data["slug"], "buyer", data.get("buyer", "").strip())
                return self.json({"ok": True})
            r = api.post(path, data)
            if r:
                return self.json(r[1], r[0])
        except KeyError:
            return self.json({"error": "unknown brand"}, 404)
        self.send(404, "Not found")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Studio on http://localhost:{port}  (config: {core.config_source()})")
    if auth.enabled() and not auth.configured():
        print("No sign-in users yet. Run: python auth.py set your@email")
    integrations.start_background(int(os.environ.get("REFRESH_SECONDS", "900")))
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
