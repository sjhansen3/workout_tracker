"""Compose today's one-line brief from data/week.json and push it via ntfy.

Env: NTFY_TOPIC (required), SITE_URL (optional, link on the notification).
Run weather.py --apply before this so venues are current.
"""
import json, os, datetime as dt, requests

def main():
    week = json.load(open("data/week.json"))
    today = dt.date.today().isoformat()
    s = next((x for x in week["days"] if x["date"] == today), None)
    if not s:
        msg = "No session in week.json for today. Time for a Sunday review?"
    elif s["sport"] == "rest":
        msg = f"Today: {s['title']}."
    else:
        venue = "" if s["sport"] == "strength" else f", {s['venue']}"
        msg = f"Today: {s['title']}, {s['minutes']} min{venue}. {s['note']}".strip()
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        print(msg); return
    headers = {"Title": "Training", "Tags": "running"}
    if os.environ.get("SITE_URL"):
        headers["Click"] = os.environ["SITE_URL"]
    requests.post(f"https://ntfy.sh/{topic}", data=msg.encode(), headers=headers, timeout=20).raise_for_status()
    print("sent:", msg)

if __name__ == "__main__":
    main()
