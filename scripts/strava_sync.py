"""Mark ledger rows done from Strava activities in the last 7 days.

Env: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN.
One-time setup: create an app at strava.com/settings/api, authorize with scope
activity:read_all, exchange the code for a refresh token. Store it as a secret.

Matching rule: same date, same sport family (Run→run, Ride/VirtualRide→bike,
WeightTraining/Workout→strength, Swim→swim). Writes status=done and minutes
actually moved to data/ledger.csv and data/week.json. Never touches rows already done.
"""
import csv, json, os, sys, time, datetime as dt, requests
from weather import dump_week

SPORT_MAP = {"Run": "run", "TrailRun": "run", "VirtualRun": "run", "Ride": "bike", "VirtualRide": "bike",
             "WeightTraining": "strength", "Workout": "strength", "Swim": "swim"}

def token():
    r = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": os.environ["STRAVA_CLIENT_ID"], "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "grant_type": "refresh_token", "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"]}, timeout=20)
    r.raise_for_status()
    j = r.json()
    if j.get("refresh_token") and j["refresh_token"] != os.environ["STRAVA_REFRESH_TOKEN"]:
        # Strava can rotate refresh tokens; the repo secret must be updated or next week's sync fails.
        print(f"::warning::Strava issued a new refresh token. Update the STRAVA_REFRESH_TOKEN secret to: {j['refresh_token']}")
    return j["access_token"]

def activities(tok, days=7):
    after = int(time.time()) - days * 86400
    r = requests.get("https://www.strava.com/api/v3/athlete/activities",
                     headers={"Authorization": f"Bearer {tok}"}, params={"after": after, "per_page": 50}, timeout=20)
    r.raise_for_status()
    out = []
    for a in r.json():
        out.append({"date": a["start_date_local"][:10], "sport": SPORT_MAP.get(a.get("sport_type") or a.get("type")),
                    "minutes": round(a["moving_time"] / 60), "name": a["name"]})
    return [a for a in out if a["sport"]]

def main():
    if not all(os.environ.get(k) for k in ("STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN")):
        print("::warning::Strava secrets not set; skipping sync."); return
    acts = activities(token())
    rows = list(csv.DictReader(open("data/ledger.csv")))
    week = json.load(open("data/week.json"))
    hit = 0
    for a in acts:
        for r in rows:
            if r["date"] == a["date"] and r["sport"] == a["sport"] and r["status"] in ("planned", "modified"):
                r["status"] = "done"; r["minutes"] = str(a["minutes"]); r["note"] = (r["note"] + f' Strava: {a["name"]}').strip()
                hit += 1; break
        for s in week["days"]:
            if s["date"] == a["date"] and s["sport"] == a["sport"] and s["status"] in ("planned", "modified"):
                s["status"] = "done"; break
    with open("data/ledger.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n"); w.writeheader(); w.writerows(rows)
    dump_week(week)
    print(f"{len(acts)} activities, {hit} ledger rows marked done")

if __name__ == "__main__":
    main()
