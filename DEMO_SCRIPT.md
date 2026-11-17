# POC demo script (about 10 minutes): Patriot Insurance, end to end

## Before the call
- `cd studio && python server.py` then open http://localhost:8000/studio/patriot-insurance
- Public preview URL for Jeff's browser (free): `cloudflared tunnel --url http://localhost:8000` and share the printed link. Or just screen share.
- Save a copy of the current Patriot page to `studio/before/patriot-insurance.html` (or set `current_url` in the Sheet) so "Before" works.
- Drop real credibility shots into `studio/assets/patriot-insurance/hero.jpg`.
- Optional live copy from Claude: set `ANTHROPIC_API_KEY` (and `RATE_IN_PER_M` / `RATE_OUT_PER_M` to get a cost per page).
- Control panel as a real Sheet: File > Share > Publish to web > CSV, then set `SHEET_CSV_URL` to that link. Columns match `brands.csv`.
- When Jeff's access arrives: paste the Ringba number tag into `data/ringba_snippet.html` and the Everflow tag into `data/everflow_snippet.html`, then regenerate. If it has not arrived, say the demo uses the Sheet number and sandbox data.
- Run a rehearsal, then record a backup of it.

## On the call
1. **Start red (1 min).** Show the dashboard: the go-live dots for Patriot are red. "This is today: no page, no compliance pages, no buyer."
2. **Control panel (1 min).** Show the Sheet row: name, vertical, offer, audience, phone, tone, colors, buyer, CTA. "One row is one brand."
3. **Prompt to page (2 min).** Type the prompt, hit Generate. New page appears in seconds with the locked skeleton: hero, trust bar, benefits, call or form, FAQ, footer.
4. **Before and after (1 min).** Switch to side by side. Point at the real-photo slot in place of AI faces. Then scroll the new page: sticky header that tightens, thin progress bar, the sticky "How it works" panel that steps 01 to 03, cards that reveal and lift on hover, FAQ that eases open. On a phone width, a sticky call bar appears after the hero. All motion switches off for visitors who prefer reduced motion.
5. **Tracking (1 min).** Open the preview with `?_ef_transaction_id=test123&sub1=mgid&affid=77`. In the console, `BWA_TRACKING` shows the captured values. The call number comes from the Ringba tag.
6. **Compliance (1 min).** Open Privacy, CCPA, Opt-Out, Cookies, Partners. All seven were generated from one template. Say plainly they are drafts until legal reviews them.
7. **Variants (1 min).** Show the 9 script variants (3 openers x 3 CTAs, with the Patriot brand line) built from Jeff's scripts doc. Say the next step is compiling them with clips from the credibility folder.
8. **Go green (1 min).** Assign a buyer. The checklist goes green and shows READY TO GO LIVE.
9. **Numbers (1 min).** Dashboard "Cost and speed" panel: seconds per page, tokens, estimated cost.

## Flight Finder Pro mockup (optional, 2 minutes)
- Open http://localhost:8000/site/flight-finder-pro/ (or the "Mockup site" button on the dashboard).
- Download the Drive folder and unzip it into `studio/assets/flight-finder-pro/`, keeping the original file names. The page picks up `Flight Finder Pro.mp4` (hero video) and `Flight Finder Pro Plane 2.jpg` (bento tile) automatically. Optional: save a frame of the video as `poster.jpg` in the same folder.
- Walk it: hero and video slot, "one call or 27 tabs" counter, bento grid, 5 stacked steps, "why is it free", FAQ.
- Re-record the video afterwards with `python record_demo.py` once the assets are in.

## Flight Finder Pro before and after (3 minutes)
- Before = a snapshot of Jeff's current Lovable page, saved in `studio/before/` (desktop and mobile PNGs). Re-capture it any time the live page changes.
- Open the Flight Finder Pro studio, click "Before (current)", then prompt, Generate, and use "Side by side".
- The new page keeps the live page's facts: phone, hours (Mon to Fri, 9am to 6pm EST), the partners strip and the fares disclaimer. It adds the brand clip in the hero, the "one call or 27 tabs" comparison, a bento grid and a scroll story.
- The concept image's "free service, the airlines pay us" claims are NOT in the generated copy, because the live page does not make them. Add them only after counsel clears them.
- Re-record with `python record_before_after.py` (server running, clean state).

## Generate a site from an image (the sales pitch in the picture)
- In the brand workspace, drop a landing page image into **Reference image**. The studio uploads it, reads the sales pitch off it, and generates the site: same headline, bullets, comparison, reasons to call, steps, "why is it free", FAQ and closing call, with the brand clip, phone and hours from the Sheet.
- The pitch is stored as plain text in `data/pitch/<brand>.json`. Edit any line and hit Generate to change the wording. A brand with a pitch file ignores the prompt box.
- Reading a NEW image needs an AI key. Gemini works out of the box: add the key on the Integrations page (or set `GEMINI_API_KEY`). Without Gemini the studio uses `ANTHROPIC_API_KEY`, then the Claude CLI if it is signed in (`claude login`). Gemini model names change, so the studio uses the `gemini-flash-latest` alias and falls back through a short list.
- **Use the image as:** the default is Inspiration. The studio studies the image's angle, section order and what it emphasizes, then writes new direct-response sales copy for the brand (not the image's brand, prices or claims). A safety pass removes fee, free and guarantee claims and invented statistics the brand never supplied; counsel still reviews everything. Choose Exact wording only when the image is this brand's own page.
- If the image cannot be read, the upload still works and the site is still generated: from the prompt (or the brand's existing pitch), with the read step marked failed and the reason shown. The image stays as the reference.
- The same key also writes page copy from a prompt when there is no image.
- Claims in the image (for example "free service, the airlines pay us") come through as written. Have counsel clear them before launch.

## Sign-in
The studio now asks for a login. Passwords are stored only as salted hashes in `data/auth.json`; sessions use an HttpOnly cookie, and five wrong tries lock that email and address for a minute. The published `/live/` pages and their public assets stay open for visitors. The downloaded media library and everything else need a login.
- Add or change a user: `python auth.py set someone@example.com` (it prompts for the password). `python auth.py list` shows users.
- Recorders and test scripts that drive the app without logging in: start the server with `BS_AUTH=off python server.py`.

## Launch pipeline on the real Sheet, Ringba, Everflow and LeadProsper (5 minutes)
Brands, priority, buyers and site status come straight from the Google Sheet (Priority List, URLs/Brands, Ringba and Inventory Draft tabs). It is read-only from the studio: edit the Sheet and the studio updates within two minutes. Studio-only settings (phone, colors, campaign mappings, legal flags) live in `brands.csv`.

Each system has one job:
- **Ringba**: calls. Tracking numbers, call logs, buyers and payouts.
- **Everflow**: clicks. Offers, valid clicks and conversions.
- **LeadProsper**: lead delivery. Leads posted to buyers: accepted, duplicated, failed, with revenue.
- **GoHighLevel**: the CRM. Still sandbox until a token is added.

A brand delivers by calls, clicks or leads (from the Sheet's Type column, default calls). That decides which system sets it up and which test it must pass.
1. **Launch board** (`/launch`). 17 brands in Priority List order with delivery chips and Sheet status. "Auto-map campaigns" maps each brand to Ringba campaigns, Everflow offers and LeadProsper campaigns whose names start with the brand name. It only changes `brands.csv`, never the vendor accounts.
2. **Open a brand, Integrations tab.** Shows what the Sheet says, how the brand delivers, and each system's mapped campaigns with suggestions and a search box.
3. **Go-live tab.** Seven checks: page, delivery set up, tracking, compliance pages, buyer, legal review, test delivery. For calls brands, "Use the campaign number" copies the live number from the Ringba campaign. Regenerate the page to show it.
4. **Test delivery.** Calls: call the number, then "I called it, check now". Leads: "Send test lead" posts one lead flagged as a test to LeadProsper (it asks first). Clicks: "Check Everflow clicks".
5. **Compliance tab, Publish, Video tab.** Same as before. The Video tab also lists the brand's rows from the Sheet's HSL_videos tracker.
6. **Ops** (`/ops`). Clicks, calls, converted calls, leads and revenue per brand from the real accounts, with alerts. "Refresh live data" pulls now; the server also refreshes every 15 minutes.
7. **CRM** (`/crm`). GoHighLevel pipelines (sandbox until a token is added).

Reset between demos: stop the server, delete `out/`, `published/`, `data/video/`, `data/studio.db`, `data/legal.json`, and clear buyer, legal_reviewed and phone in `brands.csv`. Keep `data/integrations.json` (credentials) and the campaign mappings.

## Say clearly
- Live copy needs an API key. Without it the demo uses the offline template.
- Ringba, Everflow and LeadProsper are live and were checked read-only against the real accounts. A real test lead has not been sent yet. GoHighLevel is sandbox until a token is added.
- A brand cannot pass the call test without a real call to its number.
- The video voice is a placeholder. Footage, a licensed voice or avatar provider, and real call data come next.
- The claims scan and sign-off are a workflow gate, not legal advice. Counsel decides what is acceptable.
- Legal pages are templates that need counsel before any brand goes live.

## Hosted on Vercel
Live at https://bwa-brand-studio.vercel.app (project `bwa-brand-studio`, Neon Postgres in us-east-1). Sign in with the studio login.
- **Redeploy** after any code change: `vercel deploy --prod` from the `studio` folder. Brand defaults in `brands.csv` are the starting point only: changes made in the hosted studio are stored in the database and win over the file.
- **Credentials and users** are Vercel environment variables (RINGBA_*, EVERFLOW_API_KEY, LEADPROSPER_API_TOKEN, GEMINI_API_KEY, BS_USERS, AUTH_SECRET, CRON_SECRET). Change them in the project settings, then redeploy. The Integrations page cannot edit them on the hosted studio.
- **Add or change a user:** run `python auth.py set email` locally, then `python auth.py export` and paste the result into BS_USERS.
- **Data refresh:** a daily job (06:00 UTC) pulls Ringba, Everflow and LeadProsper. The Ops page "Refresh live data" button does it on demand, brand by brand.
- **Not available on the hosted studio:** video rendering (needs ffmpeg) and media downloads. Use the local studio for those.
- **Local studio still works** unchanged (`python server.py`, SQLite). The two do not share data.

## Flight Finder Pro on its own domain
The generated Flight Finder Pro page is deployed as a separate static Vercel project, `flight-finder-pro` (preview: https://flight-finder-pro-eight.vercel.app), with `flightfinderpro.com` and `www.flightfinderpro.com` attached. It has no studio login: it is the public site.
- **Update the page:** regenerate it in the studio, then `python export_static.py flight-finder-pro ../ffp-site` and `cd ../ffp-site && vercel deploy --prod`.
- **Tracking:** the page was published without the Ringba and Everflow tags. Paste them into `data/snippets/flight-finder-pro/`, regenerate, export and redeploy to track calls and clicks.
- **DNS (set at Namecheap):** A `@` to 216.198.79.1 and 64.29.17.1, CNAME `www` to d5d66069074dd7d9.vercel-dns-017.com. Keep the existing MX and TXT records. To roll back, restore A `@` to 162.159.140.166 and CNAME `www` to sites.ludicrous.cloud.

## Landing page tracker sites (preview deployments, no domain)
The Blue Wing Landing Page Tracker (Google Sheet, Tracker tab) lists each brand with an A (with video) and B (without video) page. Built so far, each as its own Vercel project, set to noindex, no tracking tags, not reviewed by Jeff:
- Debt Center B https://bw-debt-center-b.vercel.app
- Final Expense Store B https://bw-final-expense-store-b.vercel.app
- First Legal B https://bw-first-legal-b.vercel.app
- Senior's Guide A (with video) https://bw-senior-s-guide-a.vercel.app and B https://bw-senior-s-guide-b.vercel.app
Still to build: the A (with video) pages for Debt Center, Final Expense Store and First Legal, once their hero clips are downloaded from the Drive folder (First Legal Lobby.mp4, Final Expense Store Outside Clip.mp4, Debt Center Logo Drop 2.mp4).
- **Build:** `python build_sites.py debt-center:B first-legal:A:"C:/path/clip.mp4"` writes `../sites-deploy/<brand>-<variant>/` (the clip is compressed to a muted web video). **Deploy:** `python deploy_sites.py first-legal-a` creates `bw-<folder>` on Vercel and records the address in `../sites-deploy/urls.json`.
- **Tracker:** only the Build and Deploy cells and Notes were filled (owner Kunal, Built, Deployed, Live URL, dates). Jeff approval and the calculated Go-live check were left alone, so the tracker correctly flags these as "Deployed without approval".
