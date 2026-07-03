#!/usr/bin/env python3
"""
Facebook Reels publisher — posts the same reels to a Facebook Page.

Different flow from Instagram. Facebook Reels use a 3-phase upload on the Page's
/video_reels edge:
  1) start   -> returns video_id + an upload_url (rupload.facebook.com)
  2) upload  -> POST to upload_url with headers: Authorization: OAuth <token>, file_url: <public mp4>
                (hosted upload — Facebook fetches the file from the URL)
  3) finish  -> upload_phase=finish, video_state=PUBLISHED, description=<caption>
  then poll /{video_id}?fields=status until publishing completes.

Config from environment (reuse the same .env as the IG publisher):
  FB_PAGE_ID          Facebook Page id (default: Trigunai Innovations = 1235364529650979)
  IG_ACCESS_TOKEN     the PAGE access token (the one already in .env works — it's the page token)
  REELS_BASE_URL      public base url serving the mp4s
  GRAPH_VERSION       optional, default v21.0

Needs the token to carry pages_manage_posts (+ pages_read_engagement). If you get a
(#200)/permissions error, regenerate the token in Graph API Explorer WITH pages_manage_posts.

Usage:
  set -a; source .env; set +a
  python3 fb_reels_publish.py check
  python3 fb_reels_publish.py post-all
"""
import os, sys, json, time, urllib.parse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "reels_manifest.json")
STATE = os.path.join(HERE, "fb_posted_state.json")
GRAPH = os.environ.get("GRAPH_VERSION", "v21.0")
BASE = f"https://graph.facebook.com/{GRAPH}"
PAGE = os.environ.get("FB_PAGE_ID", "1235364529650979")


def _cfg():
    tok = os.environ.get("IG_ACCESS_TOKEN")
    burl = os.environ.get("REELS_BASE_URL", "").rstrip("/")
    if not tok or not burl:
        sys.exit("ERROR: need IG_ACCESS_TOKEN + REELS_BASE_URL in env (source .env).")
    return tok, burl


def _get(url, params):
    with_q = f"{url}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(with_q, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _post(url, params, headers=None, data_empty=False):
    data = urllib.parse.urlencode(params).encode() if params else (b"" if data_empty else None)
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _load(path, default):
    return json.load(open(path)) if os.path.exists(path) else default


def check():
    tok, burl = _cfg()
    me = _get(f"{BASE}/{PAGE}", {"fields": "name,category,fan_count", "access_token": tok})
    if "error" in me:
        sys.exit(f"Page/token check FAILED: {me['error'].get('message')}")
    print(f"OK  page: {me.get('name')}  id={PAGE}  category={me.get('category')}")
    print(f"    base url: {burl}")


def _publish_one(tok, burl, filename, description):
    # phase 1: start
    start = _post(f"{BASE}/{PAGE}/video_reels", {"upload_phase": "start", "access_token": tok})
    if "error" in start:
        raise RuntimeError(f"start: {start['error'].get('message')}")
    vid = start["video_id"]
    upload_url = start["upload_url"]
    print(f"    video_id={vid}")
    # phase 2: hosted upload (Facebook fetches the file_url)
    up = _post(upload_url, None, headers={
        "Authorization": f"OAuth {tok}",
        "file_url": f"{burl}/{filename}",
    }, data_empty=True)
    if not (isinstance(up, dict) and up.get("success")):
        raise RuntimeError(f"upload: {json.dumps(up)}")
    # phase 3: finish + publish
    fin = _post(f"{BASE}/{PAGE}/video_reels", {
        "upload_phase": "finish", "video_id": vid,
        "video_state": "PUBLISHED", "description": description,
        "access_token": tok,
    })
    if "error" in fin:
        raise RuntimeError(f"finish: {fin['error'].get('message')}")
    # poll status
    for _ in range(60):
        st = _get(f"{BASE}/{vid}", {"fields": "status", "access_token": tok})
        pub = (st.get("status") or {}).get("publishing_phase", {}).get("status")
        vs = (st.get("status") or {}).get("video_status")
        print(f"    publishing: {pub or vs}")
        if pub == "complete":
            return vid
        if pub == "error" or vs == "error":
            raise RuntimeError(f"processing error: {json.dumps(st)}")
        time.sleep(10)
    return vid  # likely fine; FB finishes async


def post_all():
    tok, burl = _cfg()
    items = _load(MANIFEST, [])
    state = _load(STATE, {})
    print(f"Publishing {len(items)} reels to FB Page {PAGE} ...")
    for i, it in enumerate(items, 1):
        fn = it["filename"]
        if state.get(fn, {}).get("video_id"):
            print(f"[{i}/{len(items)}] {fn} — already posted, skip")
            continue
        print(f"[{i}/{len(items)}] {fn}")
        try:
            vid = _publish_one(tok, burl, fn, it["caption"])
            state[fn] = {"video_id": vid, "ts": int(time.time())}
            json.dump(state, open(STATE, "w"), indent=2)
            print(f"    PUBLISHED video_id={vid}")
            time.sleep(20)
        except Exception as e:
            print(f"    FAILED: {e}")
            state[fn] = {"error": str(e), "ts": int(time.time())}
            json.dump(state, open(STATE, "w"), indent=2)
    done = sum(1 for v in state.values() if v.get("video_id"))
    print(f"\nDone. {done}/{len(items)} live on Facebook.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    {"check": check, "post-all": post_all}.get(cmd, check)()
