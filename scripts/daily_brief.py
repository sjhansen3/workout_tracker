"""Compose today's one-line brief from data/week.json and push it via ntfy.

Env: NTFY_TOPIC (required), SITE_URL (optional, link on the notification),
CHAT_URL (optional, "Ask coach" button; defaults to Claude Code on the web).
Run weather.py --apply before this so venues are current.
"""
import json, os, time, datetime as dt, requests

APP_NAME = {"runna": "Runna", "trainerroad": "TrainerRoad", "fitbod": "Fitbod"}
TAGS = {"run": "running", "bike": "bike", "strength": "muscle", "swim": "swimmer", "rest": "sleeping"}

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
        app = APP_NAME.get(s["app"], s["app"])
        title = s["title"].removeprefix(app).strip()  # "Fitbod full body" -> "full body"
        msg = f"{app}: {title[0].lower() + title[1:]}, {s['minutes']} min{venue}. {s['note']}".strip()
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        print(msg); return
    headers = {"Title": "Training", "Tags": TAGS.get(s["sport"], "calendar") if s else "calendar"}
    chat = os.environ.get("CHAT_URL") or "https://claude.ai/code"
    actions = [f"view, Ask coach, {chat}"]
    if os.environ.get("SITE_URL"):
        headers["Click"] = os.environ["SITE_URL"]
        actions.insert(0, f"view, Week, {os.environ['SITE_URL']}")
    headers["Actions"] = "; ".join(actions)
    for i in range(4):  # ntfy.sh rate-limits shared IPs (CI runners); back off and retry
        r = requests.post(f"https://ntfy.sh/{topic}", data=msg.encode(), headers=headers, timeout=20)
        if r.status_code != 429:
            break
        time.sleep(10 * 2 ** i)
    r.raise_for_status()
    print("sent:", msg)

if __name__ == "__main__":
    main()
