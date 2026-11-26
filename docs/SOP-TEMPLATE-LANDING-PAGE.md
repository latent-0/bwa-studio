# SOP: one template landing page for every affiliate offer (action item 25)

**Owner:** Kunal Achintya Reddy. **Used by:** the team that builds pages for affiliate offers (assembly line 1: Home Service Live, Final Expense,
Debt Center, Flight Finder).
**Goal:** every offer gets the same proven page, A and B, with only the brand, copy, numbers and legal changed. A new offer goes from signed to a
live, tracked page in one working day.

The template is the studio's pitch page (`pitch_site.py`). Flight Finder Pro is the model: hero with a looping branded video, an overlay card,
call buttons everywhere, compare table, reasons, steps, FAQ, and the legal footer. Do not design a new page per offer. Change the inputs below.

---

## 1. Collect the inputs (30 minutes)

Get all of this before you start. If anything is missing, the page is not ready to build.

| Input | Where it goes | Who supplies it |
|---|---|---|
| Brand name, vertical, one-line offer, audience | `brands.csv` | Offer owner |
| Phone hours (for example "Mon to Fri, 9am to 6pm EST") | `brands.csv` `hours` | Buyer |
| Brand colors (primary and accent) and tone | `brands.csv` | Jeff's brand assets |
| Branded video or images | `assets/<slug>/` | Jeff's team |
| Buyer and payout | `brands.csv` `buyer`, Partner onboarding | Ravi / Ryan |
| Ringba campaign ID and its number-insertion tag | `brands.csv` `ringba_campaign`, `data/snippets/<slug>/ringba_snippet.html` | Ravi (see the Ringba SOP, item 26) |
| Everflow offer ID and tracking tag | `brands.csv` `everflow_offer`, `data/snippets/<slug>/everflow_snippet.html` | Ravi (see the Everflow SOP, item 27) |
| Legal entity, contact email, legal text | `legal/<slug>/` | Tina / Ryan |
| Category: licensed agent or specialist | Copy wording (item 8) | Jeff approves |

## 2. Add the brand (10 minutes)

1. Add one row to `studio/brands.csv`. The `slug` is the brand name in lower case with dashes (for example `final-expense-store`).
2. Fill `name, vertical, offer, audience, phone, tone, primary_color, accent_color, cta, contact_email, hours, ringba_campaign, everflow_offer`.
   Leave `phone` as the brand's main number; the Ringba tag swaps it for a pool number on the page.
3. Open the studio. The brand appears on the Priority board in *Draft*.

## 3. Assets (20 minutes)

1. Put the brand's final video in `assets/<slug>/` and build variant A with it once (step 7 compresses it to `hero.mp4`).
2. Run `python hero_assets.py <slug>` to cut the hero loop, the still for variant B and the overlay image. Add the brand's shot times to `SHOTS`
   in `hero_assets.py` first (branded shots only, no spokesperson).
3. Never show "powered by Blue Wing Ads" or a Blue Wing logo on the page.

## 4. Copy (30 minutes)

1. Copy an existing pitch in the same category as a start: `data/pitch/<similar brand>.json` to `data/pitch/<slug>.json`.
2. Rewrite every field for the offer: `eyebrow, hero, hero_accent_words, bullets, cta, badges, compare, reasons, steps, free, close, faq, disclaimer`.
   Keep the structure and lengths. Do not add or remove sections.
3. Wording rules: use the approved category wording (licensed agent or specialist). No health, income or savings claims that legal has not
   cleared. No promises of approval or prices.

## 5. Legal (20 minutes, plus review)

1. Create `legal/<slug>/` with the brand's own pages: `privacy, terms, ccpa, opt-out, aup, cookies` (`.html`), plus `footer.txt` and
   `settings.json`. Any page you leave out, and the Marketing Partners page, is generated from the template with the brand's name. `settings.json` is
   `{"cookie_banner": true, "source": "<where the text came from>"}`. Start from the brand's own site text when it has one;
   otherwise copy the closest brand and change every name, entity and email.
2. Search the files for other brand names and "Blue Wing Ads" before you continue. Fix or flag each one (see `legal/NAME-FIXES.txt`).
3. In the studio, open **Legal review** for the brand and send it for sign-off. Counsel clears each claim there.

## 6. Tracking (15 minutes)

1. Paste the Ringba number-insertion tag into `data/snippets/<slug>/ringba_snippet.html`. If the offer runs on several channels with their own
   prices, use `channels.json` instead (see `docs/FE-CHANNEL-NUMBERS.md`) and run `python channels.py <slug>`.
2. Paste the Everflow tag into `data/snippets/<slug>/everflow_snippet.html`.
3. Nothing else to do for click tracking. The template keeps these values from the link for the whole visit and adds them to the lead form:
   `_ef_transaction_id, eftid, oid, affid, sub1 to sub5, click_id, gclid, fbclid, utm_source, utm_medium, utm_campaign`.

## 7. Generate, build and deploy (20 minutes)

1. In the studio, open the brand and click **Generate**. The checklist must show *Page up*, *Tracking captured* and *Compliance pages* passed.
2. Build both variants:
   `python build_sites.py <slug>:A:"<path to video>" <slug>:B`
   (A has the hero video, B the still image. Both are marked noindex until approved.)
3. Deploy: `python deploy_sites.py <slug>-a <slug>-b`. The pages go live at `https://bw-<slug>-a.vercel.app` and `-b`, and the addresses are
   written to the Campaign Tracker automatically.

## 8. Check before you hand it over (15 minutes)

Open both variants on a phone and a laptop and tick each line:

- [ ] Every call button shows a pool number (not the main number) after a second, and tapping it dials that number.
- [ ] The hero video plays muted on iPhone; variant B shows the still image.
- [ ] Footer links open all seven legal pages; the cookie banner shows and closes.
- [ ] Open the page with `?sub1=test&utm_source=test`, move to another page and back: the values are still in `window.BWA_TRACKING`.
- [ ] No other brand's name, and no Blue Wing Ads, anywhere on the page or the legal pages.
- [ ] Place one test call. It shows in Ringba against the right campaign and publisher.
- [ ] Studio checklist: all seven checks pass (*Buyer assigned*, *Legal review* and *Test delivery* included).

## 9. Approve and send traffic

1. Jeff approves the page in the Campaign Tracker (the *Landing page Draft feedback* column). Apply any feedback, rebuild, redeploy.
2. Give each publisher the Everflow tracking link that points to the approved variant, with their sub IDs. For channel numbers, add `?ch=`.
3. Add the publisher in **Partner onboarding** and send the welcome email. Their traffic then shows on the **Publishers** board and in part 2 of the
   **Daily report**.

## Time budget

| Step | Time |
|---|---|
| Inputs, brand row, assets | 1 hour |
| Copy and legal draft | 50 minutes |
| Tracking, build, deploy | 35 minutes |
| Checks | 15 minutes |
| **Total, before legal sign-off** | **about 2.5 hours** |
