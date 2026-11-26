# Item 17: AdMaven API and webhooks for automated reporting

Owners: Ravi Palla, Kunal Achintya Reddy. Findings at 26 Nov 2026.

## Why it matters

Everflow shows AdMaven as our largest click source: 559,076 clicks in 30 days on *US Saving Center - Term Life Clicks*, with $0 revenue. We
cannot see what that traffic cost, or which AdMaven sources (zones) sent it, without AdMaven's own data.

## What AdMaven gives us

1. **URL macros (no login needed, works today).** AdMaven fills these into the destination URL on every click: `{:click_id}`, `{:cost}`,
   `{:campaign_id}`, `{:campaign_name}`, `{:creative_id}`, `{:source_id}`, `{:sub_source_id}`.
2. **Conversion postback (webhook into AdMaven).** AdMaven accepts a server-to-server postback per conversion, keyed by its click ID. The
   advertiser's unique postback ID is under *Profile > Tracking URL*, in the `info` parameter. Sending conversions back lets AdMaven optimise
   toward sources that convert.
3. **Reporting API.** AdMaven's API documentation is only inside the advertiser dashboard; it is not public. The API key is created in the
   dashboard. Trackers such as RedTrack use it to pull cost and stats per campaign and source. We need the dashboard login (Jeff is resetting the
   credentials, item 15) to read the endpoint list and create a key.

## Plan

**Step 1, now, no API needed.** Use this destination URL on every AdMaven campaign (Everflow tracking link):

    https://<everflow tracking link>?sub1={:source_id}&sub2={:sub_source_id}&sub3={:campaign_id}&sub4={:creative_id}&sub5={:cost}&click_id={:click_id}

Everflow then reports clicks and conversions per AdMaven source and creative, with the cost of each click. The landing pages already keep
`sub1` to `sub5` and `click_id` for the whole visit (see the template SOP). Ravi's daily traffic and rejects check (item 3) can then cut by source.

**Step 2, postback.** In Everflow, add an AdMaven postback on the AdMaven partner:
`https://<AdMaven postback URL>?info=<our unique ID>&click_id={sub_click_id}` (exact format to copy from *Profile > Tracking URL* in the
AdMaven dashboard). Test with one conversion.

**Step 3, API.** With the dashboard login: create an API key, add it to the studio's Integrations page (as Everflow and Ringba are), and pull
daily cost per campaign and source. The studio's Daily report (part 2) and the Publishers board then show AdMaven's real cost and profit next to
Everflow revenue. About half a day of work once the key and endpoint docs are in hand.

## Needed from the team

- Jeff: the AdMaven dashboard login (item 15).
- Ravi: switch the AdMaven destination URLs to the macro URL in step 1.
