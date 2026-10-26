"""One-time Strava OAuth: print the authorize URL, then swap the code for a refresh token.

Usage: STRAVA_CLIENT_ID=... python scripts/strava_auth.py
       STRAVA_CLIENT_ID=... STRAVA_CLIENT_SECRET=... python scripts/strava_auth.py CODE
The code is the `code=` value in the localhost URL Strava redirects to after you click Authorize
(the page itself won't load; that's expected).
"""
import os, sys, requests

cid = os.environ["STRAVA_CLIENT_ID"]
if len(sys.argv) < 2:
    print(f"https://www.strava.com/oauth/authorize?client_id={cid}&response_type=code"
          "&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read,activity:read_all")
else:
    r = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": cid, "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "code": sys.argv[1], "grant_type": "authorization_code"}, timeout=20)
    r.raise_for_status()
    j = r.json()
    print(f"athlete: {j['athlete'].get('firstname')} {j['athlete'].get('lastname')}")
    print(f"STRAVA_REFRESH_TOKEN={j['refresh_token']}")
