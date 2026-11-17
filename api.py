"""JSON API for the studio UI. get(parts, query) and post(path, data) return (status, payload) or None if the route is unknown."""
import auth
import board
import compliance
import core
import lp
import integrations
import media
import paths
import publish
import sheet
import store
import video

EDITABLE = {"hero_video", "ringba_campaign", "everflow_offer", "leadprosper_campaign", "leadprosper_supplier", "delivery", "phone", "hours", "buyer", "legal_entity", "contact_email", "cta"}
SYSTEMS = ("ringba", "everflow", "leadprosper")


def _catalog_names(system):
    return {c["id"]: c["name"] for c in {"ringba": integrations.ringba_campaigns, "everflow": integrations.everflow_offers, "leadprosper": integrations.lp_campaigns}[system]()}


def _mapped(b):
    """What the brand is mapped to in each system, as [{id, name}]."""
    out = {}
    resolvers = {"ringba": integrations.ringba_campaign_id, "everflow": integrations.everflow_offer_id, "leadprosper": integrations.lp_campaign_id}
    for system in SYSTEMS:
        names = _catalog_names(system)
        out[system] = [{"id": i, "name": names.get(i, i)} for i in integrations.ids(b[integrations.FIELD_FOR[system]], resolvers[system])]
    return out


def _status(slug):
    cl = core.checklist(slug)
    b = core.get_brand(slug)
    comp = compliance.status(slug)
    ls = publish.live_status(slug)
    pend = store.q("select count(*) n from calls where slug=? and ghl_synced=0 and is_test=0", (slug,))[0]["n"]
    calls = store.q("select count(*) n from calls where slug=? and is_test=0", (slug,))[0]["n"]
    leads = store.q("select coalesce(sum(leads),0) n, coalesce(sum(accepted),0) a, coalesce(sum(revenue),0) r from leads_daily where slug=?", (slug,))[0]
    clicks = store.q("select coalesce(sum(clicks),0) n from traffic_daily where slug=?", (slug,))[0]["n"]
    sb = core.sheet_info(slug) or {}
    return {"slug": slug, "serverless": paths.SERVERLESS, "checklist": cl, "live": ls, "stage": integrations.desired_stage(slug), "calls": calls, "calls_pending_sync": pend,
            "leads": {"total": leads["n"], "accepted": leads["a"], "revenue": round(leads["r"], 2)}, "clicks": clicks,
            "compliance": {k: comp[k] for k in ("state", "label", "open", "approved", "reviewed")},
            "modes": {n: integrations.mode(n) for n in ("ringba", "everflow", "leadprosper", "ghl")},
            "delivery": cl["delivery"],
            "brand": {k: b[k] for k in ("phone", "ringba_campaign", "everflow_offer", "leadprosper_campaign", "leadprosper_supplier", "buyer", "delivery")},
            "mapped": _mapped(b),
            "placeholder_phone": core.is_placeholder_phone(b["phone"]),
            "sheet": {k: sb.get(k, "") for k in ("priority", "url", "buyers", "buyer_confirmed", "category", "type", "note", "site_up", "ghl_subaccount", "ghl_website", "vertical_text")} | {"campaigns": sb.get("campaigns", []), "sources": sb.get("sources", []), "videos": sheet.videos(b["name"])},
            "snippets": {n: (core.DATA / "snippets" / slug / f"{n}_snippet.html").exists() for n in ("ringba", "everflow")}}


def get(parts, query=None):
    if parts[:2] == ["api", "status"] and len(parts) == 3:
        return 200, _status(parts[2])
    if parts[:2] == ["api", "compliance"] and len(parts) == 3:
        return 200, compliance.status(parts[2])
    if parts[:3] == ["api", "video", "jobs"] and len(parts) == 4:
        return 200, {"jobs": video.jobs(parts[3]), "variants": core.load_variants(parts[3])}
    if parts[:2] == ["api", "events"] and len(parts) == 3:
        return 200, store.events(parts[2], 60)
    if parts == ["api", "ops"]:
        return 200, integrations.ops(int((query or {}).get("days", 14)))
    if parts == ["api", "crm"]:
        return 200, {"board": integrations.board(), "mode": integrations.mode("ghl")}
    if parts == ["api", "integrations"]:
        return 200, {"status": integrations.status(), "postback": integrations.postback_template(), "pipelines": integrations.PIPELINES}
    if parts[:2] == ["api", "mapping"] and len(parts) == 3:
        b = core.get_brand(parts[2])
        return 200, {"mapped": _mapped(b), "suggestions": integrations.suggest(parts[2], top=8), "catalog": {k: len(v) for k, v in integrations.catalog().items()},
                     "delivery": core.delivery_modes(b)}
    if parts[:2] == ["api", "catalog"] and len(parts) == 3 and parts[2] in SYSTEMS:
        return 200, {"items": {"ringba": integrations.ringba_campaigns, "everflow": integrations.everflow_offers, "leadprosper": integrations.lp_campaigns}[parts[2]]()}
    if parts == ["api", "sheet"]:
        return 200, {"status": sheet.status(), "url": sheet.sheet_url(), "tabs": list(sheet.TABS.values()), "brands": len(sheet.roster())}
    if parts == ["api", "board"]:
        return 200, board.payload(fresh=(query or {}).get("fresh") == "1")
    if parts == ["api", "board", "history"]:
        q = query or {}
        return 200, {"ok": True, "entries": board.history(q.get("slug") or None, min(int(q.get("limit", 80)), 300)), "now": store.now()}
    if parts == ["api", "lp"]:
        q = query or {}
        src = q.get("src", lp.DEFAULT)
        if src not in lp.SOURCES:
            return 404, {"ok": False, "error": "Unknown tracker."}
        return 200, lp.payload(src, fresh=q.get("fresh") == "1")
    if parts == ["api", "refresh"]:
        return 200, {**integrations.refresh_state(), "serverless": paths.SERVERLESS}
    if parts == ["api", "refresh", "brands"]:
        return 200, [b["slug"] for b in core.load_brands() if (b["ringba_campaign"] or b["everflow_offer"] or b["leadprosper_campaign"])]
    if parts[:2] == ["api", "media"] and len(parts) == 3:
        return 200, {**media.for_brand(parts[2]), "library": media.library(parts[2]), "hero_video": core.get_brand(parts[2])["hero_video"], "serverless": paths.SERVERLESS}
    if parts[:3] == ["api", "media", "progress"] and len(parts) == 5:
        return 200, media.progress(parts[3], parts[4])
    if parts == ["api", "review"]:
        return 200, review_list()
    if parts == ["api", "history"]:
        import history
        return 200, history.query(query or {}, limit=min(int((query or {}).get("limit", 80)), 300))
    if parts == ["api", "history", "facets"]:
        import history
        return 200, history.facets()
    if parts[:2] == ["api", "review"] and len(parts) == 3:
        return 200, review_payload(parts[2], (query or {}).get("page", "index"))
    return None


def review_list():
    import wording
    out = []
    for b in core.load_brands():
        st = compliance.status(b["slug"])
        d = wording.load(b["slug"])
        out.append({"slug": b["slug"], "name": b["name"], "vertical": b["vertical"], "color": b["accent_color"] or b["primary_color"] or "#6b8cff",
                    "state": st["state"], "label": st["label"], "open": st["open"], "flags": len(st["hits"]), "edits": wording.total_edits(d),
                    "reviewed": st["reviewed"]})
    return out


def review_payload(slug, page="index"):
    import wording
    b = core.get_brand(slug)
    blks, unmatched = wording.blocks(slug, page)
    loose = wording.flags_by_block(slug, blks) if (blks and page == "index") else []
    rec = wording.load(slug)
    pages = [{"key": k, "title": t, "file": f, "exists": (core.OUT / slug / f).exists(), "edits": len(wording.edits_for(rec, k))} for k, t, f in wording.pages()]
    return {"slug": slug, "name": b["name"], "page": page, "pages": pages, "status": compliance.status(slug), "blocks": blks, "unmatched": unmatched, "loose_flags": loose,
            "live": publish.live_status(slug)["live"], "who": auth.who() or ""}


def post(path, d):
    s = d.get("slug")
    try:
        if path == "/api/legal/clear":
            compliance.clear(s, d["id"], auth.who() or d.get("by") or "counsel", d.get("on", True))
            return 200, compliance.status(s)
        if path == "/api/legal/clear-all":
            compliance.clear_all(s, auth.who() or d.get("by") or "counsel")
            return 200, compliance.status(s)
        if path == "/api/legal/review":
            st = compliance.review(s, auth.who() or d.get("reviewer", ""), d.get("note", ""))
            integrations.refresh_stage(s)
            return 200, st
        if path == "/api/review/save":
            import wording
            by = auth.who() or (d.get("by") or "").strip()
            if not by:
                raise ValueError("Enter your name so the review is recorded against you.")
            page = d.get("page") or "index"
            was = compliance.status(s)["state"]
            n = wording.save(s, d.get("edits") or [], by, page)
            present = {h["id"] for h in compliance.scan(s)}
            for hid in d.get("clear") or []:
                if hid in present:
                    compliance.clear(s, hid, by, True)
            msg = f"Saved {n} wording change{'s' if n != 1 else ''}." if n else "No wording changes."
            if was == "approved" and compliance.status(s)["state"] == "stale":
                store.log_event(s, "legal.signoff_stale", {"reason": "Wording edited after sign-off"}, by)
                msg += " The earlier sign-off now needs renewing."
            if d.get("approve"):
                try:
                    compliance.review(s, by, d.get("note", ""))
                    msg += " Signed off."
                except ValueError as ex:
                    integrations.refresh_stage(s)
                    return 400, {**review_payload(s, page), "ok": False, "error": msg + " Not signed off yet: " + str(ex)}
            integrations.refresh_stage(s)
            return 200, {**review_payload(s, page), "ok": True, "message": msg, "changed": n}
        if path == "/api/review/forget":
            import wording
            page = d.get("page") or "index"
            was = compliance.status(s)["state"]
            wording.forget(s, d.get("original", ""), auth.who() or d.get("by") or "reviewer", page)
            if was == "approved" and compliance.status(s)["state"] == "stale":
                store.log_event(s, "legal.signoff_stale", {"reason": "A wording edit was removed after sign-off"})
            return 200, review_payload(s, page)
        if path == "/api/legal/revoke":
            compliance.revoke(s)
            integrations.refresh_stage(s)
            return 200, compliance.status(s)
        if path == "/api/ringba/number":
            num = integrations.assign_number(s)
            integrations.refresh_stage(s)
            return 200, {"ok": True, "number": num, "note": "Regenerate the page so it shows the number."}
        if path == "/api/ringba/test-call":
            r = integrations.place_test_call(s)
            integrations.refresh_stage(s)
            return 200, r
        if path == "/api/leadprosper/test-lead":
            r = integrations.place_test_lead(s)
            integrations.refresh_stage(s)
            return 200, {**r, "ok": bool(r.get("ok")), "error": None if r.get("ok") else r.get("detail")}
        if path == "/api/everflow/check":
            r = integrations.pull_everflow(s)
            integrations.refresh_stage(s)
            ok = core.checklist(s)["items"][6]["ok"]
            return 200, {"ok": ok, "pull": r, "error": None if ok else "No clicks have reached Everflow for this brand's offers yet."}
        if path == "/api/ringba/pull":
            return 200, {"ok": True, "result": integrations.refresh(s)}
        if path == "/api/refresh":
            if paths.SERVERLESS:  # no background threads on a serverless host: do the work inside this request
                return 200, {"ok": True, "result": integrations.refresh(s or None, rebuild=not s)}
            return 200, {"ok": True, "started": integrations.refresh_async()}
        if path == "/api/sandbox/traffic":
            return 200, integrations.simulate_traffic(s, int(d.get("days", 14)))
        if path == "/api/ghl/sync":
            return 200, integrations.sync_calls(s)
        if path == "/api/ghl/stage":
            return 200, integrations.refresh_stage(s)
        if path == "/api/mapping/set":
            system = d["system"]
            if system not in SYSTEMS:
                raise ValueError("Unknown system.")
            core.set_brand_field(s, integrations.FIELD_FOR[system], ",".join(str(i) for i in d.get("ids", [])))
            integrations.clear_catalogs()
            integrations.refresh_stage(s)
            return 200, {"ok": True, "mapped": _mapped(core.get_brand(s))}
        if path == "/api/mapping/automap":
            res = integrations.automap(s if s else None)
            return 200, {"ok": True, "result": [r for r in res if r["mapped"]]}
        if path == "/api/media/check":
            from concurrent.futures import ThreadPoolExecutor
            ids = [i for i in (d.get("drive_ids") or [])][:30]
            with ThreadPoolExecutor(6) as ex:
                res = list(ex.map(media.check, ids))
            return 200, {"ok": True, "results": dict(zip(ids, res))}
        if path == "/api/media/download":
            if paths.SERVERLESS:
                raise ValueError("Downloads are disabled on this deployment. Use the Open link to get the file from Google Drive.")
            asset = next((x for g in media.for_brand(s)["groups"] for x in g["items"] if x["id"] == d.get("id")), None)
            if not asset or asset["type"] != "file":
                raise ValueError("That asset is not a downloadable file.")
            return 200, {"ok": True, **media.download(s, asset)}
        if path == "/api/media/use":
            f = media.library(s)
            hit = next((x for x in f if x["file"] == d.get("file")), None)
            if not hit or not hit["file"].lower().endswith((".mp4", ".mov", ".webm")):
                raise ValueError("Pick a downloaded video.")
            import shutil  # copy next to the page assets: the live page is public, the media library is not
            dest = core.ASSETS / s / ("brand-" + hit["file"])
            if not dest.exists():
                shutil.copyfile(core.ASSETS / s / "media" / hit["file"], dest)
            core.set_brand_field(s, "hero_video", dest.name)
            store.log_event(s, "media.used", f"{hit['title']} set as the brand video")
            return 200, {"ok": True, "note": "Regenerate the page to show it. Video renders use it as the background right away."}
        if path == "/api/board/priority":
            try:
                res = board.save(list(d.get("order") or []), core.load_brands(), auth.who() or "studio", d.get("move"))
            except ValueError as ex:
                return 400, {"ok": False, "error": str(ex)}
            return 200, {"ok": True, **res}
        if path == "/api/lp/update":
            try:
                row = lp.update(d.get("src", lp.DEFAULT), d.get("rid", ""), d.get("set") or {}, auth.who() or "studio")
            except (ValueError, RuntimeError) as ex:
                return 400, {"ok": False, "error": str(ex)}
            return 200, {"ok": True, "row": row}
        if path == "/api/sheet/refresh":
            sheet.roster(fresh=True)
            media.catalog(fresh=True)
            return 200, {"ok": True, "status": sheet.status(), "brands": len(sheet.roster())}
        if path == "/api/publish":
            r = publish.publish(s, d.get("note", ""), d.get("actor", "studio"))
            return 200, r
        if path == "/api/pause":
            publish.pause(s)
            return 200, {"ok": True}
        if path == "/api/resume":
            publish.resume(s)
            return 200, {"ok": True}
        if path == "/api/rollback":
            return 200, {"ok": True, "release": publish.rollback(s)}
        if path == "/api/video/render":
            ids = d.get("variants") or []
            fmt = d.get("fmt", "9x16")
            if paths.SERVERLESS:
                raise ValueError("Video rendering needs ffmpeg, which Vercel does not provide. Render videos from the local studio.")
            if fmt not in video.FORMATS:
                raise ValueError("Unknown format.")
            video.render_async(s, ids, fmt)
            return 200, {"ok": True, "queued": len(ids)}
        if path == "/api/brand/fields":
            for k, v in (d.get("fields") or {}).items():
                if k in EDITABLE:
                    core.set_brand_field(s, k, str(v).strip())
            integrations.refresh_stage(s)
            return 200, {"ok": True}
        if path == "/api/integrations/save":
            integrations.save_cfg({k: v for k, v in d.items() if k in ("ringba", "everflow", "leadprosper", "ghl", "gemini", "force_sandbox")})
            integrations.clear_catalogs()
            return 200, integrations.status()
        if path == "/api/integrations/test":
            fn = {"ringba": integrations.ringba_test, "everflow": integrations.everflow_test, "leadprosper": integrations.lp_test, "ghl": integrations.ghl_test, "gemini": integrations.gemini_test}[d["name"]]
            return 200, fn()
        if path == "/api/bulk/generate":
            done = []
            for b in core.load_brands():
                if d.get("missing_only") and (core.OUT / b["slug"] / "index.html").exists():
                    continue
                core.build_page(b, "")
                done.append(b["slug"])
            return 200, {"ok": True, "generated": done}
    except (ValueError, KeyError) as ex:
        return 400, {"ok": False, "error": str(ex).strip("'") or "Bad request"}
    except Exception as ex:
        return 500, {"ok": False, "error": str(ex)[:300]}
    return None
