# Instagram Reels auto-publisher (Meta Graph API)

Publishes Reels to @trigunaiinnovations headlessly. Same Meta API family as the WhatsApp
Cloud API you already run.

## The 3 things you must provide
1. **IG_USER_ID** — the Instagram *Business* account id (a number). Get it from Graph API
   Explorer: `GET /me/accounts` → your Page → `GET /{page-id}?fields=instagram_business_account`.
2. **IG_ACCESS_TOKEN** — long-lived token with scopes `instagram_basic`,
   `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`.
   In your existing Meta app: add the **Instagram Graph API** product, generate a User token
   in Graph API Explorer with those scopes, then exchange for a long-lived (60-day) token.
3. **REELS_BASE_URL** — a PUBLIC url that serves the MP4s (Meta downloads them). Host the
   files in `../ig_reels_ready/` on your EC2 nginx or S3.

## Run
```bash
cp .env.example .env   # then fill it in (kept out of git)
set -a; source .env; set +a
python3 ig_reels_publish.py check       # verify token + account + 24h quota
python3 ig_reels_publish.py post-all    # publish all 11 reels in reels_manifest.json
```
`posted_state.json` records what went live so re-runs never double-post.

## Notes
- Content-publishing limit is ~25 posts / 24h — 11 is fine.
- No native scheduling in the API. To drip 1/day instead of all-at-once, run `post-all` daily
  via cron with a manifest trimmed to one item, or add a date field + guard.
- `instagram_content_publish` for your OWN account works with a token where you're an app
  admin/dev; publishing for *other* people's accounts needs App Review (not your case).
