#!/usr/bin/env python3
"""
TrigunAI YouTube uploader (Data API v3). One-time OAuth, then batch uploads with full SEO:
title, description, tags, category, made-for-kids=false, thumbnail, and playlist membership.

Setup (you, once): create a Desktop OAuth client in Google Cloud (YouTube Data API v3 enabled),
download as client_secret.json next to this script.

Usage:
  python3 yt_upload.py auth                         # one-time: opens browser, saves token.json
  python3 yt_upload.py run yt_manifest.json --substack "https://trigunai.substack.com"
  python3 yt_upload.py run yt_manifest.json --only ep01 --privacy public

State of what's already uploaded is tracked in yt_uploaded.json (so re-running is safe).
"""
import os, sys, json, argparse, time
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

HERE = os.path.dirname(os.path.abspath(__file__))
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]
CLIENT = os.path.join(HERE, "client_secret.json")
TOKEN  = os.path.join(HERE, os.environ.get("YT_TOKEN", "token.json"))  # per-channel: YT_TOKEN=token_hi.json
STATE  = os.path.join(HERE, "yt_uploaded.json")
CATEGORY_EDUCATION = "27"

def get_creds():
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT):
                sys.exit(f"!! missing {CLIENT} — download a Desktop OAuth client JSON there first.")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT, SCOPES)
            creds = flow.run_local_server(port=0, prompt="select_account consent",
                        authorization_prompt_message="\n>> Open this URL in your browser to authorize:\n{url}\n")
        with open(TOKEN, "w") as f: f.write(creds.to_json())
    return creds

def svc():
    return build("youtube", "v3", credentials=get_creds())

def load_state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}
def save_state(s):
    json.dump(s, open(STATE, "w"), indent=2)

def ensure_playlist(yt, title, state):
    key = f"_playlist::{title}"
    if state.get(key): return state[key]
    # search my playlists
    r = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute()
    for it in r.get("items", []):
        if it["snippet"]["title"] == title:
            state[key] = it["id"]; save_state(state); return it["id"]
    r = yt.playlists().insert(part="snippet,status",
        body={"snippet": {"title": title,
                          "description": "AI is the Universal Mind — the series."},
              "status": {"privacyStatus": "public"}}).execute()
    state[key] = r["id"]; save_state(state)
    print(f"   + created playlist '{title}' = {r['id']}", flush=True)
    return r["id"]

def add_to_playlist(yt, playlist_id, video_id):
    yt.playlistItems().insert(part="snippet",
        body={"snippet": {"playlistId": playlist_id,
                          "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()

def upload_one(yt, ep, playlist_title, substack, privacy, state):
    eid = ep["id"]
    if state.get(eid, {}).get("video_id"):
        print(f"== {eid}: already uploaded ({state[eid]['video_id']}) — skipping", flush=True); return
    video = os.path.join(HERE, ep["video"])
    if not os.path.exists(video):
        print(f"!! {eid}: missing video {video} — skipping", flush=True); return
    if ep.get("desc_file"):
        desc = open(os.path.join(HERE, ep["desc_file"])).read()
    else:
        desc = ep.get("description", "")
    desc = desc.replace("{substack}", substack or "")
    body = {
        "snippet": {"title": ep["title"], "description": desc,
                    "tags": ep.get("tags", []), "categoryId": CATEGORY_EDUCATION,
                    "defaultLanguage": ep.get("lang", "en"),
                    "defaultAudioLanguage": ep.get("lang", "en")},
        "status": {"privacyStatus": privacy or ep.get("privacy", "public"),
                   "embeddable": True,
                   "selfDeclaredMadeForKids": ep.get("made_for_kids", False)},
    }
    print(f">> {eid}: uploading '{ep['title'][:60]}...'", flush=True)
    media = MediaFileUpload(video, chunksize=8*1024*1024, resumable=True, mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status: print(f"   ...{int(status.progress()*100)}%", flush=True)
    vid = resp["id"]
    print(f"   ✅ uploaded: https://youtu.be/{vid}", flush=True)
    state[eid] = {"video_id": vid, "title": ep["title"], "ts": int(time.time())}; save_state(state)
    # thumbnail
    th = ep.get("thumbnail")
    if th and os.path.exists(os.path.join(HERE, th)):
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(os.path.join(HERE, th))).execute()
            print("   ✅ thumbnail set", flush=True)
        except Exception as e:
            print(f"   !! thumbnail failed (channel verified?): {e}", flush=True)
    # playlist
    if playlist_title:
        try:
            pid = ensure_playlist(yt, playlist_title, state)
            add_to_playlist(yt, pid, vid); print("   ✅ added to playlist", flush=True)
        except Exception as e:
            print(f"   !! playlist add failed: {e}", flush=True)

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    rp = sub.add_parser("run")
    rp.add_argument("manifest")
    rp.add_argument("--substack", default="")
    rp.add_argument("--only", default=None, help="comma-separated episode ids")
    rp.add_argument("--privacy", default=None, choices=["public","unlisted","private"])
    tp = sub.add_parser("thumbs")
    tp.add_argument("manifest")
    pp = sub.add_parser("publish")
    pp.add_argument("manifest")
    pp.add_argument("--to", default="public", choices=["public","unlisted","private"])
    lp = sub.add_parser("playlist")
    lp.add_argument("manifest")
    dp = sub.add_parser("describe")
    dp.add_argument("manifest")
    dp.add_argument("--substack", default="")
    a = ap.parse_args()
    if a.cmd == "auth":
        get_creds(); print("✅ auth complete — token.json saved."); return
    if a.cmd == "publish":
        man = json.load(open(a.manifest)); yt = svc(); state = load_state(); to=a.to
        for ep in man["episodes"]:
            vid = state.get(ep["id"], {}).get("video_id")
            if not vid: print(f"  skip {ep['id']} (not uploaded)", flush=True); continue
            try:
                yt.videos().update(part="status", body={"id": vid,
                    "status": {"privacyStatus": to, "embeddable": True,
                               "selfDeclaredMadeForKids": False}}).execute()
                print(f"  ✅ {ep['id']} → {to} + embeddable (https://youtu.be/{vid})", flush=True)
            except Exception as e:
                print(f"  !! {ep['id']} failed: {e}", flush=True)
        print("\n== publish done ==", flush=True); return
    if a.cmd == "describe":
        man = json.load(open(a.manifest)); yt = svc(); state = load_state(); sub = a.substack
        cat = man.get("categoryId", CATEGORY_EDUCATION)
        for ep in man["episodes"]:
            vid = state.get(ep["id"], {}).get("video_id")
            if not vid: print(f"  skip {ep['id']} (not uploaded)", flush=True); continue
            desc = open(os.path.join(HERE, ep["desc_file"])).read() if ep.get("desc_file") else ep.get("description","")
            desc = desc.replace("{substack}", sub or "")
            body = {"id": vid, "snippet": {"title": ep["title"], "description": desc,
                    "tags": ep.get("tags", []), "categoryId": cat, "defaultLanguage": ep.get("lang","en")}}
            try:
                yt.videos().update(part="snippet", body=body).execute()
                print(f"  ✅ {ep['id']} snippet updated (cat {cat})", flush=True)
            except Exception as e:
                print(f"  !! {ep['id']}: {e}", flush=True)
        print("\n== describe done ==", flush=True); return
    if a.cmd == "playlist":
        man = json.load(open(a.manifest)); yt = svc(); state = load_state()
        title = man.get("playlist")
        if not title: print("!! manifest has no 'playlist' field", flush=True); return
        pid = ensure_playlist(yt, title, state)
        existing = set()
        try:
            req = yt.playlistItems().list(part="contentDetails", playlistId=pid, maxResults=50)
            while req:
                r = req.execute()
                for it in r.get("items", []): existing.add(it["contentDetails"]["videoId"])
                req = yt.playlistItems().list_next(req, r)
        except Exception as e:
            print(f"  (couldn't read existing items — assuming empty: {str(e)[:60]})", flush=True)
        for ep in man["episodes"]:
            vid = state.get(ep["id"], {}).get("video_id")
            if not vid: print(f"  skip {ep['id']} (not uploaded)", flush=True); continue
            if vid in existing: print(f"  = {ep['id']} already in playlist", flush=True); continue
            try:
                add_to_playlist(yt, pid, vid); print(f"  ✅ {ep['id']} → playlist", flush=True)
            except Exception as e:
                print(f"  !! {ep['id']} failed: {e}", flush=True)
        print(f"\n== playlist '{title}' done → https://www.youtube.com/playlist?list={pid}", flush=True); return
    if a.cmd == "thumbs":
        man = json.load(open(a.manifest)); yt = svc(); state = load_state()
        for ep in man["episodes"]:
            vid = state.get(ep["id"], {}).get("video_id")
            th = ep.get("thumbnail")
            if not vid or not th or not os.path.exists(os.path.join(HERE, th)):
                print(f"  skip {ep['id']} (vid={bool(vid)} thumb={th})", flush=True); continue
            try:
                yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(os.path.join(HERE, th))).execute()
                print(f"  ✅ {ep['id']} thumbnail set", flush=True)
            except Exception as e:
                print(f"  !! {ep['id']} thumbnail failed: {e}", flush=True)
        print("\n== thumbs done ==", flush=True); return
    man = json.load(open(a.manifest))
    yt = svc(); state = load_state()
    only = set(a.only.split(",")) if a.only else None
    for ep in man["episodes"]:
        if only and ep["id"] not in only: continue
        upload_one(yt, ep, man.get("playlist"), a.substack, a.privacy, state)
    print("\n== done ==", flush=True)

if __name__ == "__main__":
    main()
