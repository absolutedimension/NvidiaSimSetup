#!/usr/bin/env python3
"""
One-time helper: exchange an OAuth Desktop client_id/secret for a Google Ads refresh_token.
Opens a browser, you approve, it prints the refresh_token to paste into google-ads.yaml.

    python3 get_refresh_token.py --client-id "XXX.apps.googleusercontent.com" --client-secret "YYY"

Needs: pip install google-auth-oauthlib   (installed with requirements.txt)
"""
import argparse

SCOPES = ["https://www.googleapis.com/auth/adwords"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret", required=True)
    args = ap.parse_args()
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise SystemExit("Run: pip install google-auth-oauthlib")

    flow = InstalledAppFlow.from_client_config(
        {"installed": {
            "client_id": args.client_id,
            "client_secret": args.client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }},
        scopes=SCOPES,
    )
    creds = flow.run_local_server(port=0, prompt="consent")
    print("\n" + "=" * 60)
    print("refresh_token:", creds.refresh_token)
    print("=" * 60)
    print("Paste this into google-ads.yaml as  refresh_token:")


if __name__ == "__main__":
    main()
