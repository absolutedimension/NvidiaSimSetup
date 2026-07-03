#!/usr/bin/env python3
"""
LinkedIn video publisher — posts videos to the TrigunAI Company Page.

LinkedIn has NO "Reels" — these post as native feed videos on the Organization page.
Unlike Meta, LinkedIn does NOT fetch from a URL — you UPLOAD the file bytes.

Flow (Posts API + Videos API, versioned header required):
  1) initializeUpload -> returns a video URN + one-or-more upload URLs
  2) PUT the file bytes to the upload URL(s), capture ETag(s)
  3) finalizeUpload with the URN + ETags
  4) POST /rest/posts with author=urn:li:organization:{ORG_ID}, the video URN, commentary

Requires the app to have the **Community Management API** product approved (scope
w_organization_social) AND the app verified with the Company Page. See SKILL §LinkedIn.

Config from env (add to the same .env):
  LI_ACCESS_TOKEN   OAuth token with w_organization_social (+ r_organization_social)
  LI_ORG_ID         numeric Company Page/organization id (urn:li:organization:<this>)
  LI_VERSION        LinkedIn-Version header, e.g. 202405 (YYYYMM); bump as LinkedIn deprecates

Usage:
  set -a; source .env; set +a
  python3 li_reels_publish.py check
  python3 li_reels_publish.py post-all           # posts every unposted item in reels_manifest.json
  python3 li_reels_publish.py post-one --filename Day01_brand_universal_mind.mp4 --caption "..."
"""
import os, sys, json, time, argparse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "reels_manifest.json")
STATE = os.path.join(HERE, "li_posted_state.json")
REELS_DIR = os.path.join(os.path.dirname(HERE), "ig_reels_ready")  # local mp4s live here
API = "https://api.linkedin.com"


def _cfg():
    tok = os.environ.get("LI_ACCESS_TOKEN")
    org = os.environ.get("LI_ORG_ID")
    ver = os.environ.get("LI_VERSION", "202405")
    if not tok or not org:
        sys.exit("ERROR: need LI_ACCESS_TOKEN + LI_ORG_ID in env (source .env).")
    return tok, org, ver


def _hdrs(tok, ver, extra=None):
    h = {"Authorization": f"Bearer {tok}", "LinkedIn-Version": ver,
         "X-Restli-Protocol-Version": "2.0.0", "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h


def _req(method, url, headers, body=None, raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            txt = r.read().decode() or "{}"
            return r.status, r.headers, (json.loads(txt) if txt.strip().startswith(("{", "[")) else txt)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            body = json.loads(body)
        except Exception:
            pass
        return e.code, e.headers, body


def check():
    tok, org, ver = _cfg()
    # confirm token can see the org (needs r_organization_social)
    st, _, body = _req("GET", f"{API}/rest/organizations/{org}", _hdrs(tok, ver))
    if st == 200:
        print(f"OK  org urn:li:organization:{org}  name={body.get('localizedName','?')}  version={ver}")
    else:
        print(f"CHECK returned {st}: {json.dumps(body)[:400]}")
        print("If 403/permission: the Community Management API isn't approved yet, or token lacks r/w_organization_social.")


def _publish_one(tok, org, ver, filename, caption):
    path = os.path.join(REELS_DIR, filename)
    if not os.path.exists(path):
        raise RuntimeError(f"file not found locally: {path}")
    size = os.path.getsize(path)
    owner = f"urn:li:organization:{org}"
    # 1) initialize upload
    st, _, body = _req("POST", f"{API}/rest/videos?action=initializeUpload", _hdrs(tok, ver),
                       {"initializeUploadRequest": {"owner": owner, "fileSizeBytes": size,
                                                    "uploadCaptions": False, "uploadThumbnail": False}})
    if st not in (200, 201):
        raise RuntimeError(f"initializeUpload {st}: {json.dumps(body)[:300]}")
    val = body["value"]
    video_urn = val["video"]
    instrs = val["uploadInstructions"]
    # 2) upload each part (small files = single part)
    etags = []
    with open(path, "rb") as f:
        blob = f.read()
    for ins in instrs:
        start, end = ins.get("firstByte", 0), ins.get("lastByte", size - 1)
        chunk = blob[start:end + 1]
        st, hdrs, _ = _req("PUT", ins["uploadUrl"],
                           {"Authorization": f"Bearer {tok}", "Content-Type": "application/octet-stream"},
                           raw=chunk)
        if st not in (200, 201):
            raise RuntimeError(f"upload part {st}")
        etags.append(hdrs.get("ETag") or hdrs.get("etag"))
    # 3) finalize
    st, _, body = _req("POST", f"{API}/rest/videos?action=finalizeUpload", _hdrs(tok, ver),
                       {"finalizeUploadRequest": {"video": video_urn,
                                                  "uploadToken": "", "uploadedPartIds": etags}})
    if st not in (200, 201):
        raise RuntimeError(f"finalizeUpload {st}: {json.dumps(body)[:300]}")
    # 4) create the post
    post = {"author": owner, "commentary": caption, "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
            "content": {"media": {"title": filename, "id": video_urn}},
            "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False}
    st, hdrs, body = _req("POST", f"{API}/rest/posts", _hdrs(tok, ver), post)
    if st not in (200, 201):
        raise RuntimeError(f"create post {st}: {json.dumps(body)[:300]}")
    return hdrs.get("x-restli-id") or hdrs.get("X-RestLi-Id") or "posted"


def post_all():
    tok, org, ver = _cfg()
    items = json.load(open(MANIFEST))
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    print(f"Posting {len(items)} videos to LinkedIn org {org} ...")
    for i, it in enumerate(items, 1):
        fn = it["filename"]
        if state.get(fn, {}).get("post_id"):
            print(f"[{i}/{len(items)}] {fn} — already posted, skip"); continue
        print(f"[{i}/{len(items)}] {fn}")
        try:
            pid = _publish_one(tok, org, ver, fn, it["caption"])
            state[fn] = {"post_id": pid, "ts": int(time.time())}
            print(f"    POSTED {pid}")
            time.sleep(20)
        except Exception as e:
            print(f"    FAILED: {e}")
            state[fn] = {"error": str(e), "ts": int(time.time())}
        json.dump(state, open(STATE, "w"), indent=2)
    done = sum(1 for v in state.values() if v.get("post_id"))
    print(f"\nDone. {done}/{len(items)} live on LinkedIn.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check"); sub.add_parser("post-all")
    po = sub.add_parser("post-one"); po.add_argument("--filename", required=True); po.add_argument("--caption", required=True)
    a = ap.parse_args()
    if a.cmd == "check":
        check()
    elif a.cmd == "post-all":
        post_all()
    elif a.cmd == "post-one":
        tok, org, ver = _cfg()
        print(_publish_one(tok, org, ver, a.filename, a.caption))
