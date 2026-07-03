#!/usr/bin/env python3
"""
Instagram Reels publisher — Meta Graph API (same family as the WhatsApp Cloud API).

Publishes Reels to a Business/Creator IG account via the 3-step Content Publishing flow:
  1) create media container (media_type=REELS, video_url=<public url>, caption=...)
  2) poll container status until FINISHED (Meta downloads + transcodes the video)
  3) media_publish the container

KEY DIFFERENCE FROM WHATSAPP: Meta FETCHES the video from a PUBLIC URL. You do not
upload the file. Host the MP4s somewhere public (EC2 nginx / S3 / Cloudflare) and put
the base URL in REELS_BASE_URL.

Credentials are read from the environment — nothing is hardcoded:
  IG_USER_ID        Instagram Business account id (a number, NOT the @handle)
  IG_ACCESS_TOKEN   long-lived token with instagram_basic + instagram_content_publish
  REELS_BASE_URL    public base url, e.g. https://media.trigunai.com/reels
  GRAPH_VERSION     optional, default v21.0

Usage:
  export IG_USER_ID=... IG_ACCESS_TOKEN=... REELS_BASE_URL=https://.../reels
  python3 ig_reels_publish.py check                 # verify token + account + rate limit
  python3 ig_reels_publish.py post-all              # publish every unposted item in the manifest
  python3 ig_reels_publish.py post-one --filename Day01_brand_universal_mind.mp4 --caption "..."

State is tracked in posted_state.json so re-runs never double-post.
"""
import os, sys, json, time, argparse, urllib.parse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "reels_manifest.json")
STATE = os.path.join(HERE, "posted_state.json")
GRAPH = os.environ.get("GRAPH_VERSION", "v21.0")
BASE = f"https://graph.facebook.com/{GRAPH}"


def _cfg():
    uid = os.environ.get("IG_USER_ID")
    tok = os.environ.get("IG_ACCESS_TOKEN")
    burl = os.environ.get("REELS_BASE_URL", "").rstrip("/")
    missing = [k for k, v in [("IG_USER_ID", uid), ("IG_ACCESS_TOKEN", tok), ("REELS_BASE_URL", burl)] if not v]
    if missing:
        sys.exit(f"ERROR: missing env vars: {', '.join(missing)}. See the header of this file.")
    return uid, tok, burl


def _get(url, params):
    q = urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(f"{url}?{q}", timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _post(url, params):
    data = urllib.parse.urlencode(params).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _load(path, default):
    return json.load(open(path)) if os.path.exists(path) else default


def _save_state(s):
    json.dump(s, open(STATE, "w"), indent=2)


def check():
    uid, tok, burl = _cfg()
    me = _get(f"{BASE}/{uid}", {"fields": "id,username,name", "access_token": tok})
    if "error" in me:
        sys.exit(f"Token/account check FAILED: {me['error'].get('message')}")
    lim = _get(f"{BASE}/{uid}/content_publishing_limit",
               {"fields": "quota_usage,config", "access_token": tok})
    print(f"OK  account: @{me.get('username')} ({me.get('name')})  id={me.get('id')}")
    print(f"    base url: {burl}")
    q = (lim.get("data") or [{}])[0]
    print(f"    posts used in last 24h: {q.get('quota_usage','?')} / {q.get('config',{}).get('quota_limit','25')}")


def _publish_one(uid, tok, burl, filename, caption, cover=None):
    video_url = f"{burl}/{filename}"
    print(f"  → container: {video_url}")
    p = {"media_type": "REELS", "video_url": video_url, "caption": caption,
         "share_to_feed": "true", "access_token": tok}
    if cover:
        p["cover_url"] = f"{burl}/{cover}"
    c = _post(f"{BASE}/{uid}/media", p)
    if "error" in c:
        raise RuntimeError(c["error"].get("message"))
    cid = c["id"]
    # poll until FINISHED (Meta downloads + transcodes)
    for _ in range(60):  # up to ~10 min
        st = _get(f"{BASE}/{cid}", {"fields": "status_code,status", "access_token": tok})
        code = st.get("status_code")
        print(f"    status: {code}")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {cid}: {st.get('status')}")
        time.sleep(10)
    else:
        raise RuntimeError(f"container {cid} not ready after 10 min")
    r = _post(f"{BASE}/{uid}/media_publish", {"creation_id": cid, "access_token": tok})
    if "error" in r:
        raise RuntimeError(r["error"].get("message"))
    return r["id"]


def post_all():
    uid, tok, burl = _cfg()
    items = _load(MANIFEST, [])
    state = _load(STATE, {})
    if not items:
        sys.exit(f"No manifest at {MANIFEST}")
    print(f"Publishing {len(items)} reels to @{uid} ...")
    for i, it in enumerate(items, 1):
        fn = it["filename"]
        if state.get(fn, {}).get("media_id"):
            print(f"[{i}/{len(items)}] {fn} — already posted ({state[fn]['media_id']}), skip")
            continue
        print(f"[{i}/{len(items)}] {fn}")
        try:
            mid = _publish_one(uid, tok, burl, fn, it["caption"], it.get("cover"))
            state[fn] = {"media_id": mid, "ts": int(time.time())}
            _save_state(state)
            print(f"    PUBLISHED media_id={mid}")
            time.sleep(30)  # be gentle between posts
        except Exception as e:
            print(f"    FAILED: {e}")
            state[fn] = {"error": str(e), "ts": int(time.time())}
            _save_state(state)
    done = sum(1 for v in state.values() if v.get("media_id"))
    print(f"\nDone. {done}/{len(items)} live.")


def post_one(args):
    uid, tok, burl = _cfg()
    mid = _publish_one(uid, tok, burl, args.filename, args.caption, args.cover)
    print(f"PUBLISHED media_id={mid}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("post-all")
    po = sub.add_parser("post-one")
    po.add_argument("--filename", required=True)
    po.add_argument("--caption", required=True)
    po.add_argument("--cover")
    a = ap.parse_args()
    if a.cmd == "check":
        check()
    elif a.cmd == "post-all":
        post_all()
    elif a.cmd == "post-one":
        post_one(a)
