---
name: trigunai-social-reels
description: >
  Publish and manage Reels on Instagram AND Facebook for TrigunAI programmatically via the
  Meta Graph API (no manual uploading). Given a folder of vertical MP4s + captions, it hosts
  them on the EC2 box (public URL), then publishes each to @trigunaiinnovations (Instagram)
  and the Trigunai Innovations Facebook Page as Reels, tracking what went live so it never
  double-posts. Also handles: checking publish status, re-posting failures, adding new reels,
  and drip-scheduling 1/day via cron. Use when the user wants to: "post reels", "upload reels
  to instagram / facebook", "publish to IG and FB", "post to social", "schedule reels",
  "cross-post to facebook", "batch upload reels", "manage the reels", or add new reels to the
  pipeline. Handles the full Meta token setup (Business account + Page link + app use cases +
  permissions) with every gotcha we already hit baked in. Companion to shader-reactive-pattern
  -music / production-video-trigunai (which MAKE the videos) and trigunai-youtube (YouTube side).
  Runs against the EC2 A10G box (EIP 34.192.145.204). Engine: marketing_pipeline/ig_publish/.
---

# TrigunAI Social Reels — publish to Instagram + Facebook by API

> **Job:** take finished vertical reels (1080×1920 MP4) + captions and push them to
> **Instagram (@trigunaiinnovations)** and the **Trigunai Innovations Facebook Page** as
> Reels — headlessly, via the Meta Graph API. No manual app uploading, no Business Suite
> clicking. Tracks state so re-runs never duplicate.

The engine lives in **`marketing_pipeline/ig_publish/`**:
`ig_reels_publish.py` (Instagram) · `fb_reels_publish.py` (Facebook) · `reels_manifest.json`
(filenames + captions) · `.env` (secrets, gitignored) · `posted_state.json` / `fb_posted_state.json`
(what's live).

---

## 0. Locked facts (verified working 2026-07-02)

| Thing | Value |
|---|---|
| Instagram account | **@trigunaiinnovations** — must be **Business** + linked to the FB Page |
| **IG_USER_ID** | `17841480511571246` |
| Facebook Page | **Trigunai Innovations**, page id **`1235364529650979`** |
| Meta app | **Gurukul** (the same app that runs WhatsApp) |
| **REELS_BASE_URL** | `https://rtx.trigunai.com/reels` (Caddy on EC2, serves `/var/www/reels`) |
| EC2 box | EIP **34.192.145.204** (TrigunAI-Omniverse), SSH `~/.ssh/trigunai_key.pem` |
| Graph version | v21.0 |

Meta **fetches** the videos from the public URL (it does NOT accept file uploads like
WhatsApp). So the MP4s must be reachable at `REELS_BASE_URL/<filename>`.

---

## 1. The daily/whenever loop

### Step A — make sure the videos are hosted (EC2 up + files in /var/www/reels)
```bash
EC2=34.192.145.204; PEM=~/.ssh/trigunai_key.pem
# reels are copied into /var/www/reels (dir 755, files 644) and served by Caddy at
# rtx.trigunai.com/reels/<file>. To add/refresh, scp then fix perms:
scp -i $PEM local_reel.mp4 ubuntu@$EC2:/tmp/ && \
  ssh -i $PEM ubuntu@$EC2 'sudo cp /tmp/local_reel.mp4 /var/www/reels/ && sudo chmod 644 /var/www/reels/*.mp4'
# verify it serves (must return 200, content-type video/mp4):
curl -sI https://rtx.trigunai.com/reels/<file>.mp4 | grep -iE "HTTP|content-type"
```
Caddy config (already in place) — the `/reels/*` file_server was added to the existing
`rtx.trigunai.com` block; don't remove the `reverse_proxy localhost:8010` that runs RTX studio.

### Step B — build/refresh the manifest
`reels_manifest.json` = a JSON array of `{ "filename": "...", "caption": "..." }`. Captions
carry the real URLs: **courses → acharya.trigunai.com**, **brand/series → trigunai.com**.
Brand voice rules from `content-marketing-emotion-connect` apply (emotion first, no
fear-mongering, no guaranteed-results, "course completion certificate" wording).

### Step C — token in .env (see §2 if expired/missing)
```bash
cd marketing_pipeline/ig_publish
cp .env.example .env   # then paste the PAGE access token; base URL + IG_USER_ID prefilled
```

### Step D — publish
```bash
set -a; source .env; set +a
python3 ig_reels_publish.py check      # confirms @trigunaiinnovations + 24h quota
python3 ig_reels_publish.py post-all   # Instagram — all unposted items in the manifest
python3 fb_reels_publish.py check      # confirms the FB Page
python3 fb_reels_publish.py post-all   # Facebook — same reels as FB Reels
```
Long-running (Meta transcodes each ~1–2 min) → run in the background and watch with an
`until ! pgrep -f post-all; do sleep 15; done` loop. State files mean a re-run only does
what hasn't posted yet.

### Step E — report
Read `posted_state.json` (IG) + `fb_posted_state.json` (FB): count `video_id`/`media_id`
(live) vs `error` (failed). Report live/total per platform, honestly.

---

## 2. Token setup — the ONE-TIME plumbing (and every gotcha we hit)

> **CURRENT STATE (2026-07-02): a PERMANENT page token is already installed in `.env`.**
> It's a page token derived from a 60-day long-lived user token → it does NOT expire.
> So **future runs are zero-click**: just `source .env` and `post-all`. You only need to
> redo the steps below if the token ever breaks (FB password change, permissions revoked,
> or the app config changes). Underlying long-lived user token expires ~2026-08-31; the
> derived page token stays valid beyond that unless revoked.

**To re-mint the permanent token if it ever breaks:** get a fresh full-scope User token in
Explorer + the App Secret (App settings → Basic → Show), put `FB_APP_ID=1047742064872397`,
`FB_APP_SECRET=…`, `FB_USER_TOKEN=…` temporarily in `.env`, then exchange:
```
GET /oauth/access_token?grant_type=fb_exchange_token&client_id={app}&client_secret={secret}&fb_exchange_token={short}
```
→ take the long-lived user token → `GET /{page-id}?fields=access_token&access_token={long-lived}`
→ that page token is permanent → write as `IG_ACCESS_TOKEN`, delete the temp secret lines.
Verify with `/debug_token` (page token `expires_at` should be `0` = never).

Explorer tokens are **short-lived (~1–2 h)** — the exchange above is what makes it permanent.
The token you actually use in `.env` is the **PAGE access token** for Trigunai Innovations.

**Prereqs (do once, in this order — this is what took an hour the first time):**
1. **@trigunaiinnovations must be a Business account** (IG app → Settings → For professionals
   → Account type and tools → Business). Personal/Creator won't publish.
2. **A real Facebook Page** (Trigunai Innovations) must exist and be **connected** to the IG
   account. Link it from the FB/Business-Suite side (Instagram web has no page-connect on
   desktop). The Page must be admined by the **same** Facebook login used in Graph API Explorer.
3. **Gurukul app needs two use cases** (App Dashboard → Add use cases):
   - **"Manage messaging & content on Instagram"** → then open **"API setup with Facebook
     login"** (NOT Instagram login) — this exposes `instagram_basic` + `instagram_content_publish`.
   - **"Manage everything on your Page"** → exposes `pages_manage_posts`.

**Generate the token (Graph API Explorer, app = Gurukul, User Token):**
Add these permissions, then **Generate Access Token** and **complete the FB popup fully**
(tick the Trigunai Innovations Page, approve the Page-management consent):
```
instagram_basic  instagram_content_publish  pages_show_list
pages_read_engagement  pages_manage_posts  business_management
```
Then get the PAGE token: run `me/accounts` → copy the **Trigunai Innovations** entry's
`access_token`. Put THAT in `.env` as `IG_ACCESS_TOKEN` (it works for both IG and FB here).

**Gotchas that WILL bite (all real, all hit):**
| Symptom | Cause / fix |
|---|---|
| `instagram_content_publish` not in the permission list | App missing the Instagram "Facebook login" use case → add it (prereq 3). |
| `me/accounts` only shows "Hear Me Now", not TrigunAI | IG not linked to the TrigunAI Page, OR the Page wasn't ticked in the token popup. Link + re-mint, tick the Page. |
| `instagram_business_account` is null on the page | IG account isn't connected to that Page yet. Connect it (prereq 2). |
| Publish → `(#200) lack of pages_manage_posts` | Permission selected in list ≠ granted. Regenerate and APPROVE the popup consent. Verify with `me/permissions`. |
| Popup → `Invalid Scopes: pages_read_user_content` | That scope is deprecated — **remove it** from the list, regenerate. |
| Publish → `(#200) lack of pages_read_engagement` | FB Reels needs BOTH `pages_manage_posts` AND `pages_read_engagement` granted together. |
| Selected a permission but token doesn't have it | The token in the box predates the selection — click **Generate** again and finish the OAuth popup. Check `GET /me/permissions`. |

Verify what's actually granted before publishing:
```bash
curl -s "https://graph.facebook.com/v21.0/me/permissions?access_token=$USER_TOKEN"
```

---

## 3. The two publish flows (why they differ)

- **Instagram** (`ig_reels_publish.py`): 3 calls — `POST /{ig-user-id}/media` (media_type=REELS,
  video_url, caption, share_to_feed=true) → poll container `status_code` until `FINISHED` →
  `POST /{ig-user-id}/media_publish`. `share_to_feed` also puts it in the IG feed (NOT Facebook).
- **Facebook** (`fb_reels_publish.py`): 3-phase — `POST /{page-id}/video_reels?upload_phase=start`
  (returns video_id + upload_url) → `POST upload_url` with headers `Authorization: OAuth <token>`
  + `file_url: <public mp4>` (hosted fetch) → `?upload_phase=finish&video_state=PUBLISHED&
  description=<caption>` → poll `/{video_id}?fields=status` until `publishing_phase=complete`.

**Instagram publishing does NOT cross-post to Facebook** — that's why there are two scripts.

---

## 4. Managing / extending

- **Add new reels:** drop the MP4 in `/var/www/reels` (Step A), add a `{filename,caption}` row
  to `reels_manifest.json`, run `post-all` — state files skip the already-posted ones.
- **Re-post a failure:** delete that file's entry from `posted_state.json` / `fb_posted_state.json`
  and re-run `post-all`.
- **Drip 1/day instead of all-at-once** (better for reach): the API has no native scheduling —
  run `post-all` daily via cron with a manifest trimmed to one item, or add a `date` field +
  guard. Needs a **60-day long-lived token**:
  `GET /oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={secret}&fb_exchange_token={short-token}`.
- **Content-publishing limit:** IG ~25 posts / 24h. Check via `/{ig-user-id}/content_publishing_limit`.
- **Profile bio/name/links: NOT settable by API** — Instagram exposes no profile-edit endpoint.
  Bio + Name on instagram.com/accounts/edit; the bio LINKS are mobile-app only.

---

## 4b. LinkedIn (Company Page) — PENDING LinkedIn approval (as of 2026-07-02)

Script built: **`li_reels_publish.py`** (untested until access lands). LinkedIn has **no Reels**
— these post as native org feed videos. Unlike Meta, LinkedIn **uploads the file bytes** (no
URL fetch), so it reads MP4s from `marketing_pipeline/ig_reels_ready/`.

**Status:** Company-page posting needs the **Community Management API** (scope
`w_organization_social`). That product must be the **ONLY** product on its app, so a dedicated
LinkedIn app was created: **"TrigunAI Community"**, Client ID **`78ucb3zcefmnap`**, verified
with the Trigunaï Innovations page. The **Development Tier access form was submitted 2026-07-02**
→ now in LinkedIn review (watch **deepak@trigunai.com** for a **Microsoft Vetting Services**
verification email — the request stalls until that's completed; have incorp cert + PAN ready).

**When the approval email arrives — finish it:**
1. In the TrigunAI Community app → **Auth** tab: set a redirect URL, note Client ID + Secret.
2. Run 3-legged OAuth for scopes `w_organization_social` + `r_organization_social` → get an
   access token (LinkedIn tokens ~60 days; refresh tokens available).
3. Get the **org id** (numeric) of the Trigunaï Innovations page → `LI_ORG_ID`.
4. Add to `.env`: `LI_ACCESS_TOKEN`, `LI_ORG_ID`, `LI_VERSION` (e.g. 202405).
5. `python3 li_reels_publish.py check` then `post-all` (uploads bytes → Posts API).

**Personal-profile posting** (Deepak's feed) is self-serve via the FIRST app ("TrigunAI",
Client ID `78jlinm2redrty`) with `w_member_social` — buildable without review if ever wanted.

---

## 5. Honesty + safety guardrails

- **"Posted" = the API returned a media_id/video_id AND status reached FINISHED/complete.** A
  created container that never finished is NOT posted — report it as failed.
- **Report real live counts per platform**, including zeros/failures. State files are the record.
- **Tokens are secrets** — keep them in gitignored `.env`, never echo them back, never commit.
  Explorer tokens expire in ~1–2 h; if a run fails with an auth error mid-way, re-mint (§2).
- **Don't cold-blast** — posting all N at once looks bot-like and hurts reach; prefer the daily
  drip (§4) unless the user explicitly says "post all now."
- Keep the EC2 box **running** during a publish (Meta fetches the videos live from it).
