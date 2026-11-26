# Final Expense: phone numbers by channel (action item 18)

Owners: Ravi Palla, Kunal Achintya Reddy. Status at 26 Nov 2026: studio side built and tested; the Ringba side waits on two decisions (below).

## Goal

Keep the static-bid buyers on Final Expense. Give each traffic channel (search, CTV, push, email) its own phone number, so every call shows
which channel it came from and what the buyer paid for it.

## How it works

1. **Ringba.** On the campaign *Final Expense Store - Final Expense* (CA4feee4c2ae4d4517870a7af501abf764), add one publisher per channel:
   *BWA FE - Search*, *BWA FE - CTV*, *BWA FE - Push*, *BWA FE - Email*. Give each its own number. The buyers (targets) and their static bids
   do not change. Ringba then reports calls, revenue and payout per channel, because each channel is its own publisher.
2. **Landing page.** The Final Expense Store page reads the channel from the link, `?ch=search|ctv|push|email`. It also reads `utm_medium`, where
   cpc, ppc and sem count as search, ott and tv as CTV, inpage, pop and native as push, and newsletter as email. It shows that channel's number in every
   call button, and remembers the channel for the rest of the visit. Every other visitor sees the ring-pool number, exactly as today.
3. **Studio report.** The Daily report (/report, part 2) and the Publishers board pick up each channel publisher automatically, with calls, revenue
   and profit.

## Numbers

| Channel | Number | Where it comes from | Status |
|---|---|---|---|
| Search | (888) 865-1054 | Already in the Ringba account, unassigned, no calls since Dec 2025 | Attach to the campaign |
| Email | (866) 661-3295 | Already in the Ringba account, unassigned, no calls since Feb 2026 | Attach to the campaign |
| CTV | to buy | Toll-free, easy to read on screen | Needs purchase approval |
| Push | to buy | Toll-free | Needs purchase approval |

The other 12 unassigned numbers in the account got calls this month, most likely from old creatives. Reusing them would mix stray calls into the
channel figures, so they are left alone.

## Decisions needed

- **Jeff or Ryan:** approve buying 2 toll-free numbers in Ringba (CTV and push).
- **Ravi:** confirm the static bid each buyer pays per channel, if a channel is priced differently. Today all channels route to the same buyers.

## Switching a channel on

1. In Ringba, attach the number to the channel publisher on the campaign, and place a test call.
2. In `studio/data/snippets/final-expense-store/channels.json`, set `"ready": true` for that channel.
3. Run `python channels.py final-expense-store`, then rebuild and deploy the Final Expense Store site (`build_sites.py`, `deploy_sites.py`).
4. Check: open the page with `?ch=<channel>`. The call buttons show the channel number.

The page only shows a channel number once it is marked ready, so a visitor is never shown a number that does not ring.

## Links for media buyers

- Search: `https://bw-final-expense-store-a.vercel.app/?ch=search`, or keep `utm_medium=cpc`
- Push: `...?ch=push`
- Email: `...?ch=email`
- CTV: show the CTV number on screen. For a vanity URL, use `...?ch=ctv`.
